# from app import app
import dash
from dash import callback, Input, Output
import pandas as pd
import json
from ids import (
    AFFIX_TABLE,
    AFFIX_PLOT,
    INTERNAL_LOGS,
    AFFIX_DATE_PICKER,
)
from layout.tab_template import (
    make_columns,
    get_left_buttons_layout,
    get_tab_layout_dict,
    make_main_content_list,
)
from plotter.plotter import overview_plot
from utils import get_cached_dataframe, limit_rows_for_plotting, add_id_column


from config import get_logger

logger = get_logger(__name__)


dash.register_page(__name__, name="Internal Audits")

PAGE_ID = "internal-audit"

TAB_OPTIONS = [
    {"label": "Crawler: Updated Counts", "tab_id": INTERNAL_LOGS},
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
    table_name = "overview"
    if dash.ctx.triggered_id and not isinstance(dash.ctx.triggered_id, str):
        table_name = dash.ctx.triggered_id["index"]
    if table_name == "overview":
        metrics = ["total_rows", "avg_days", "max_days", "rows_older_than15"]
    else:
        metrics = ["updated_count", "created_count", "last_updated_count"]
    query_dict = {
        "id": INTERNAL_LOGS,
        "table_name": table_name,
        "start_date": start_date,
    }
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    dimensions = [
        x for x in df.columns if x not in metrics and x not in ["date", "updated_at"]
    ]
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
    if table_name == "overview":
        metrics = ["total_rows", "avg_days", "max_days", "rows_older_than15"]
        date_col = "updated_at"
        bar_column = "total_rows"
    else:
        metrics = ["updated_count", "created_count", "last_updated_count"]
        date_col = "date"
        bar_column = "created_count"
    query_dict = {
        "id": INTERNAL_LOGS,
        "table_name": table_name,
        "start_date": start_date,
    }
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    dimensions = [
        x for x in df.columns if x not in metrics and x not in ["date", "updated_at"]
    ]
    if table_name == "overview":
        df = (
            df.groupby(
                [pd.Grouper(key="updated_at", freq="H")] + dimensions, dropna=False
            )
            .last()
            .reset_index()
        )
    df = add_id_column(df, dimensions=dimensions)
    logger.info(f"Internal logs plot_df: {df.shape=} {dimensions=}")
    df = limit_rows_for_plotting(df, derived_viewport_row_ids, metrics=metrics)
    fig = overview_plot(
        df=df,
        xaxis_col=date_col,
        y_vals=metrics,
        title="Updated Counts by Date",
        stack_bars=True,
        bar_column=bar_column,
    )
    return fig
