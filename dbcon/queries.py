import pandas as pd
from .connections import get_db_connection


def get_dash_users():
    sel_query = """SELECT *
                    FROM dash_users
                    ;"""
    df = pd.read_sql(sel_query, DBCON.engine)
    return df


def query_overview():
    sel_query = """SELECT * FROM
                    overview_table
                    LIMIT 1000
                    ;
                    """
    df = pd.read_sql(sel_query, DBCON.engine)
    return df


DBCON = get_db_connection("madrone")
DBCON.set_engine()
