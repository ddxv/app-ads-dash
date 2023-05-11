import datetime
import json

import dash
import pandas as pd
from flask_caching import Cache

from config import DATE_FORMAT, get_logger
from dbcon.queries import (
    get_app_txt_view,
    query_network_uniqueness,
    query_networks_count,
    query_networks_with_app_metrics,
    query_pub_domains_overview,
    query_search_developers,
    query_store_apps_overview,
    query_updated_timestamps,
)
from ids import (
    DEVELOPERS_SEARCH,
    INTERNAL_LOGS,
    NETWORK_UNIQUES,
    NETWORKS,
    PUB_URLS_HISTORY,
    STORE_APPS_HISTORY,
    TXT_VIEW,
)

logger = get_logger(__name__)

logger.info("utils initialize cache")

CACHE_CONFIG = {
    "CACHE_TYPE": "filesystem",
    "CACHE_DIR": "/tmp/appdash/",
    # higher numbers will store more data in the filesystem
    "CACHE_THRESHOLD": 50,
}


def create_new_cache():
    try:
        app = dash.get_app()
        server = app.server
    except Exception:
        # Ok if importing via repl
        logger.warning("Dash app not set first, not caching across dash server")
        from flask import Flask

        server = Flask(__name__)
    cache = Cache(
        app=server,
        config=CACHE_CONFIG,
    )
    with server.app_context():
        cache.clear()
    return cache


CACHE = create_new_cache()


@CACHE.memoize()
def get_cached_dataframe(query_json):
    query_dict = json.loads(query_json)
    if query_dict["id"] == "networks-with-app-metrics":
        df = query_networks_with_app_metrics()
    elif query_dict["id"] == STORE_APPS_HISTORY:
        df = query_store_apps_overview(start_date=query_dict["start_date"])
    elif query_dict["id"] == PUB_URLS_HISTORY:
        df = query_pub_domains_overview(start_date=query_dict["start_date"])
    elif query_dict["id"] == INTERNAL_LOGS:
        table_name = query_dict["table_name"]
        df = query_updated_timestamps(
            table_name=table_name, start_date=query_dict["start_date"]
        )
    elif query_dict["id"] == TXT_VIEW:
        df = get_app_txt_view(query_dict["developer_url"])
    elif query_dict["id"] == NETWORK_UNIQUES:
        df = query_network_uniqueness()
    elif query_dict["id"] == NETWORKS:
        df = query_networks_count(top_only=query_dict["top_only"])
    elif query_dict["id"] == DEVELOPERS_SEARCH:
        df = query_search_developers(
            search_input=query_dict["search_input"], limit=1000
        )
    else:
        logger.error(f"query_dict id: {query_dict['id']} not recognized")
    return df


def limit_rows_for_plotting(
    df: pd.DataFrame,
    row_ids: list[str] | None,
    sort_by_columns: list[str] | None = None,
    sort_ascending: bool = False,
) -> pd.DataFrame:
    original_shape = df.shape
    if row_ids and len(row_ids) > 0:
        row_ids = pd.DataFrame.from_records(row_ids[:MAX_ROWS])["id"].tolist()
        logger.info(f"Limit plot ids: {row_ids=}")
        df = df[df["id"].isin(row_ids)]
    if not row_ids:
        if sort_by_columns and len(sort_by_columns) > 0:
            sort_column = sort_by_columns[0]
        else:
            logger.warning("Limit plot ids: No row_ids! manual select")
            sort_column = "count"
        idf = df.groupby("id")[sort_column].sum().reset_index()
        idf = (
            idf.sort_values(sort_column, ascending=sort_ascending)
            .reset_index(drop=True)
            .head(MAX_ROWS)
        )
        row_ids = idf["id"].unique().tolist()
        df = df[df["id"].isin(row_ids)]
    logger.info(f"Limit plot ids: {original_shape=} new_shape: {df.shape}")
    return df


def add_id_column(df: pd.DataFrame, dimensions: list[str]) -> pd.DataFrame:
    df["id"] = df[dimensions].apply(
        lambda row: " ".join(row.values.astype(str)), axis=1
    )
    return df


def get_earlier_date(days: int = 30) -> str:
    my_date = datetime.datetime.strftime(
        datetime.datetime.now() - datetime.timedelta(days=days),
        DATE_FORMAT,
    )
    return my_date


def titlelize(original: str | list | None) -> str:
    if isinstance(original, list):
        title = ", ".join([x.replace("_", " ").title() for x in set(original)])
    elif isinstance(original, str):
        title = original.replace("_", " ").title()
    else:
        title = ""
    return title


MAX_ROWS = 10
