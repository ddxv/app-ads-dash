import dash
from dash import callback, Input, Output
import pandas as pd
import json
from ids import (
    AFFIX_GROUPBY_TIME,
    AFFIX_SWITCHES,
    AFFIX_TABLE,
    AFFIX_PLOT,
    INTERNAL_LOGS,
    AFFIX_DATE_PICKER,
    STORE_APPS_HISTORY,
    PUB_URLS_HISTORY,
)
from layout.tab_template import (
    make_columns,
    get_left_buttons_layout,
    get_tab_layout_dict,
    make_main_content_list,
)
from plotter.plotter import overview_plot
from utils import (
    get_cached_dataframe,
    get_earlier_date,
    limit_rows_for_plotting,
    add_id_column,
)
from config import get_logger

logger = get_logger(__name__)


dash.register_page(__name__, name="Internal Audits")

PAGE_ID = "internal-audit"

TAB_OPTIONS = [
    {"label": "Crawler: Updated Counts", "tab_id": INTERNAL_LOGS},
    {"label": "Store Apps Historical", "tab_id": STORE_APPS_HISTORY},
    {"label": "Pub URLs Historical", "tab_id": PUB_URLS_HISTORY},
]

TABS_DICT = get_tab_layout_dict(page_id=PAGE_ID, tab_options=TAB_OPTIONS)


layout = make_main_content_list(page_id=PAGE_ID, tab_options=TAB_OPTIONS)


@callback(
    Output(PAGE_ID + "-tabs-content", "children"),
    Input(PAGE_ID + "-tabs-selector", "active_tab"),
)
def render_content(tab):
    logger.info(f"Loading tab: {tab}")
    return TABS_DICT[tab]


@callback(
    Output(INTERNAL_LOGS + AFFIX_TABLE, "data"),
    Output(INTERNAL_LOGS + AFFIX_TABLE, "columns"),
    Output(INTERNAL_LOGS + "-buttongroup", "children"),
    Output(INTERNAL_LOGS + "-memory-output", "data"),
    Input({"type": "left-menu", "index": dash.ALL}, "n_clicks"),
    Input(INTERNAL_LOGS + AFFIX_DATE_PICKER, "start_date"),
)
def internal_logs(n_clicks, start_date):
    logger.info(f"Internal logs: {dash.ctx.triggered_id=}")
    table_name = "store_apps"
    if dash.ctx.triggered_id and not isinstance(dash.ctx.triggered_id, str):
        table_name = dash.ctx.triggered_id["index"]
    metrics = ["updated_count", "created_count", "last_updated_count"]
    date_col = "date"
    query_dict = {
        "id": INTERNAL_LOGS,
        "table_name": table_name,
        "start_date": start_date,
    }
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    dimensions = [x for x in df.columns if x not in metrics and x != date_col]
    df = add_id_column(df, dimensions=dimensions)
    column_dicts = make_columns(dimensions, metrics)
    buttons = get_left_buttons_layout(INTERNAL_LOGS, active_x=table_name)
    logger.info(f"Internal Logs: {table_name=} {df.shape=}")
    table_obj = df.to_dict("records")
    return table_obj, column_dicts, buttons, table_name


@callback(
    Output(INTERNAL_LOGS + AFFIX_PLOT, "figure"),
    Input(INTERNAL_LOGS + AFFIX_DATE_PICKER, "start_date"),
    Input(INTERNAL_LOGS + "-memory-output", "data"),
    Input(INTERNAL_LOGS + AFFIX_TABLE, "derived_viewport_row_ids"),
)
def internal_logs_plot(
    start_date,
    table_name,
    derived_viewport_row_ids,
):
    logger.info(f"Internal logs plot {table_name=}")
    metrics = ["updated_count", "created_count", "last_updated_count"]
    date_col = "date"
    bar_column = "created_count"
    query_dict = {
        "id": INTERNAL_LOGS,
        "table_name": table_name,
        "start_date": start_date,
    }
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    dimensions = [x for x in df.columns if x not in metrics and x != date_col]
    df = add_id_column(df, dimensions=dimensions)
    logger.info(f"Internal logs plot_df: {df.shape=} {dimensions=}")
    df = limit_rows_for_plotting(df, derived_viewport_row_ids, sort_by_columns=metrics)
    fig = overview_plot(
        df=df,
        xaxis_col=date_col,
        y_vals=metrics,
        title="Updated Counts by Date",
        stack_bars=True,
        bar_column=bar_column,
    )
    return fig


@callback(
    Output(STORE_APPS_HISTORY + AFFIX_TABLE, "data"),
    Output(STORE_APPS_HISTORY + AFFIX_TABLE, "columns"),
    Input(STORE_APPS_HISTORY + AFFIX_DATE_PICKER, "start_date"),
    Input(STORE_APPS_HISTORY + AFFIX_SWITCHES, "value"),
)
def store_apps_history(start_date, switches):
    logger.info("Store apps historical data")
    metrics = ["total_rows", "avg_days", "max_days", "rows_older_than15"]
    date_col = "updated_at"
    query_dict = {
        "id": STORE_APPS_HISTORY,
        "start_date": start_date,
    }
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    dimensions = [x for x in df.columns if x not in metrics and x != date_col]
    if switches and len(switches) > 0:
        dimensions = [x for x in dimensions if x in switches]
        metrics = [x for x in metrics if x in switches]
        agg_default = {
            "total_rows": sum,
            "avg_days": "mean",
            "max_days": max,
            "rows_older_than15": sum,
        }
        metric_aggs = {k: v for k, v in agg_default.items() if k in metrics}
    # First agg across dimensions
    df = df.groupby([date_col] + dimensions)[metrics].agg(metric_aggs).reset_index()
    # Take last time for overview
    df = df.set_index(date_col).groupby(dimensions, dropna=False).last().reset_index()
    df = add_id_column(df, dimensions=dimensions)
    column_dicts = make_columns(dimensions, metrics)
    logger.info(f"Store apps history: {dimensions=} {df.shape=}")
    table_obj = df.to_dict("records")
    return table_obj, column_dicts


@callback(
    Output(STORE_APPS_HISTORY + AFFIX_PLOT, "figure"),
    Input(STORE_APPS_HISTORY + AFFIX_DATE_PICKER, "start_date"),
    Input(STORE_APPS_HISTORY + AFFIX_TABLE, "derived_viewport_row_ids"),
    Input(STORE_APPS_HISTORY + AFFIX_SWITCHES, "value"),
    Input(STORE_APPS_HISTORY + AFFIX_GROUPBY_TIME, "value"),
)
def store_apps_history_plot(
    start_date: str,
    derived_viewport_row_ids: list[str],
    switches: list[str],
    groupby_time,
):
    logger.info(f"Store apps history plot, {groupby_time=}")
    if "start_date" not in locals() or not start_date:
        start_date = get_earlier_date(days=30)
    metrics = ["total_rows", "avg_days", "max_days", "rows_older_than15"]
    date_col = "updated_at"
    bar_column = "total_rows"
    query_dict = {
        "id": STORE_APPS_HISTORY,
        "start_date": start_date,
    }
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    dimensions = [x for x in df.columns if x not in metrics and x != date_col]
    if switches and len(switches) > 0:
        dimensions = [x for x in dimensions if x in switches]
        metrics = [x for x in metrics if x in switches]
        agg_default = {
            "total_rows": sum,
            "avg_days": "mean",
            "max_days": max,
            "rows_older_than15": sum,
        }
        metric_aggs = {k: v for k, v in agg_default.items() if k in metrics}
    # First agg across dimensions
    df = df.groupby([date_col] + dimensions)[metrics].agg(metric_aggs).reset_index()
    # Limit Frequency for plotting to control number of points/columns
    df = (
        df.groupby(
            [pd.Grouper(key=date_col, freq=groupby_time)] + dimensions, dropna=False
        )
        .last()
        .reset_index()
    )
    df = add_id_column(df, dimensions=dimensions)
    logger.info(f"Store apps history plot: {dimensions=} {df.shape=}")
    df = limit_rows_for_plotting(df, derived_viewport_row_ids, sort_by_columns=metrics)

    fig = overview_plot(
        df=df,
        xaxis_col=date_col,
        y_vals=metrics,
        title="Updated Counts by Date",
        stack_bars=True,
        bar_column=bar_column,
    )
    return fig


@callback(
    Output(PUB_URLS_HISTORY + AFFIX_TABLE, "data"),
    Output(PUB_URLS_HISTORY + AFFIX_TABLE, "columns"),
    Input(PUB_URLS_HISTORY + AFFIX_DATE_PICKER, "start_date"),
    Input(PUB_URLS_HISTORY + AFFIX_SWITCHES, "value"),
)
def pub_domains_history(start_date, switches):
    logger.info("Store pub domains history data")
    metrics = ["total_rows", "avg_days", "max_days", "rows_older_than15"]
    date_col = "updated_at"
    query_dict = {
        "id": PUB_URLS_HISTORY,
        "start_date": start_date,
    }
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    dimensions = [x for x in df.columns if x not in metrics and x != date_col]
    if switches and len(switches) > 0:
        dimensions = [x for x in dimensions if x in switches]
        metrics = [x for x in metrics if x in switches]
        agg_default = {
            "total_rows": sum,
            "avg_days": "mean",
            "max_days": max,
            "rows_older_than15": sum,
        }
        metric_aggs = {k: v for k, v in agg_default.items() if k in metrics}
    # First agg across dimensions
    df = df.groupby([date_col] + dimensions)[metrics].agg(metric_aggs).reset_index()
    # Take last time for overview
    df = df.set_index(date_col).groupby(dimensions, dropna=False).last().reset_index()
    df = add_id_column(df, dimensions=dimensions)
    column_dicts = make_columns(dimensions, metrics)
    logger.info(f"Store apps history: {dimensions=} {df.shape=}")
    table_obj = df.to_dict("records")
    return table_obj, column_dicts


@callback(
    Output(PUB_URLS_HISTORY + AFFIX_PLOT, "figure"),
    Input(PUB_URLS_HISTORY + AFFIX_DATE_PICKER, "start_date"),
    Input(PUB_URLS_HISTORY + AFFIX_TABLE, "derived_viewport_row_ids"),
    Input(PUB_URLS_HISTORY + AFFIX_SWITCHES, "value"),
    Input(PUB_URLS_HISTORY + AFFIX_GROUPBY_TIME, "value"),
)
def pub_domains_history_plot(
    start_date: str,
    derived_viewport_row_ids: list[str],
    switches: list[str],
    groupby_time,
):
    logger.info(f"Pub domains plot, {groupby_time=}")
    if "start_date" not in locals() or not start_date:
        start_date = get_earlier_date(days=30)
    metrics = ["total_rows", "avg_days", "max_days", "rows_older_than15"]
    date_col = "updated_at"
    bar_column = "total_rows"
    query_dict = {
        "id": PUB_URLS_HISTORY,
        "start_date": start_date,
    }
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    dimensions = [x for x in df.columns if x not in metrics and x != date_col]
    if switches and len(switches) > 0:
        dimensions = [x for x in dimensions if x in switches]
        metrics = [x for x in metrics if x in switches]
        agg_default = {
            "total_rows": sum,
            "avg_days": "mean",
            "max_days": max,
            "rows_older_than15": sum,
        }
        metric_aggs = {k: v for k, v in agg_default.items() if k in metrics}
    # First agg across dimensions
    df = df.groupby([date_col] + dimensions)[metrics].agg(metric_aggs).reset_index()
    # Limit Frequency for plotting to control number of points/columns
    df = (
        df.groupby(
            [pd.Grouper(key=date_col, freq=groupby_time)] + dimensions, dropna=False
        )
        .last()
        .reset_index()
    )
    df = add_id_column(df, dimensions=dimensions)
    logger.info(f"Store apps history plot: {dimensions=} {df.shape=}")
    df = limit_rows_for_plotting(df, derived_viewport_row_ids, sort_by_columns=metrics)

    fig = overview_plot(
        df=df,
        xaxis_col=date_col,
        y_vals=metrics,
        title="Updated Counts by Date",
        stack_bars=True,
        bar_column=bar_column,
    )
    return fig
