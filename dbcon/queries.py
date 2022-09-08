import pandas as pd
from dbcon.connections import get_db_connection
from config import get_logger

logger = get_logger(__name__)


def get_dash_users():
    sel_query = """SELECT *
                    FROM dash.users
                    ;"""
    df = pd.read_sql(sel_query, DBCON.engine)
    users_dict = df.set_index("username").to_dict(orient="index")
    return users_dict


def query_all(table_name: str, groupby: str | list[str] = None, limit: int = 1000):
    logger.info(f"Query: {table_name} {groupby=}")
    groupby_str = ""
    select_str = "*"
    if groupby:
        if isinstance(groupby, list):
            groupby = ",".join(groupby)
        groupby_str = f"GROUP BY {groupby}"
        select_str = groupby + ", count(*)"
    sel_query = f"""SELECT {select_str}
                    FROM {table_name}
                    {groupby_str}
                    LIMIT {limit}
                    ;
                    """
    df = pd.read_sql(sel_query, DBCON.engine)
    return df


def query_update_histogram(table_name: str, start_date="2021-01-01") -> pd.DataFrame:
    logger.info(f"Query times for histogram: {table_name=}")
    sel_query = f"""WITH md AS (
                    SELECT
                        generate_series('{start_date}', 
                            CURRENT_DATE, '1 day'::INTERVAL)::date AS date),
                    ud AS (
                    SELECT
                        updated_at::date AS updated_date,
                        count(1) AS updated_count
                    FROM
                        {table_name}
                    WHERE
                        updated_at >= '{start_date}'
                    GROUP BY
                        updated_at::date),
                    cd AS (
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
                        md.date AS date,
                        ud.updated_count,
                        cd.created_count
                    FROM
                        md
                    LEFT JOIN ud ON
                        md.date = ud.updated_date
                    LEFT JOIN cd ON
                        md.date = cd.created_date
                    ORDER BY
                        md.date DESC
                    ;
                """
    df = pd.read_sql(sel_query, con=DBCON.engine)
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


def query_overview(limit: int = 1000):
    logger.info("Query overview_table")
    sel_query = f"""SELECT * FROM
                    overview_table
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


def get_updated_ats(schema_name: str):
    df = SCHEMA_OVERVIEW[SCHEMA_OVERVIEW.column_name.str.endswith("_at")]
    tables = df.table_name.unique().tolist()
    dfs = []
    for table in tables:
        time_columns = df[df["table_name"] == table].column_name.unique().tolist()
        cols = [
            f"min({col}) as min_{col}, max({col}) as max_{col}" for col in time_columns
        ]
        cols_str = ", ".join(cols)
        sel_query = f"""SELECT '{table}' as table_name, {cols_str}
            FROM {schema_name}.{table}
            ;"""
        temp = pd.read_sql(sel_query, DBCON.engine)
        dfs.append(temp)
    df = pd.concat(dfs)
    return df


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


DBCON = get_db_connection("madrone")
DBCON.set_engine()
SCHEMA_OVERVIEW = get_schema_overview("public")
