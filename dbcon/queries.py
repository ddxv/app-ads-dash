import pandas as pd


def get_dash_users(database_connection):
    sel_query = """SELECT *
                    FROM dash_users
                    ;"""
    df = pd.read_sql(sel_query, database_connection.engine)
    return df


def query_latest_updates(start_date, end_date, database_connection):
    sel_query = """SELECT * FROM
                        """
    df = pd.read_sql(sel_query, database_connection.engine)
    return df
