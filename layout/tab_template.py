from dash.dash_table import FormatTemplate
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash import dash_table
from plotly import graph_objects as go
from dbcon.queries import TABLES_WITH_TIMES, query_overview, SCHEMA_OVERVIEW
from config import get_logger
from ids import (
    AFFIX_GROUPBY_TIME,
    AFFIX_LOADING,
    AFFIX_PLOT,
    AFFIX_GROUPBY,
    AFFIX_SWITCHES,
    AFFIX_TABLE,
    DEVELOPERS,
    LATEST_UPDATES,
    TXT_VIEW,
    DEVELOPERS_SEARCH,
    AFFIX_BUTTON,
)

logger = get_logger(__name__)


def make_tab_options(tab_id: str) -> html.Div:
    options_div = html.Div([])

    if DEVELOPERS_SEARCH == tab_id:
        options_div = make_options_div(tab_id, search_hint="Name, ids or URL parts...")
    if TXT_VIEW == tab_id:
        switch_defaults = [""]
        groupby_options = [{"label": x, "value": x} for x in TXT_VIEW_COLUMNS]
        groupby_defaults = ["my_domain_url", "ad_domain_url"]
        options_div = make_options_div(
            tab_id,
            groupby_options=groupby_options,
            groupby_defaults=groupby_defaults,
            search_hint="Developer URL ...",
        )

    if DEVELOPERS == tab_id:
        switch_defaults = [""]
        groupby_options = [{"label": x, "value": x} for x in DEVELOPERS_COLUMNS]
        groupby_defaults = ["name"]
        options_div = make_options_div(
            tab_id,
            groupby_options=groupby_options,
            groupby_defaults=groupby_defaults,
        )

    if LATEST_UPDATES == tab_id:
        switch_defaults = [""]
        switch_options = [
            {
                "label": "",
                "value": "",
            },
        ]
        groupby_options = [{"label": x, "value": x} for x in OVERVIEW_COLUMNS]
        groupby_defaults = ["publisher_id", "developer_domain_url"]
        options_div = make_options_div(
            tab_id,
            groupby_options=groupby_options,
            groupby_defaults=groupby_defaults,
            switch_options=switch_options,
            switch_defaults=switch_defaults,
            groupby_time=True,
        )
        options_div.children.insert(0, get_cards_group())
    return options_div


def make_table_div(tab_id: str) -> html.Div:
    if tab_id in [TXT_VIEW]:
        page_action = "custom"
        sort_action = "custom"
        filter_action = "custom"
    else:
        page_action = "native"
        sort_action = "native"
        filter_action = "native"
    table_div = html.Div(
        [
            dash_table.DataTable(
                id=tab_id + AFFIX_TABLE,
                style_header={
                    "overflowX": "scroll",
                    "fontWeight": "bold",
                },
                filter_action=filter_action,
                filter_options={"case": "insensitive"},
                sort_action=sort_action,
                sort_mode="multi",
                page_action=page_action,
                page_current=0,
                page_size=15,
                style_table={"overflowX": "auto"},
                persistence=False,
                persisted_props=[
                    "columns.name",
                    "hidden_columns",
                    "sort_by",
                ],
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
    buttons_div = get_left_buttons_layout(tab_id)
    tab_layout = html.Div(
        [
            dcc.Store(id=f"{tab_id}-memory-output", storage_type="memory"),
            dbc.Row(  # Entire Page Row
                [
                    None
                    if tab_id != "updated-histogram"
                    else dbc.Col(
                        [buttons_div],
                        width={"size": 2, "order": "first"},
                    ),
                    dbc.Col(
                        [
                            options_div,
                            table_div,
                            plot_div,
                        ]
                    ),
                ]
            ),
            dbc.Row([dbc.Col()]),
        ],
    )
    return tab_layout


def make_groupby_time_column(tab_id: str, groupby_time: bool) -> dbc.Col:
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


def make_groupby_column(
    tab_id, groupby_columns: list[dict], groupby_defaults: list[str] | None
) -> dbc.Col:
    groupby_col = dbc.Col([])
    if groupby_columns and not groupby_defaults:
        groupby_defaults = [groupby_columns[0]["value"]]
    if groupby_columns:
        groupby_col.children.append(
            dcc.Dropdown(
                id=tab_id + AFFIX_GROUPBY,
                options=groupby_columns,
                multi=True,
                placeholder="Select Groupby...",
                persistence=True,
                persistence_type="memory",
                value=groupby_defaults,
            )
        )
    return groupby_col


def make_switch_options(
    tab_id: str, switch_options: list[str] | None, switch_defaults: list[str] | None
) -> dbc.Col:
    checklist_col = dbc.Col([])
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


def make_search_column(tab_id: str, search_hint: str | None) -> dbc.Col:
    search_col = dbc.Col([])
    if search_hint:
        search_col.children.append(
            dbc.InputGroup(
                [
                    dbc.Input(id=f"{tab_id}-input", placeholder=search_hint),
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
    groupby_options: list[dict] = None,
    groupby_defaults: list[str] = None,
    switch_options: list[dict] = None,
    switch_defaults: list[str] = None,
    groupby_time: bool = None,
    search_hint: str = None,
) -> html.Div:
    options_row = dbc.Row([])
    search_col = make_search_column(tab_id, search_hint)
    options_row.children.append(search_col)
    groupby_col = make_groupby_column(tab_id, groupby_options, groupby_defaults)
    options_row.children.append(groupby_col)
    checklist = make_switch_options(tab_id, switch_options, switch_defaults)
    options_row.children.append(checklist)
    time_col = make_groupby_time_column(tab_id, groupby_time)
    options_row.children.append(time_col)
    options_row = html.Div([options_row], style={"padding": "15px"})
    return options_row


def is_percent(name: str) -> bool:
    return any(True for x in PERCENT_NAMES if x in name)


def is_dollar(name: str) -> bool:
    return any(True for x in DOLLAR_NAMES if x in name)


def make_columns(dimensions: list[str], metrics: list[str]) -> list[dict]:
    dimensions = [
        {"name": i, "id": i, "selectable": False, "type": "text"} for i in dimensions
    ]
    money_metrics = [m for m in metrics if is_dollar(m)]
    percent_metrics = [m for m in metrics if is_percent(m) and m not in money_metrics]
    numeric_metrics = [x for x in metrics if x not in percent_metrics + money_metrics]
    money_metrics = [
        {
            "name": i,
            "id": i,
            "type": "numeric",
            "format": FormatTemplate.money(2),
        }
        for i in money_metrics
    ]
    percent_metrics = [
        {
            "name": i,
            "id": i,
            "type": "numeric",
            "format": FormatTemplate.percentage(2),
        }
        for i in percent_metrics
    ]
    numeric_metrics = [
        {"name": i, "id": i, "selectable": True, "type": "numeric"}
        for i in numeric_metrics
    ]
    metric_columns = numeric_metrics + money_metrics + percent_metrics

    columns = dimensions + metric_columns
    return columns


def get_cards_group() -> dbc.CardGroup:
    card_group = dbc.CardGroup(
        [
            dbc.Card(
                [
                    dbc.CardHeader("App-Ads.txt File Last Pulled"),
                    dbc.CardBody(
                        [
                            html.H5("Card title", className="card-title"),
                            html.P(
                                "Last time an App-Ads.txt file was updated",
                                className="card-text",
                            ),
                        ],
                        id="txt-entry-crawled-at-body",
                    ),
                ],
                color="primary",
                inverse=True,
                id="txt-entry   -crawled-at",
            ),
            dbc.Card(
                [
                    dbc.CardHeader("Store Info Last Pulled"),
                    dbc.CardBody(
                        [
                            html.H5("Card title", className="card-title"),
                            html.P(
                                "Last time the store info for apps was pulled",
                                className="card-text",
                            ),
                        ],
                        id="ad-domain-updated-at-body",
                    ),
                ],
                color="secondary",
                inverse=True,
                id="ad-domain-updated-at",
            ),
        ],
        id="cards-group",
    )
    cards = html.Div(
        [
            dbc.Row(
                [
                    card_group,
                ],
                className="mb-4",
            ),
        ]
    )
    return cards


def get_left_buttons_layout(tab_id, info=None, active_x=None) -> html.Div:
    mydiv = html.Div([])
    tables = ["overview"] + TABLES_WITH_TIMES
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
                id={"type": "left-menu", "index": x},
                style={"text-align": "left"},
            )
            for x in tables
        ],
        vertical=True,
        id=f"{tab_id}-buttongroup",
    )
    return mydiv


logger.info("Set layout column defaults")
# Is a materialized view
OVERVIEW_COLUMNS = query_overview(limit=1).columns.tolist()

DEVELOPERS_COLUMNS = SCHEMA_OVERVIEW[
    SCHEMA_OVERVIEW["table_name"] == "developers"
].column_name.tolist()

TXT_VIEW_COLUMNS = [
    "my_domain_url",
    "their_domain_url",
    "publisher_id",
    "ad_domain_url",
    "ad_domain_id",
    "relationship",
    "is_my_id",
    "txt_entry_crawled_at",
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
