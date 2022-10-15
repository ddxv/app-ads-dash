import json
import pandas as pd
from flask_caching import Cache
from config import get_logger
from ids import INTERNAL_LOGS, TXT_VIEW, NETWORKS, DEVELOPERS_SEARCH, STORE_APPS_HISTORY
from dbcon.queries import (
    get_app_txt_view,
    query_search_developers,
    query_store_apps_overview,
    query_updated_timestamps,
    query_networks_count,
)
import dash


logger = get_logger(__name__)

app = dash.get_app()


CACHE = Cache(
    app.server,
    config={
        "CACHE_TYPE": "filesystem",
        "CACHE_DIR": "/tmp/appdash/",
        # higher numbers will store more data in the filesystem
        "CACHE_THRESHOLD": 50,
    },
)
CACHE.clear()


@CACHE.memoize()
def get_cached_dataframe(query_json):
    query_dict = json.loads(query_json)
    if query_dict["id"] == STORE_APPS_HISTORY:
        df = query_store_apps_overview(start_date=query_dict["start_date"])
    if query_dict["id"] == INTERNAL_LOGS:
        table_name = query_dict["table_name"]
        df = query_updated_timestamps(
            table_name=table_name, start_date=query_dict["start_date"]
        )
    elif query_dict["id"] == TXT_VIEW:
        df = get_app_txt_view(query_dict["developer_url"])
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
    df: pd.DataFrame, row_ids: list[str] | None, metrics: list[str] = None
) -> pd.DataFrame:
    original_shape = df.shape
    if row_ids:
        logger.info(f"Limit plot ids: {row_ids=}")
        df = df[df["id"].isin(row_ids)]
    if not row_ids:
        if metrics and len(metrics) > 0:
            sort_column = metrics[0]
        else:
            logger.warning("Limit plot ids: No row_ids! Attempt manual select")
            sort_column = "count"
        idf = df.groupby("id")[sort_column].sum().reset_index()
        idf = (
            idf.sort_values(sort_column, ascending=False)
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


MAX_ROWS = 10
