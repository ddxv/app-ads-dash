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


def query_overview(limit: int = 1000):
    logger.info("Query overview_table")
    sel_query = f"""SELECT * FROM
                    overview_table
                    LIMIT {limit}
                    ;
                    """
    df = pd.read_sql(sel_query, DBCON.engine)
    return df


DBCON = get_db_connection("madrone")
DBCON.set_engine()
