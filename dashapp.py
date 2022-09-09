from app import app
from dash.dependencies import Input, Output, State
import dash
from dash.exceptions import PreventUpdate
import pandas as pd
import json
from ids import (
    AFFIX_GROUPBY,
    AFFIX_TABLE,
    DEVELOPERS,
    DEVELOPERS_SEARCH,
    LATEST_UPDATES,
    AFFIX_PLOT,
    UPDATED_AT,
    UPDATED_HISTOGRAM,
    DATE_PICKER_RANGE,
)
from layout.layout import APP_LAYOUT, TAB_LAYOUT_DICT
from layout.tab_template import make_columns, get_cards_group, get_left_buttons_layout
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
    if query_dict["id"] == LATEST_UPDATES:
        df = query_overview(limit=1000)
    elif query_dict["id"] == DEVELOPERS:
        df = query_all(table_name=query_dict["table_name"], limit=1000)
    elif query_dict["id"] == UPDATED_HISTOGRAM:
        df = query_update_histogram(
            table_name=query_dict["table_name"], start_date=query_dict["start_date"]
        )
        df["table_name"] = query_dict["table_name"]
    elif query_dict["id"] == UPDATED_AT:
        df = get_updated_ats("public")
    elif query_dict["id"] == DEVELOPERS_SEARCH:
        df = query_search_developers(
            search_input=query_dict["search_input"], limit=1000
        )
    else:
        logger.error(f"query_dict id: {query_dict['id']} not recognized")
    return df


def limit_rows_for_plotting(
    df: pd.DataFrame, row_ids: list[str], metrics: list[str] = None
) -> pd.DataFrame:
    logger.info("Limit Rows for Plotting")
    original_shape = df.shape
    if row_ids:
        logger.info(f"Rows selected: {row_ids=}")
        df = df[df["id"].isin(row_ids)]
    if not row_ids:
        logger.warning("NO row_ids or derived_row_ids! attempting to manually select")
        if metrics and len(metrics) > 0:
            sort_column = metrics[0]
        else:
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
    Output(UPDATED_HISTOGRAM + AFFIX_TABLE, "data"),
    Output(UPDATED_HISTOGRAM + AFFIX_TABLE, "columns"),
    Output(UPDATED_HISTOGRAM + "-buttongroup", "children"),
    Output(UPDATED_HISTOGRAM + "-memory-output", "data"),
    Input({"type": "left-menu", "index": dash.ALL}, "n_clicks"),
)
def histograms(
    n_clicks,
):
    logger.info(f"Updated histogram {dash.ctx.triggered_id=}")
    table_name = "store_apps"
    if (
        dash.ctx.triggered_id
        and dash.ctx.triggered_id != UPDATED_HISTOGRAM + AFFIX_TABLE
    ):
        table_name = dash.ctx.triggered_id["index"]
    metrics = ["updated_count", "created_count"]
    query_dict = {"id": UPDATED_HISTOGRAM, "table_name": table_name}
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    dimensions = [x for x in df.columns if x not in metrics and x != "id"]
    df = add_id_column(df, dimensions=dimensions)
    column_dicts = make_columns(dimensions, metrics)
    buttons = get_left_buttons_layout("updated-histogram", active_x=table_name)
    logger.info(f"Updated histogram: {table_name=} {df.shape=}")
    table_obj = df.to_dict("records")
    return table_obj, column_dicts, buttons, table_name


@app.callback(
    Output(UPDATED_HISTOGRAM + AFFIX_PLOT, "figure"),
    Input(DATE_PICKER_RANGE, "start_date"),
    Input(UPDATED_HISTOGRAM + "-memory-output", "data"),
    Input(UPDATED_HISTOGRAM + AFFIX_TABLE, "derived_viewport_row_ids"),
)
def histograms_plot(
    start_date,
    table_name,
    derived_viewport_row_ids,
):
    logger.info(f"Updated histogram plot {table_name=}")
    metrics = ["updated_count", "created_count"]
    if not table_name:
        PreventUpdate
    query_dict = {
        "id": UPDATED_HISTOGRAM,
        "table_name": table_name,
        "start_date": start_date,
    }
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    dimensions = [x for x in df.columns if x not in metrics and x != "date"]
    df = add_id_column(df, dimensions=dimensions)
    logger.info(f"Updated histogram plot_df: {df.shape=}")
    df = limit_rows_for_plotting(df, derived_viewport_row_ids, metrics=metrics)
    fig = overview_plot(
        df=df,
        xaxis_col="date",
        y_vals=metrics,
        title="Updated Histogram",
        stack_bars=True,
        bar_column=metrics[0],
    )
    fig.show()
    return fig


@app.callback(
    Output(DEVELOPERS_SEARCH + AFFIX_TABLE, "data"),
    Output(DEVELOPERS_SEARCH + AFFIX_TABLE, "columns"),
    Input(DEVELOPERS_SEARCH + "-button", "n_clicks"),
    State(DEVELOPERS_SEARCH + "-input", "value"),
    Input(DEVELOPERS_SEARCH + AFFIX_TABLE, "derived_viewport_row_ids"),
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
        "id": DEVELOPERS_SEARCH,
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
    Output(DEVELOPERS + AFFIX_TABLE, "data"),
    Output(DEVELOPERS + AFFIX_TABLE, "columns"),
    Output(DEVELOPERS + AFFIX_PLOT, "figure"),
    Input(DEVELOPERS + AFFIX_GROUPBY, "value"),
    Input(DEVELOPERS + AFFIX_TABLE, "derived_viewport_row_ids"),
)
def developers(
    groupby,
    derived_viewport_row_ids: list[str],
):
    logger.info("Developers")
    metrics = ["size"]
    query_dict = {"id": DEVELOPERS, "table_name": "developers", "groupby": groupby}
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
    Output(UPDATED_AT + AFFIX_TABLE, "data"),
    Output(UPDATED_AT + AFFIX_TABLE, "columns"),
    Input(UPDATED_AT + AFFIX_TABLE, "derived_viewport_row_ids"),
)
def updated_at_table(
    derived_viewport_row_ids: list[str],
):
    logger.info("Updates At Table")
    metrics = ["size"]
    query_dict = {"id": UPDATED_AT}
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    dimensions = [x for x in df.columns if x not in metrics and x != "id"]
    column_dicts = make_columns(dimensions, metrics)
    table_obj = df.to_dict("records")
    return table_obj, column_dicts


@app.callback(
    Output(LATEST_UPDATES + AFFIX_TABLE, "data"),
    Output(LATEST_UPDATES + AFFIX_TABLE, "columns"),
    Output(LATEST_UPDATES + AFFIX_PLOT, "figure"),
    Output("cards-group", "children"),
    Input(LATEST_UPDATES + AFFIX_GROUPBY, "value"),
    Input(LATEST_UPDATES + AFFIX_TABLE, "derived_viewport_row_ids"),
)
def latest_updates_table(
    groupby,
    derived_viewport_row_ids: list[str],
):
    logger.info("Latest Updates Table")
    metrics = ["size"]
    query_dict = {"id": LATEST_UPDATES}
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
        cards_group[f"{card_name}-body"] = dash.html.P(
            [
                f'Latest:  {df[column_name].max().strftime("%Y-%m-%d %H:%M:%S")}',
                dash.html.Br(),
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
