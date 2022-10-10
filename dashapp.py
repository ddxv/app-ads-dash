from app import app
from dash.dependencies import Input, Output, State
import dash
from dash.exceptions import PreventUpdate
import pandas as pd
import json
from ids import (
    AFFIX_BUTTON,
    AFFIX_GROUPBY,
    AFFIX_LOADING,
    AFFIX_RADIOS,
    AFFIX_SWITCHES,
    AFFIX_TABLE,
    DEVELOPERS_SEARCH,
    AFFIX_PLOT,
    TXT_VIEW,
    UPDATED_HISTOGRAM,
    AFFIX_DATE_PICKER,
    TXT_VIEW_TABLE,
    NETWORKS,
)
from layout.layout import APP_LAYOUT, TAB_LAYOUT_DICT
from layout.tab_template import make_columns, get_left_buttons_layout
from plotter.plotter import horizontal_barchart, treemap, overview_plot
from dbcon.queries import (
    get_app_txt_view,
    query_search_developers,
    query_updated_timestamps,
    query_networks_count,
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
    if query_dict["id"] == UPDATED_HISTOGRAM:
        df = query_updated_timestamps(
            table_name=query_dict["table_name"], start_date=query_dict["start_date"]
        )
        df["table_name"] = query_dict["table_name"]
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
    Input(UPDATED_HISTOGRAM + AFFIX_DATE_PICKER, "start_date"),
)
def histograms(n_clicks, start_date):
    logger.info(f"Updated histogram {dash.ctx.triggered_id=}")
    table_name = "store_apps"
    if (
        dash.ctx.triggered_id
        and dash.ctx.triggered_id != UPDATED_HISTOGRAM + AFFIX_TABLE
    ):
        table_name = dash.ctx.triggered_id["index"]
    metrics = ["updated_count", "created_count", "last_updated_count"]
    query_dict = {
        "id": UPDATED_HISTOGRAM,
        "table_name": table_name,
        "start_date": start_date,
    }
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    dimensions = [x for x in df.columns if x not in metrics and x != "date"]
    df = add_id_column(df, dimensions=dimensions)
    column_dicts = make_columns(dimensions, metrics)
    buttons = get_left_buttons_layout("updated-histogram", active_x=table_name)
    logger.info(f"Updated histogram: {table_name=} {df.shape=}")
    table_obj = df.to_dict("records")
    return table_obj, column_dicts, buttons, table_name


@app.callback(
    Output(UPDATED_HISTOGRAM + AFFIX_PLOT, "figure"),
    Input(UPDATED_HISTOGRAM + AFFIX_DATE_PICKER, "start_date"),
    Input(UPDATED_HISTOGRAM + "-memory-output", "data"),
    Input(UPDATED_HISTOGRAM + AFFIX_TABLE, "derived_viewport_row_ids"),
)
def histograms_plot(
    start_date,
    table_name,
    derived_viewport_row_ids,
):
    logger.info(f"Updated histogram plot {table_name=}")
    metrics = ["updated_count", "created_count", "last_updated_count"]
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
        title="Updated Counts by Date",
        stack_bars=True,
        bar_column="created_count",
    )
    return fig


@app.callback(
    Output(DEVELOPERS_SEARCH + AFFIX_TABLE, "data"),
    Output(DEVELOPERS_SEARCH + AFFIX_TABLE, "columns"),
    Input(DEVELOPERS_SEARCH + AFFIX_BUTTON, "n_clicks"),
    State(DEVELOPERS_SEARCH + "-input", "value"),
    Input(DEVELOPERS_SEARCH + AFFIX_TABLE, "derived_viewport_row_ids"),
)
def developers_search(
    button,
    input_value,
    derived_viewport_row_ids: list[str],
):
    logger.info(f"Developers Search {input_value=}")
    metrics = ["size"]
    if not input_value:
        logger.info(f"Developers Search {input_value=} prevent update")
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


operators = [
    ["ge ", ">="],
    ["le ", "<="],
    ["lt ", "<"],
    ["gt ", ">"],
    ["ne ", "!="],
    ["eq ", "="],
    ["contains "],
    ["datestartswith "],
]


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                first = name_part.find("{") + 1
                last = name_part.rfind("}")
                name = name_part[first:last]

                value_part = value_part.strip()
                v0 = value_part[0]
                if v0 == value_part[-1] and v0 in ("'", '"', "`"):
                    value = value_part[1:-1].replace("\\" + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value
    return [None] * 3


def filter_table(dff, page_current, page_size, sort_by, filter):
    original_shape = dff.shape
    if filter:
        filtering_expressions = filter.split(" && ")
        for filter_part in filtering_expressions:
            col_name, operator, filter_value = split_filter_part(filter_part)

            if operator in ("eq", "ne", "lt", "le", "gt", "ge"):
                # these operators match pandas series operator method names
                dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
            elif operator == "contains":
                dff = dff.loc[dff[col_name].str.contains(filter_value)]
            elif operator == "datestartswith":
                # this is a simplification of the front-end filtering logic,
                # only works with complete fields in standard format
                dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    if sort_by and len(sort_by):
        dff = dff.sort_values(
            [col["column_id"] for col in sort_by],
            ascending=[col["direction"] == "asc" for col in sort_by],
            inplace=False,
        )
    first = page_current * page_size
    last = (page_current + 1) * page_size
    dff = dff.iloc[first:last]
    new_shape = dff.shape
    logger.info(f"Filter table {original_shape=} -> {new_shape=}")
    return dff


@app.callback(
    Output(TXT_VIEW_TABLE, "data"),
    Output(TXT_VIEW_TABLE, "columns"),
    Output(TXT_VIEW + f"-search{AFFIX_LOADING}", "children"),
    Input(TXT_VIEW_TABLE, "page_current"),
    Input(TXT_VIEW_TABLE, "page_size"),
    Input(TXT_VIEW_TABLE, "sort_by"),
    Input(TXT_VIEW_TABLE, "filter_query"),
    Input(TXT_VIEW + AFFIX_BUTTON, "n_clicks"),
    State(TXT_VIEW + "-input", "value"),
    Input(TXT_VIEW + AFFIX_GROUPBY, "value"),
    Input(TXT_VIEW_TABLE, "derived_viewport_row_ids"),
)
def txt_view_table(
    page_current,
    page_size,
    sort_by,
    filter,
    button,
    developer_url,
    groupby,
    derived_viewport_row_ids: list[str],
):
    logger.info(f"{TXT_VIEW} Table {developer_url=}")
    metrics = ["size"]
    if not developer_url:
        PreventUpdate
    query_dict = {"id": TXT_VIEW, "developer_url": developer_url}
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    logger.info(f"{TXT_VIEW} Table {developer_url=} {df.shape=}")
    metrics = ["size"]
    df = (
        df.groupby(groupby, dropna=False)
        .size()
        .reset_index()
        .rename(columns={0: "size"})
    )
    df = filter_table(df, page_current, page_size, sort_by, filter)
    # df[df["publisher_id"] == "1137"]
    dimensions = [x for x in df.columns if x not in metrics and x != "id"]
    column_dicts = make_columns(dimensions, metrics)
    table_obj = df.to_dict("records")
    return table_obj, column_dicts, ""


@app.callback(
    Output(NETWORKS + AFFIX_TABLE, "data"),
    Output(NETWORKS + AFFIX_TABLE, "columns"),
    Output(NETWORKS + AFFIX_PLOT, "figure"),
    Input(NETWORKS + AFFIX_TABLE, "derived_viewport_row_ids"),
    Input(NETWORKS + AFFIX_SWITCHES, "value"),
    Input(NETWORKS + AFFIX_RADIOS, "value"),
)
def networks_table(
    derived_viewport_row_ids: list[str], switches: list[str], radios: str
):
    logger.info(f"{NETWORKS} start")
    metrics = ["size"]
    if switches and "top_only" in switches:
        top_only = True
    else:
        top_only = False
    query_dict = {"id": NETWORKS, "top_only": top_only}
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    if switches and "view_reseller" in switches:
        df = df[df["relationship"] == "RESELLER"]
    else:
        df = df[df["relationship"] == "DIRECT"]
    num_sites = df["publishers_count"].sum()
    df["percent"] = df["publishers_count"] / num_sites
    df = df.sort_values("percent", ascending=False)
    metrics = ["percent"]
    dimensions = [x for x in df.columns if x not in metrics]
    df = add_id_column(df, dimensions=dimensions)

    df["percent"] = df["publishers_count"] / df["publishers_total"]

    column_dicts = make_columns(dimensions, metrics)
    table_obj = df.to_dict("records")
    df = limit_rows_for_plotting(
        df=df, row_ids=derived_viewport_row_ids, metrics=metrics
    )
    if top_only:
        title = "Ad Network Marketshare of Top Apps"
    else:
        title = "Ad Network Marketshare of All Apps"
    xaxis_col = "ad_domain_url"
    bar_column = "percent"
    y_vals = metrics
    if radios and "view_treemap" in radios:
        path = [xaxis_col]
        values = "percent"
        color = xaxis_col
        fig = treemap(df, path=path, values=values, color=color, title=title)
    elif radios and "view_horizontalbars" in radios:
        df = df.head(10)
        df = df.reset_index(drop=True)
        fig = horizontal_barchart(
            df,
            xaxis=bar_column,  # Note switched
            yaxis=xaxis_col,  # Note switched
            title=title,
        )
    else:
        fig = overview_plot(
            df=df,
            y_vals=y_vals,
            xaxis_col=xaxis_col,
            bar_column=bar_column,
            title=title,
        )
    return table_obj, column_dicts, fig


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
