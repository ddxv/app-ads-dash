import pandas as pd


def get_dash_users(database_connection):
    sel_query = """SELECT *
                    FROM dash_users
                    ;"""
    df = pd.read_sql(sel_query, database_connection.engine)
    return df