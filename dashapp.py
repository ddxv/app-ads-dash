from app import app
from dash.dependencies import Input, Output, State
from dash import html
from dash.exceptions import PreventUpdate
import pandas as pd
import json
from layout.layout import APP_LAYOUT, TAB_LAYOUT_DICT
from layout.tab_template import make_columns, get_cards_group
from plotter.plotter import overview_plot
from dbcon.queries import (
    query_overview,
    query_all,
    get_updated_ats,
    query_search_developers,
    query_update_histogram,
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
        df = query_overview(limit=1000)
    elif query_dict["id"] == "developers":
        df = query_all(table_name=query_dict["table_name"], limit=1000)
    elif query_dict["id"] == "updated-histogram":
        df = query_update_histogram("store_apps")
    elif query_dict["id"] == "updated-at":
        df = get_updated_ats("public")
    elif query_dict["id"] == "developers-search":
        df = query_search_developers(
            search_input=query_dict["search_input"], limit=1000
        )
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
    Output("updated-histogram-df-table-overview", "data"),
    Output("updated-histogram-df-table-overview", "columns"),
    Input("updated-histogram-df-table-overview", "derived_viewport_row_ids"),
)
def histograms(
    derived_viewport_row_ids: list[str],
):
    logger.info("Developers Search {input_value=}")
    metrics = ["size"]
    query_dict = {
        "id": "updated-histogram",
    }
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    logger.info(f"Developers Search {df.shape=}")
    dimensions = [x for x in df.columns if x not in metrics and x != "id"]
    column_dicts = make_columns(dimensions, metrics)
    logger.info(f"Developers Search {df.shape=}")
    table_obj = df.to_dict("records")
    return table_obj, column_dicts


@app.callback(
    Output("developers-search-df-table-overview", "data"),
    Output("developers-search-df-table-overview", "columns"),
    Input("developers-search-button", "n_clicks"),
    State("developers-search-input", "value"),
    Input("developers-search-df-table-overview", "derived_viewport_row_ids"),
)
def developers_search(
    button,
    input_value,
    derived_viewport_row_ids: list[str],
):
    logger.info("Developers Search {input_value=}")
    metrics = ["size"]
    if not input_value:
        logger.info("Developers Search {input_value=} prevent update")
        PreventUpdate
    query_dict = {
        "id": "developers-search",
        "search_input": input_value,
    }
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    logger.info(f"Developers Search {df.shape=}")
    dimensions = [x for x in df.columns if x not in metrics and x != "id"]
    column_dicts = make_columns(dimensions, metrics)
    logger.info(f"Developers Search {df.shape=}")
    table_obj = df.to_dict("records")
    return table_obj, column_dicts


@app.callback(
    Output("developers-df-table-overview", "data"),
    Output("developers-df-table-overview", "columns"),
    Output("developers-overview-plot", "figure"),
    Input("developers-groupby", "value"),
    Input("developers-df-table-overview", "derived_viewport_row_ids"),
)
def developers(
    groupby,
    derived_viewport_row_ids: list[str],
):
    logger.info("Developers")
    metrics = ["size"]
    query_dict = {"id": "developers", "table_name": "developers", "groupby": groupby}
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    logger.info(f"Developers {df.shape=}")

    dimensions = [x for x in groupby if x not in metrics and x != "id"]
    column_dicts = make_columns(dimensions, metrics)
    dff = (
        df.groupby(dimensions, dropna=False)
        .size()
        .reset_index()
        .rename(columns={0: "size"})
    )
    logger.info(f"Developers {dff.shape=}")
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
        title="Developers",
    )

    return table_obj, column_dicts, fig


@app.callback(
    Output("updated-at-df-table-overview", "data"),
    Output("updated-at-df-table-overview", "columns"),
    Input("updated-at-df-table-overview", "derived_viewport_row_ids"),
)
def updated_at_table(
    derived_viewport_row_ids: list[str],
):
    logger.info("Updates At Table")
    metrics = ["size"]
    query_dict = {"id": "updated-at"}
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    dimensions = [x for x in df.columns if x not in metrics and x != "id"]
    column_dicts = make_columns(dimensions, metrics)
    table_obj = df.to_dict("records")
    return table_obj, column_dicts


@app.callback(
    Output("latest-updates-df-table-overview", "data"),
    Output("latest-updates-df-table-overview", "columns"),
    Output("latest-updates-overview-plot", "figure"),
    Output("cards-group", "children"),
    Input("latest-updates-groupby", "value"),
    Input("latest-updates-df-table-overview", "derived_viewport_row_ids"),
)
def latest_updates_table(
    groupby,
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
        cards_group[f"{card_name}-body"] = html.P(
            [
                f'Latest:  {df[column_name].max().strftime("%Y-%m-%d %H:%M:%S")}',
                html.Br(),
                f'Earliest: {df[column_name].min().strftime("%Y-%m-%d %H:%M:%S")}',
            ]
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
