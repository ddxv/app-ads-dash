import json

import dash
from dash import Input, Output, State, callback
from dash.exceptions import PreventUpdate

from config import get_logger
from ids import (
    AFFIX_BUTTON,
    AFFIX_GROUPBY,
    AFFIX_LOADING,
    AFFIX_PLOT,
    AFFIX_RADIOS,
    AFFIX_SWITCHES,
    AFFIX_TABLE,
    DEVELOPERS_SEARCH,
    NETWORK_UNIQUES,
    NETWORKS,
    TXT_VIEW,
    TXT_VIEW_TABLE,
)
from layout.tab_template import (
    get_tab_layout_dict,
    make_columns,
    make_main_content_list,
)
from plotter.plotter import horizontal_barchart, overview_plot, treemap
from utils import (
    add_id_column,
    get_cached_dataframe,
    limit_rows_for_plotting,
    titlelize,
)

logger = get_logger(__name__)
logger.info("app_ads initialize")

dash.register_page(__name__, name="App-Ads.txt Insights", path="/ads")


APP_TAB_OPTIONS = [
    {"label": "Ad Networks", "tab_id": NETWORKS},
    {"label": "Ad Network: Uniqueness Ranking", "tab_id": NETWORK_UNIQUES},
    {"label": "Search: Developers", "tab_id": DEVELOPERS_SEARCH},
    {"label": "Search App-Ads.txt File", "tab_id": TXT_VIEW},
]


PAGE_ID = "analytics"

APP_TABS_DICT = get_tab_layout_dict(page_id=PAGE_ID, tab_options=APP_TAB_OPTIONS)

layout = make_main_content_list(page_id=PAGE_ID, tab_options=APP_TAB_OPTIONS)


@callback(
    Output(PAGE_ID + "-tabs-content", "children"),
    Input(PAGE_ID + "-tabs-selector", "active_tab"),
)
def render_content(tab):
    logger.info(f"Loading tab: {tab}")
    return APP_TABS_DICT[tab]


@callback(
    Output(DEVELOPERS_SEARCH + AFFIX_TABLE, "rowData"),
    Output(DEVELOPERS_SEARCH + AFFIX_TABLE, "columnDefs"),
    Input(DEVELOPERS_SEARCH + AFFIX_BUTTON, "n_clicks"),
    State(DEVELOPERS_SEARCH + "-input", "value"),
    Input(DEVELOPERS_SEARCH + AFFIX_TABLE, "virtualRowData"),
)
def developers_search(
    button,
    input_value,
    virtual_row_data: list[str],
):
    logger.info(f"Developers Search {input_value=}")
    metrics = ["size"]
    if not input_value:
        logger.info(f"Developers Search {input_value=} prevent update")
        raise PreventUpdate
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


def filter_table(dff, page_current, page_size, sort_by, myfilter):
    original_shape = dff.shape
    if myfilter:
        filtering_expressions = myfilter.split(" && ")
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


@callback(
    Output(TXT_VIEW_TABLE, "rowData"),
    Output(TXT_VIEW_TABLE, "columnDefs"),
    Output(TXT_VIEW + f"-search{AFFIX_LOADING}", "children"),
    Input(TXT_VIEW_TABLE, "page_current"),
    Input(TXT_VIEW_TABLE, "page_size"),
    Input(TXT_VIEW_TABLE, "sort_by"),
    Input(TXT_VIEW_TABLE, "filter_query"),
    Input(TXT_VIEW + AFFIX_BUTTON, "n_clicks"),
    State(TXT_VIEW + "-input", "value"),
    Input(TXT_VIEW + AFFIX_GROUPBY, "value"),
    Input(TXT_VIEW_TABLE, "virtualRowData"),
)
def txt_view_table(
    page_current,
    page_size,
    sort_by,
    myfilter,
    button,
    developer_url,
    groupby,
    virtual_row_data: list[str],
):
    logger.info(f"{TXT_VIEW} Table {developer_url=}")
    metrics = ["size"]
    if not developer_url:
        raise PreventUpdate
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
    df = filter_table(df, page_current, page_size, sort_by, myfilter)
    # df[df["publisher_id"] == "1137"]
    dimensions = [x for x in df.columns if x not in metrics and x != "id"]
    column_dicts = make_columns(dimensions, metrics)
    table_obj = df.to_dict("records")
    return table_obj, column_dicts, ""


@callback(
    Output(NETWORKS + AFFIX_TABLE, "rowData"),
    Output(NETWORKS + AFFIX_TABLE, "columnDefs"),
    Output(NETWORKS + AFFIX_PLOT, "figure"),
    Input(NETWORKS + AFFIX_TABLE, "virtualRowData"),
    Input(NETWORKS + AFFIX_SWITCHES, "value"),
    Input(NETWORKS + AFFIX_RADIOS, "value"),
    Input(NETWORKS + AFFIX_GROUPBY, "value"),
)
def networks_table(
    virtual_row_ids: list[str],
    switches: list[str],
    radios: str,
    dropdown: str,
):
    logger.info(f"{NETWORKS} start")
    metrics = ["size"]
    if switches and "top_only" in switches:
        top_only = True
    else:
        top_only = False
    if dropdown and dropdown != "all_data":
        logger.info(f"Networks Dropdown is {dropdown=}")
        category = dropdown
        cat_title = f"{category.replace('_', ' ').title()}"
        title = f"{cat_title} Marketshare of Programmatic Ad Networks"
        logger.info(f"Networks Dropdown is {category=}")
        query_dict: dict = {"id": "networks-with-app-metrics"}
        df = get_cached_dataframe(query_json=json.dumps(query_dict))
        df = df[df["store"] == 1]
        df = df[df["category"] == category]
        if top_only:
            error = """Top only for categories is NOT implemented, 
                requires checking publisher install count!"""
            logger.error(error)
    else:
        title = "Marketshare of Programmatic Ad Networks"
        query_dict = {"id": NETWORKS, "top_only": top_only}
        df = get_cached_dataframe(query_json=json.dumps(query_dict))
    if switches and "view_reseller" in switches:
        df = df[df["relationship"] == "RESELLER"]
    else:
        df = df[df["relationship"] == "DIRECT"]
    df["percent"] = df["publishers_count"] / df["publishers_total"]
    df = df.sort_values("percent", ascending=False)
    metrics = ["percent"]
    dimensions = [x for x in df.columns if x not in metrics]
    df = add_id_column(df, dimensions=dimensions)
    column_dicts = make_columns(dimensions, metrics)
    df = limit_rows_for_plotting(
        df=df, row_ids=virtual_row_ids, sort_by_columns=metrics
    )
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
            xaxis_title="Percent Integrated",
        )
    else:
        fig = overview_plot(
            df=df,
            y_vals=y_vals,
            xaxis_col=xaxis_col,
            bar_column=bar_column,
            title=title,
        )
    table_obj = df.to_dict("records")
    return table_obj, column_dicts, fig


@callback(
    Output(NETWORK_UNIQUES + AFFIX_TABLE, "rowData"),
    Output(NETWORK_UNIQUES + AFFIX_TABLE, "columnDefs"),
    Output(NETWORK_UNIQUES + AFFIX_PLOT, "figure"),
    Input(NETWORK_UNIQUES + AFFIX_TABLE, "virtualRowData"),
    Input(NETWORK_UNIQUES + AFFIX_RADIOS, "value"),
    Input(NETWORK_UNIQUES + AFFIX_SWITCHES, "value"),
)
def network_uniques(virtual_row_data: list[str], radios, switches):
    logger.info(f"{NETWORK_UNIQUES} start")
    metrics = ["percent"]
    query_dict = {"id": NETWORK_UNIQUES}
    df = get_cached_dataframe(query_json=json.dumps(query_dict))
    df["ad_domain_url"] = df["ad_domain_url"].apply(
        lambda x: titlelize(x.replace(".com", ""))
    )
    ascending = False
    sort_by = ["publisher_count"]
    if switches and "view_best" in switches:
        ascending = False
        title = "Uniqueness of DIRECT Publisher IDs"
    else:
        ascending = True
        title = "Worst/Smallest Uniqueness of DIRECT Publisher IDs"

    dimensions = [x for x in df.columns if x not in metrics]
    df = add_id_column(df, dimensions=dimensions)
    column_dicts = make_columns(dimensions, metrics)
    table_obj = df.to_dict("records")
    df = limit_rows_for_plotting(
        df=df,
        row_ids=virtual_row_data,
        sort_by_columns=sort_by,
        sort_ascending=ascending,
    )

    xaxis_col = "ad_domain_url"
    bar_column = "percent"
    y_vals = metrics
    df = df.sort_values(sort_by, ascending=ascending)
    if radios and "view_horizontalbars" in radios:
        df = df.head(20)
        df = df.reset_index(drop=True)
        fig = horizontal_barchart(
            df,
            xaxis=bar_column,  # Note switched
            yaxis=xaxis_col,  # Note switched
            title=title,
            xaxis_title="Average Uniqueness of Publisher IDs",
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
