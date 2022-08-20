import pandas as pd
from dbcon.connections import get_db_connection


def get_dash_users():
    sel_query = """SELECT *
                    FROM dash_users
                    ;"""
    df = pd.read_sql(sel_query, DBCON.engine)
    return df


def query_overview(limit: int = 1000):
    sel_query = f"""SELECT * FROM
                    overview_table
                    LIMIT {limit}
                    ;
                    """
    df = pd.read_sql(sel_query, DBCON.engine)
    return df


DBCON = get_db_connection("madrone")
DBCON.set_engine()

df = query_overview(limit=1)
