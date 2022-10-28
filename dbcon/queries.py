import pandas as pd
from dbcon.connections import get_db_connection
from config import get_logger

logger = get_logger(__name__)


def get_dash_users() -> dict:
    sel_query = """SELECT *
                    FROM dash.users
                    ;"""
    df = pd.read_sql(sel_query, DBCON.engine)
    users_dict = df.set_index("username").to_dict(orient="index")
    return users_dict


def get_app_categories() -> list[str]:
    sel_query = """SELECT DISTINCT category
                    FROM networks_with_app_metrics
                    ;
                    """
    df = pd.read_sql(sel_query, DBCON.engine)
    category_list = df["category"].tolist()
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


def query_network_uniqueness(limit=100):
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


def get_app_txt_view(developer_url: str, direct_only=True) -> pd.DataFrame:
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


def query_store_apps_overview(start_date: str):
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


def query_updated_timestamps(
    table_name: str, start_date: str = "2021-01-01"
) -> pd.DataFrame:
    logger.info(f"Query updated times: {table_name=}")
    if table_name == "store_apps":
        audit_select = " audit_dates.updated_count, "
        audit_join = """LEFT JOIN audit_dates ON
                        my_dates.date = audit_dates.updated_date
                        """
    else:
        audit_join, audit_select = "", ""
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
                        created_at::date AS created_date,
                        count(1) AS created_count
                    FROM
                        {table_name}
                    WHERE
                        created_at >= '{start_date}'
                    GROUP BY
                        created_at::date)
                    SELECT
                        my_dates.date AS date,
                        updated_dates.last_updated_count,
                        {audit_select}
                        created_dates.created_count
                    FROM
                        my_dates
                    LEFT JOIN updated_dates ON
                        my_dates.date = updated_dates.last_updated_date
                    {audit_join}
                    LEFT JOIN created_dates ON
                        my_dates.date = created_dates.created_date
                    ORDER BY
                        my_dates.date DESC
                    ;
                """
    df = pd.read_sql(sel_query, con=DBCON.engine)
    df = df.fillna(0)
    return df


def query_search_developers(search_input: str, limit: int = 1000):
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


def get_all_tables_in_schema(schema_name: str):
    logger.info("Get checks tables")
    sel_schema = f"""SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = '{schema_name}'
    ;"""
    tables = pd.read_sql(sel_schema, DBCON.engine)
    tables = tables["table_name"].values.tolist()
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


try:
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
    APP_CATEGORIES = ["cat1", "cat2"]
    TABLES_WITH_TIMES = ["overview", "store_apps"]
