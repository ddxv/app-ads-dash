import datetime

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import dcc, html
from plotly import graph_objects as go

from config import DATE_FORMAT, get_logger
from dbcon.queries import APP_CATEGORIES, TABLES_WITH_TIMES
from ids import (
    AFFIX_BUTTON,
    AFFIX_DATE_PICKER,
    AFFIX_GROUPBY,
    AFFIX_GROUPBY_TIME,
    AFFIX_LEFT_MENU,
    AFFIX_LOADING,
    AFFIX_PLOT,
    AFFIX_RADIOS,
    AFFIX_SWITCHES,
    AFFIX_TABLE,
    APP_SOURCES,
    DEVELOPERS_SEARCH,
    HOME_TAB,
    INTERNAL_LOGS,
    NETWORK_UNIQUES,
    NETWORKS,
    PUB_URLS_HISTORY,
    STORE_APPS_HISTORY,
    TXT_VIEW,
)
from utils import get_earlier_date

logger = get_logger(__name__)

logger.info("layout initilialize tab templates")


def make_main_content_list(page_id: str, tab_options) -> list:
    tabs = make_tabs(page_id=page_id, tab_options=tab_options)
    main_content = [
        dbc.Card(
            [
                dbc.CardHeader(
                    [
                        dbc.Row(  # Top Row tabs
                            [
                                dbc.Col([tabs]),
                            ],
                        ),
                        dbc.Row(
                            [
                                dbc.CardBody(id=page_id + "-tabs-content"),
                            ],
                        ),
                    ]
                )
            ]
        )
    ]
    return main_content


def get_tab_layout_dict(page_id: str, tab_options: list[dict]) -> dict:
    tabs = make_tabs(page_id, tab_options=tab_options)
    tab_layout = {}
    tab_tags = [x.tab_id for x in tabs.children]
    for tab_tag in tab_tags:
        default_layout = create_tab_layout(tab_tag)
        tab_layout[tab_tag] = default_layout
    return tab_layout


def make_tabs(page_id: str, tab_options: list[dict]) -> dbc.Tabs:
    tabs = dbc.Tabs(
        id=page_id + "-tabs-selector",
        persistence=True,
        persistence_type="memory",
        children=[dbc.Tab(label=x["label"], tab_id=x["tab_id"]) for x in tab_options],
    )
    return tabs


def make_tab_options(tab_id: str) -> html.Div:
    options_div = html.Div([])
    if PUB_URLS_HISTORY == tab_id:
        switch_options = [
            {
                "label": "Crawl Outcome",
                "value": "outcome",
            },
            # Metrics
            {
                "label": "Total Rows",
                "value": "total_rows",
            },
            {
                "label": "Days Delay Average",
                "value": "avg_days",
            },
            {
                "label": "Days Delay Max",
                "value": "max_days",
            },
            {
                "label": "Rows Older than 15 Days",
                "value": "rows_older_than15",
            },
        ]
        options_div = make_options_div(
            tab_id,
            date_picker=True,
            switch_options=switch_options,
            switch_defaults=["outcome", "total_rows"],
            switch_title="Columns",
            groupby_time=True,
        )
    if APP_SOURCES == tab_id:
        switch_options = [
            {
                "label": "Crawl Source",
                "value": "crawl_source",
            },
            {
                "label": "Store",
                "value": "store",
            },
            # Metrics
            {
                "label": "App Count",
                "value": "app_count",
            },
        ]
        options_div = make_options_div(
            tab_id,
            date_picker=True,
            switch_options=switch_options,
            switch_defaults=["crawl_source", "store", "app_count"],
            switch_title="Columns",
            groupby_time=True,
        )
    if STORE_APPS_HISTORY == tab_id:
        switch_options = [
            {
                "label": "Store",
                "value": "store_name",
            },
            {
                "label": "Crawl Outcome",
                "value": "outcome",
            },
            # Metrics
            {
                "label": "Total Rows",
                "value": "total_rows",
            },
            {
                "label": "Days Delay Average",
                "value": "avg_days",
            },
            {
                "label": "Days Delay Max",
                "value": "max_days",
            },
            {
                "label": "Rows Older than 15 Days",
                "value": "rows_older_than15",
            },
        ]
        options_div = make_options_div(
            tab_id,
            date_picker=True,
            switch_options=switch_options,
            switch_defaults=["store_name", "total_rows"],
            switch_title="Columns",
            groupby_time=True,
        )
    if INTERNAL_LOGS == tab_id:
        options_div = make_options_div(tab_id, date_picker=True)
    if NETWORK_UNIQUES == tab_id:
        switch_options = [
            {
                "label": "View Best",
                "value": "view_best",
            },
        ]
        switch_defaults = ["view_best"]
        radio_options = [
            {
                "label": "View Horizontal Barchart",
                "value": "view_horizontalbars",
            },
            {
                "label": "View Vertical Barchart",
                "value": "view_verticalbars",
            },
        ]
        options_div = make_options_div(
            tab_id,
            radio_options=radio_options,
            radio_title="Plot Type",
            switch_options=switch_options,
            switch_defaults=switch_defaults,
            switch_title="Filter By",
        )
    if NETWORKS == tab_id:
        switch_options = [
            {
                "label": "View Resellers",
                "value": "view_reseller",
            },
            {
                "label": "View Top 5%",
                "value": "top_only",
            },
        ]
        radio_options = [
            {
                "label": "View Horizontal Barchart",
                "value": "view_horizontalbars",
            },
            {
                "label": "View Vertical Barchart",
                "value": "view_verticalbars",
            },
            {
                "label": "View Treemap Plot",
                "value": "view_treemap",
            },
        ]
        groupby_options = [{"label": "All Categories", "value": "all_data"}] + [
            {"label": x.replace("_", " ").title(), "value": x} for x in APP_CATEGORIES
        ]
        groupby_defaults = "all_data"
        options_div = make_options_div(
            tab_id,
            switch_options=switch_options,
            switch_title="Filter By",
            radio_options=radio_options,
            radio_title="Plot Type",
            dropdown_options=groupby_options,
            dropdown_defaults=groupby_defaults,
            dropdown_title="Select Category",
            dropdown_multi=False,
        )
    if DEVELOPERS_SEARCH == tab_id:
        options_div = make_options_div(tab_id, search_hint="Name, ids or URL parts...")
    if TXT_VIEW == tab_id:
        groupby_options = [{"label": x, "value": x} for x in TXT_VIEW_COLUMNS]
        groupby_defaults = "ad_domain_url"
        options_div = make_options_div(
            tab_id,
            dropdown_options=groupby_options,
            dropdown_defaults=groupby_defaults,
            dropdown_title="Group By",
            search_hint="Developer URL ...",
        )
    return options_div


def make_table_div(tab_id: str) -> html.Div:
    default_col_def = {
        "filter": True,
        "resizable": True,
        "sortable": True,
        "editable": False,
        "floatingFilter": True,
    }
    table_div = html.Div(
        [
            dag.AgGrid(
                id=tab_id + AFFIX_TABLE,
                defaultColDef=default_col_def,
                columnSize="sizeToFit",
                className="ag-theme-alpine-dark",
            ),
        ],
    )
    return table_div


def make_plot_div(tab_id: str) -> html.Div:
    plot_div = html.Div(
        [
            dcc.Loading(
                children=[
                    dcc.Graph(
                        id=tab_id + AFFIX_PLOT,
                        config={"displaylogo": False},
                        figure=go.Figure(),
                    ),
                ]
            ),
        ],
        style={
            "padding": "15px",
        },
    )
    return plot_div


def create_tab_layout(tab_id: str) -> html.Div:
    options_div = make_tab_options(tab_id)
    table_div = make_table_div(tab_id)
    plot_div = make_plot_div(tab_id)
    if tab_id == INTERNAL_LOGS:
        tables = TABLES_WITH_TIMES
    else:
        tables = None
    buttons_div = get_left_buttons_layout(tab_id, tables=tables)
    if tab_id == HOME_TAB:
        tab_content = [dcc.Markdown(README_LINES, dangerously_allow_html=True)]
    else:
        tab_content = [
            plot_div,
            options_div,
            table_div,
        ]
    tab_layout = html.Div(
        [
            dcc.Store(id=f"{tab_id}-memory-output", storage_type="memory"),
            dbc.Row(  # Entire Page Row
                [
                    None
                    if tab_id not in [INTERNAL_LOGS, STORE_APPS_HISTORY]
                    else dbc.Col(
                        [buttons_div],
                        width={"size": 2, "order": "first"},
                    ),
                    dbc.Col(tab_content),
                ]
            ),
            dbc.Row([dbc.Col()]),
        ],
    )
    return tab_layout


def make_groupby_time_column(tab_id: str, groupby_time: bool | None) -> dbc.Col:
    time_col = dbc.Col([])
    if groupby_time:
        time_col.children.append(
            dbc.Select(
                id=tab_id + AFFIX_GROUPBY_TIME,
                options=[
                    {"label": "Plot Hourly", "value": "1H"},
                    {"label": "Plot Daily", "value": "1D"},
                    {"label": "Plot Weekly", "value": "7D"},
                ],
                value="1D",
            ),
        )
    return time_col


def make_radio_buttons(
    tab_id: str,
    radio_options: list[dict[str, str]] | None,
    radio_default: str | None = None,
    title: str | None = None,
) -> dbc.Col:
    button_group = dbc.Col([])
    if title:
        header = html.H4(title)
        button_group.children.append(header)
    if radio_options:
        if not radio_default:
            radio_default = radio_options[0]["value"]
        button_group = dbc.Col(
            [
                dbc.RadioItems(
                    id=tab_id + AFFIX_RADIOS,
                    className="btn-group",
                    inputClassName="btn-check",
                    labelClassName="btn btn-outline-primary",
                    labelCheckedClassName="active",
                    options=radio_options,
                    value=radio_default,
                ),
                html.Div(id="output"),
            ],
            className="radio-group",
        )
    return button_group


def make_dropdown(
    tab_id: str,
    dropdown_options: list[dict[str, str]] | None,
    dropdown_defaults: str | None,
    dropdown_multi: bool = True,
    title: str | None = None,
) -> dbc.Col:
    groupby_col = dbc.Col([])
    if title:
        header = html.H4(title)
        groupby_col.children.append(header)
    if dropdown_options and not dropdown_defaults:
        dropdown_defaults = dropdown_options[0]["value"]
    if dropdown_options:
        groupby_col.children.append(
            dcc.Dropdown(
                id=tab_id + AFFIX_GROUPBY,
                options=dropdown_options,
                multi=dropdown_multi,
                placeholder="Select ...",
                persistence=True,
                persistence_type="memory",
                value=dropdown_defaults,
            )
        )
    return groupby_col


def make_switch_options(
    tab_id: str,
    switch_options: list[dict[str, str]] | None,
    switch_defaults: list[str] | None,
    title: str | None,
) -> dbc.Col:
    checklist_col = dbc.Col([])
    if title:
        header = html.H4(title)
        checklist_col.children.append(header)
    if not switch_defaults:
        switch_defaults = []
    if switch_options:
        checklist_col.children.append(
            dbc.Checklist(
                options=switch_options,
                value=switch_defaults,
                id=tab_id + AFFIX_SWITCHES,
                inline=True,
                switch=True,
            ),
        )
    return checklist_col


def make_date_picker_column(tab_id: str, date_picker: bool | None) -> dbc.Col:
    date_picker_col = dbc.Col([])
    if date_picker:
        date_picker_col = dbc.Col(
            [
                dcc.DatePickerRange(
                    id=tab_id + AFFIX_DATE_PICKER,
                    persistence_type="session",
                    start_date=get_earlier_date(days=30),
                    end_date=datetime.datetime.strftime(
                        datetime.datetime.now(), DATE_FORMAT
                    ),
                ),
            ],
            width={"size": "auto", "order": "last"},
        )
    return date_picker_col


def make_search_column(tab_id: str, search_hint: str | None) -> dbc.Col:
    search_col = dbc.Col([])
    if search_hint:
        search_col.children.append(
            dbc.InputGroup(
                [
                    dbc.Input(
                        id=f"{tab_id}-input", placeholder=search_hint, debounce=True
                    ),
                    dbc.Button(
                        [
                            "Search ",
                            dbc.Spinner(
                                [html.Div(id=f"{tab_id}-search{AFFIX_LOADING}")],
                                size="sm",
                                show_initially=False,
                            ),
                        ],
                        id=tab_id + AFFIX_BUTTON,
                        n_clicks=0,
                    ),
                ]
            )
        )
    return search_col


def make_options_div(
    tab_id=str,
    dropdown_options: list[dict[str, str]] | None = None,
    dropdown_defaults: str | None = None,
    dropdown_multi: bool = True,
    dropdown_title: str | None = None,
    switch_options: list[dict[str, str]] | None = None,
    switch_defaults: list[str] | None = None,
    switch_title: str | None = None,
    radio_options: list[dict[str, str]] | None = None,
    radio_default: str | None = None,
    radio_title: str | None = None,
    groupby_time: bool | None = None,
    date_picker: bool | None = None,
    search_hint: str | None = None,
) -> html.Div:
    options_row = dbc.Row([])
    search_col = make_search_column(tab_id, search_hint)
    if len(search_col.children) > 0:
        options_row.children.append(search_col)
    groupby_col = make_dropdown(
        tab_id,
        dropdown_options,
        dropdown_defaults,
        dropdown_multi=dropdown_multi,
        title=dropdown_title,
    )
    if len(groupby_col.children) > 0:
        options_row.children.append(groupby_col)
    checklist_col = make_switch_options(
        tab_id, switch_options, switch_defaults, title=switch_title
    )
    if len(checklist_col.children) > 0:
        options_row.children.append(checklist_col)
    radios_col = make_radio_buttons(
        tab_id, radio_options, radio_default, title=radio_title
    )
    if len(radios_col.children) > 0:
        options_row.children.append(radios_col)
    time_col = make_groupby_time_column(tab_id, groupby_time)
    if len(time_col.children) > 0:
        options_row.children.append(time_col)
    date_picker_col = make_date_picker_column(tab_id, date_picker)
    if len(date_picker_col.children) > 0:
        options_row.children.append(date_picker_col)
    options_row = html.Div([options_row], style={"padding": "15px"})
    return options_row


def is_percent(name: str) -> bool:
    return any(True for x in PERCENT_NAMES if x in name.lower())


def is_dollar(name: str) -> bool:
    return any(True for x in DOLLAR_NAMES if x in name.lower())


def make_columns(dimensions: list[str], metrics: list[str]) -> list[dict]:
    dimensions_new = [
        {
            "headerName": i.replace("_", " ").title(),
            "field": i,
            "id": i,
            "selectable": False,
            "type": "text",
        }
        for i in dimensions
    ]
    money_metrics = [m for m in metrics if is_dollar(m)]
    percent_metrics = [m for m in metrics if is_percent(m) and m not in money_metrics]
    numeric_metrics = [x for x in metrics if x not in percent_metrics + money_metrics]
    money_metrics_new = [
        {
            "headerName": i.replace("_", " ").title(),
            "name": i,
            "id": i,
            "type": "numeric",
            "valueFormatter": {"function": "d3.format('($,.2f')(params.value)"},
        }
        for i in money_metrics
    ]
    percent_metrics_new = [
        {
            "headerName": i.replace("_", " ").title(),
            "field": i,
            "id": i,
            "type": "numeric",
            "valueFormatter": {"function": "d3.format(',.1%')(params.value)"},
        }
        for i in percent_metrics
    ]
    numeric_metrics_new = [
        {
            "headerName": i.replace("_", " ").title(),
            "field": i,
            "id": i,
            "type": "numeric",
        }
        for i in numeric_metrics
    ]
    metric_columns = numeric_metrics_new + money_metrics_new + percent_metrics_new

    columns = dimensions_new + metric_columns
    print(columns)
    return columns


def get_left_buttons_layout(
    tab_id, info=None, active_x=None, tables: list[str] | None = None
) -> html.Div:
    mydiv = html.Div([])
    if tables:
        mydiv = dbc.ButtonGroup(
            [
                dbc.Button(
                    [
                        html.Strong(x),
                        ""
                        if not info
                        else f" {info[x]['updated_at'].strftime('%Y-%m-%d %H:%M')}",
                    ],
                    color="secondary" if x != active_x else "primary",
                    id={"type": tab_id + AFFIX_LEFT_MENU, "index": x},
                    style={"text-align": "left"},
                )
                for x in tables
            ],
            vertical=True,
            id=f"{tab_id}-buttongroup",
        )
    return mydiv


TXT_VIEW_COLUMNS = [
    "my_domain_url",
    "their_domain_url",
    "publisher_id",
    "ad_domain_url",
    "ad_domain_id",
    "relationship",
    "is_my_id",
    "txt_entry_crawled_at",
    "developer_domain_crawled_at",
]


DOLLAR_NAMES = [
    "arpu",
    "cpi",
    "cpm",
    "cost",
    "spend",
    "ecpi",
    "cpm",
    "rev",
    "rule",
]

PERCENT_NAMES = ["roas", "ctr", "ctr", "percent"]

with open("README.md") as f:
    README_LINES = f.read()
