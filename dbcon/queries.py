import pandas as pd

from config import get_logger
from dbcon.connections import get_db_connection

logger = get_logger(__name__)


def get_dash_users() -> dict:
    sel_query = """SELECT *
                    FROM dash.users
                    ;"""
    df = pd.read_sql(sel_query, DBCON.engine)
    users_dict: dict = df.set_index("username").to_dict(orient="index")
    return users_dict


def get_app_categories() -> list[str]:
    sel_query = """SELECT DISTINCT category
                    FROM networks_with_app_metrics
                    ;
                    """
    df = pd.read_sql(sel_query, DBCON.engine)
    category_list: list[str] = df["category"].tolist()
    category_list.sort()
    return category_list


def query_networks_with_app_metrics() -> pd.DataFrame:
    table_name = "networks_with_app_metrics"
    sel_query = f"""SELECT
                    *
                    FROM 
                    {table_name}
                    ;
                """
    df = pd.read_sql(sel_query, DBCON.engine)
    df = df.rename(
        columns={
            "publisher_urls": "publishers_count",
            "total_publisher_urls": "publishers_total",
        }
    )
    return df


def query_networks_count(top_only: bool = False) -> pd.DataFrame:
    if top_only:
        table_name = "network_counts_top"
    else:
        table_name = "network_counts"
    sel_query = f"""SELECT
                    *
                    FROM 
                    {table_name}
                    ;
                """
    df = pd.read_sql(sel_query, DBCON.engine)
    return df


def query_network_uniqueness(limit: int = 100) -> pd.DataFrame:
    sel_query = f"""
        SELECT
        ad_domain_url,
        count(DISTINCT publisher_id) AS publisher_count,
        sum(is_unique) AS unique_count
    FROM
        publisher_url_developer_ids_uniques
    GROUP BY
        ad_domain_url
    ORDER BY publisher_count DESC
    LIMIT {limit}
    ;
    """
    df = pd.read_sql(sel_query, DBCON.engine)
    df["percent"] = df["unique_count"] / df["publisher_count"]
    return df


def get_app_txt_view(developer_url: str, direct_only: bool = True) -> pd.DataFrame:
    if direct_only:
        direct_only_str = "AND av.relationship = 'DIRECT'"
    else:
        direct_only_str = ""
    sel_query = f"""WITH cte1 AS (
            SELECT
                av.developer_domain_url,
                av.ad_domain AS ad_domain_id,
                av.ad_domain_url,
                av.publisher_id
            FROM
                app_ads_view av
            WHERE
                av.developer_domain_url LIKE '{developer_url}'
                {direct_only_str}
                )
            SELECT
                c1.developer_domain_url AS my_domain_url,
                av2.developer_domain_url AS their_domain_url,
                CASE
                  WHEN av2.developer_domain_url != c1.developer_domain_url
                    THEN 'FAIL'
                    ELSE 'PASS'
                  END AS is_my_id,
                av2.publisher_id,
                av2.ad_domain_url,
                av2.ad_domain AS ad_domain_id,
                av2.relationship AS relationship,
                av2.txt_entry_crawled_at
            FROM
                cte1 c1
            LEFT JOIN app_ads_view av2 ON
                av2.ad_domain_url = c1.ad_domain_url
                AND av2.publisher_id = c1.publisher_id
                    ;
                """
    df = pd.read_sql(sel_query, DBCON.engine)
    return df


def query_store_apps_overview(start_date: str) -> pd.DataFrame:
    logger.info("Query logging.store_apps_snapshot")
    sel_query = f"""SELECT
                        sas.*,
                        s.name AS store_name,
                        coalesce(cr.outcome, 'not_crawled') AS outcome
                    FROM
                    logging.store_apps_snapshot sas
                    LEFT JOIN crawl_results cr
                        ON cr.id = sas.crawl_result
                    LEFT JOIN stores s
                        ON s.id = sas.store
                    where updated_at >= '{start_date}'
                    ;
                """
    df = pd.read_sql(sel_query, con=DBCON.engine)
    df = df.drop(["store", "crawl_result"], axis=1)
    return df


def query_pub_domains_overview(start_date: str) -> pd.DataFrame:
    logger.info("Query logging.pub_domains_snapshot")
    sel_query = f"""SELECT
                        ss.*,
                        coalesce(cr.outcome, 'not_crawled') AS outcome
                    FROM
                    logging.snapshot_pub_domains ss
                    LEFT JOIN crawl_results cr
                        ON cr.id = ss.crawl_result
                    where updated_at >= '{start_date}'
                    ;
                """
    df = pd.read_sql(sel_query, con=DBCON.engine)
    df = df.drop(["crawl_result"], axis=1)
    return df


def query_app_store_sources(start_date: str = "2021-01-01") -> pd.DataFrame:
    logger.info(f"Query app_store sources: table_name=app_store_sources {start_date=}")
    sel_query = f"""SELECT 
                        date,
                        store,
                        COALESCE(crawl_source, 'unknown') AS crawl_source,
                        created_count as app_count
                    FROM 
                        store_apps_created_at
                    WHERE
                        date >= '{start_date}'
                    ;
                    """
    df = pd.read_sql(sel_query, con=DBCON.engine)
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    return df


def query_developer_updated_timestamps(start_date: str = "2021-01-01") -> pd.DataFrame:
    logger.info(f"Query updated times: table_name=developers {start_date=}")
    sel_query = f"""WITH my_dates AS (
                    SELECT
                        store,
                        generate_series('{start_date}', 
                            CURRENT_DATE, '1 day'::INTERVAL)::date AS date
                    FROM generate_series(1, 2, 1) AS num_series(store)
                    ),
                    updated_dates AS (
                    SELECT
                        store,
                        dca.apps_crawled_at::date AS crawled_date,
                        count(1) AS devs_crawled_count
                    FROM
                        developers d
                    LEFT JOIN logging.developers_crawled_at dca
                        ON dca.developer = d.id
                    WHERE
                        dca.apps_crawled_at >= '{start_date}'
                    GROUP BY
                        store,
                        dca.apps_crawled_at::date
                    ),
                    created_dates AS (
                    SELECT
                        store,
                        created_at::date AS created_date,
                        count(1) AS created_count
                    FROM
                        developers
                    WHERE
                        created_at >= '{start_date}'
                    GROUP BY
                        store,
                        created_at::date
                        )
                    SELECT
                        my_dates.store AS store,
                        my_dates.date AS date,
                        updated_dates.devs_crawled_count,
                        created_dates.created_count
                    FROM
                        my_dates
                    LEFT JOIN updated_dates ON
                        my_dates.date = updated_dates.crawled_date 
                            AND my_dates.store = updated_dates.store
                    LEFT JOIN created_dates ON
                        my_dates.date = created_dates.created_date
                            AND my_dates.store = created_dates.store
                    ORDER BY
                        my_dates.date DESC
                    ;
                """
    df = pd.read_sql(sel_query, con=DBCON.engine)
    df = df.fillna(0)
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    return df


def query_app_updated_timestamps(start_date: str) -> pd.DataFrame:
    logger.info(f"Query store app updated ats: {start_date=}")
    sel_query = f"""WITH created_counts AS (
                    SELECT
                        cr.store,
                        cr.date,
                        sum(created_count) AS created_count
                    FROM
                        store_apps_created_at cr
                    WHERE
                        date >= '{start_date}'
                    GROUP BY
                        cr.store,
                        cr.date
                )
                SELECT
                    ua.store,
                    ua.date,
                    ua.last_updated_count,
                    ua.updated_count,
                        cr.created_count
                FROM
                    store_apps_updated_at ua
                LEFT JOIN created_counts cr ON
                    cr.date = ua.date
                    AND ua.store = cr.store
                WHERE
                    ua.date >= '{start_date}'
                ;
    """
    df = pd.read_sql(sel_query, con=DBCON.engine)
    df = df.fillna(0)
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    return df


def query_updated_version_code_timestamps(start_date: str) -> pd.DataFrame:
    sel_query = f"""WITH my_dates AS
                        (
                            SELECT
                                store,
                                crawl_result,
                                generate_series(
                                    '{start_date}',
                                    CURRENT_DATE,
                                    '1 day'::INTERVAL
                                )::date AS date
                            FROM
                                generate_series(
                                    1,
                                    2,
                                    1
                                ) AS num_series(store),
                                generate_series(
                                    1,
                                    4,
                                    1
                                ) AS num_seriess(crawl_result)
                        ),
                        updated_dates AS (
                            SELECT
                                vc.updated_at::date AS last_updated_date,
                                sa.store,
                                vc.crawl_result,
                                count(1) AS last_updated_count
                            FROM
                                version_codes vc
                            LEFT JOIN store_apps sa ON
                                vc.store_app = sa.id
                            WHERE
                                vc.updated_at >= '{start_date}'
                            GROUP BY
                                vc.updated_at::date,
                                sa.store,
                                vc.crawl_result
                        ),
                        min_version_per_app AS (
                            SELECT
                                sa.store,
                                store_app,
                                MIN(vc.version_code) AS min_version_code,
                                DATE(vc.updated_at) AS updated_date
                            FROM
                                version_codes vc
                            LEFT JOIN store_apps sa ON
                                vc.store_app = sa.id
                            WHERE
                                vc.crawl_result = 1
                            GROUP BY
                                store,
                                store_app,
                                DATE(vc.updated_at)
                        ),
                        created_dates AS (
                            SELECT
                                updated_date AS created_date,
                                store,
                                1 AS crawl_result,
                                COUNT(*) AS created_count
                            FROM
                                min_version_per_app
                            GROUP BY
                                updated_date,
                                store
                            ORDER BY
                                updated_date
                        )
                        SELECT
                            my_dates.date AS date,
                            my_dates.store,
                            my_dates.crawl_result,
                            updated_dates.last_updated_count,
                            created_dates.created_count
                        FROM
                            my_dates
                        LEFT JOIN updated_dates ON
                            my_dates.date = updated_dates.last_updated_date
                            AND my_dates.store = updated_dates.store
                            AND my_dates.crawl_result = updated_dates.crawl_result
                        LEFT JOIN created_dates ON
                            my_dates.date = created_dates.created_date
                            AND my_dates.store = created_dates.store
                            AND my_dates.crawl_result = created_dates.crawl_result
                        ORDER BY
                            my_dates.date DESC
                        ;
                """
    df = pd.read_sql(sel_query, con=DBCON.engine)
    df = df.fillna(0)
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    df["crawl_result"] = df["crawl_result"].replace(
        {1: "Success (1)", 2: "Fail (2)", 3: "Fail (3)", 4: "Fail (4)"}
    )
    return df


def query_updated_timestamps(
    table_name: str, start_date: str = "2021-01-01"
) -> pd.DataFrame:
    created_column = "created_at"
    if table_name == "version_codes":
        created_column = "updated_at"  # no created_at column
    logger.info(f"Query updated times: {table_name=}")
    sel_query = f"""WITH my_dates AS (
                    SELECT
                        generate_series('{start_date}', 
                            CURRENT_DATE, '1 day'::INTERVAL)::date AS date),
                    updated_dates AS (
                    SELECT
                        updated_at::date AS last_updated_date,
                        count(1) AS last_updated_count
                    FROM
                        {table_name}
                    WHERE
                        updated_at >= '{start_date}'
                    GROUP BY
                        updated_at::date),
                    created_dates AS (
                    SELECT
                        {created_column}::date AS created_date,
                        count(1) AS created_count
                    FROM
                        {table_name}
                    WHERE
                        {created_column} >= '{start_date}'
                    GROUP BY
                        {created_column}::date)
                    SELECT
                        my_dates.date AS date,
                        updated_dates.last_updated_count,
                        created_dates.created_count
                    FROM
                        my_dates
                    LEFT JOIN updated_dates ON
                        my_dates.date = updated_dates.last_updated_date
                    LEFT JOIN created_dates ON
                        my_dates.date = created_dates.created_date
                    ORDER BY
                        my_dates.date DESC
                    ;
                """
    print(sel_query)
    df = pd.read_sql(sel_query, con=DBCON.engine)
    df = df.fillna(0)
    return df


def query_search_developers(search_input: str, limit: int = 1000) -> pd.DataFrame:
    logger.info(f"Developer search: {search_input=}")
    search_input = f"%%{search_input}%%"
    sel_query = f"""SELECT
                        d.*,
                        pd.*,
                        sa.*
                    FROM
                        app_urls_map aum
                    LEFT JOIN pub_domains pd ON
                        pd.id = aum.pub_domain
                    LEFT JOIN store_apps sa ON
                        sa.id = aum.store_app
                    LEFT JOIN developers d ON
                        d.id = sa.developer
                    WHERE
                        d.name ILIKE '{search_input}'
                        OR d.developer_id ILIKE '{search_input}'
                        OR pd.url ILIKE '{search_input}'
                    LIMIT {limit}
                    ;
                    """
    df = pd.read_sql(sel_query, DBCON.engine)
    return df


def get_all_tables_in_schema(schema_name: str) -> list[str]:
    logger.info("Get checks tables")
    sel_schema = f"""SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = '{schema_name}'
    ;"""
    tables_df = pd.read_sql(sel_schema, DBCON.engine)
    tables: list[str] = tables_df["table_name"].to_numpy().tolist()
    return tables


def get_schema_overview(schema_name: str = "public") -> pd.DataFrame:
    sel_query = f"""SELECT
                        table_schema,
                        table_name,
                        column_name
                    FROM
                        information_schema.columns
                    WHERE
                        table_schema ='{schema_name}'
                    ORDER BY
                        table_schema,
                        table_name
                ;
                """
    df = pd.read_sql(sel_query, DBCON.engine)
    return df


def get_appstore_categories() -> pd.DataFrame:
    sel_query = """SELECT *
                    FROM mv_app_categories
                    ;
                    """
    df = pd.read_sql(sel_query, DBCON.engine)
    df["store"] = df["store"].replace({1: "android", 2: "ios"})
    df = pd.pivot_table(
        data=df, index="category", values="app_count", columns="store", fill_value=0
    ).reset_index()
    df["total_apps"] = df["android"] + df["ios"]
    df = df.sort_values("total_apps", ascending=False)

    return df


try:
    logger.info("set db engine")
    DBCON = get_db_connection("madrone")
    DBCON.set_engine()
    SCHEMA_OVERVIEW = get_schema_overview("public")
    TABLES = SCHEMA_OVERVIEW["table_name"].unique().tolist()
    APP_CATEGORIES = get_app_categories()
    TABLES_WITH_TIMES = (
        SCHEMA_OVERVIEW[
            SCHEMA_OVERVIEW["column_name"].isin(["updated_at", "created_at"])
        ]["table_name"]
        .unique()
        .tolist()
    )
except Exception:
    logger.exception("Database Connection failed!")
    APP_CATEGORIES = ["cat1", "cat2"]
    TABLES_WITH_TIMES = ["overview", "store_apps", "version_codes"]
