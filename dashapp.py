from app import app
from dash.dependencies import Input, Output
from dash import html
import pandas as pd
import json
from layout.layout import APP_LAYOUT
from layout.tab_template import make_columns, TAB_LAYOUT_DICT, get_cards_group
from plotter.plotter import overview_plot
from dbcon.queries import (
    query_overview,
)
from flask_caching import Cache

from config import get_logger

logger = get_logger(__name__)


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
    if query_dict["id"] == "latest-updates":
        df = query_overview()
    else:
        logger.error(f"query_dict id: {query_dict['id']} not recognized")
    return df


def limit_rows_for_plotting(df: pd.DataFrame, row_ids: list[str]) -> pd.DataFrame:
    logger.info("Limit Rows for Plotting")
    original_shape = df.shape
    if row_ids:
        logger.info(f"Rows selected: {row_ids=}")
        df = df[df["id"].isin(row_ids)]
    if not row_ids:
        logger.warning("NO row_ids or derived_row_ids! attempting to manually select")
        sort_column = "count"
        idf = df.groupby("id")[sort_column].sum().reset_index()
        idf = (
            idf.sort_values(sort_column, ascending=False)
            .reset_index(drop=True)
            .head(MAX_ROWS)
        )
        row_ids = idf["id"].unique().tolist()
        df = df[df["id"].isin(row_ids)]
    logger.info(f"limit_rows_for_plotting: {original_shape=} new_shape: {df.shape}")
    return df


@app.callback(
    Output("tabs-content", "children"),
    Input("tabs-selector", "active_tab"),
)
def render_content(tab):
    logger.info(f"Loading tab: {tab}")
    return TAB_LAYOUT_DICT[tab]


@app.callback(
    Output("latest-updates-df-table-overview", "data"),
    Output("latest-updates-df-table-overview", "columns"),
    Output("latest-updates-overview-plot", "figure"),
    Output("cards-group", "children"),
    Input("date-picker-range", "start_date"),
    Input("date-picker-range", "end_date"),
    Input("latest-updates-groupby", "value"),
    Input("latest-updates-switches", "value"),
    Input("latest-updates-df-table-overview", "derived_viewport_row_ids"),
)
def latest_updates_table(
    start_date,
    end_date,
    groupby,
    switches,
    derived_viewport_row_ids: list[str],
):
    logger.info("Latest Updates Table")
    metrics = ["size"]
    query_dict = {"id": "latest-updates"}
    df = get_cached_dataframe(query_json=json.dumps(query_dict))

    dimensions = [x for x in groupby if x not in metrics and x != "id"]
    column_dicts = make_columns(dimensions, metrics)
    dff = (
        df.groupby(dimensions, dropna=False)
        .size()
        .reset_index()
        .rename(columns={0: "size"})
    )
    table_obj = dff.to_dict("records")
    plot_df = (
        df.groupby(dimensions, dropna=False)
        .size()
        .reset_index()
        .rename(columns={0: "size"})
    )
    plot_df = add_id_column(plot_df, dimensions=dimensions)
    fig = overview_plot(
        plot_df,
        y_vals=["size"],
        xaxis_col=groupby[0],
        title="Updates",
    )

    cards_group = get_cards_group()
    card_ids = [
        "txt-updated-at",
        "ad-domain-updated-at",
        "store-app-updated-at",
        "pub-domain-updated-at",
    ]
    for card_name in card_ids:
        column_name = card_name.replace("-", "_")
        cards_group[f"{card_name}-body"] = html.H5(
            df[column_name].max().strftime("%Y-%m-%d %H:%M:%S")
        )

    return table_obj, column_dicts, fig, cards_group.children


def add_id_column(df: pd.DataFrame, dimensions: list[str]) -> pd.DataFrame:
    df["id"] = df[dimensions].apply(
        lambda row: " ".join(row.values.astype(str)), axis=1
    )
    return df


MAX_ROWS = 10


logger.info("Set Layout")
app.layout = APP_LAYOUT

if __name__ == "__main__":
    app.run_server(debug=True)
