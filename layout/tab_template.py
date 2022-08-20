from dash.dash_table import FormatTemplate
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash import dash_table
from plotly import graph_objects as go
from dbcon.queries import query_overview
from config import get_logger

logger = get_logger(__name__)


def make_tab_options(tab_id: str) -> html.Div:
    options_div = html.Div()
    if "latest-updates" == tab_id:
        default_values = [""]
        switch_options = [
            {
                "label": "",
                "value": "",
            },
        ]
        groupby_options = [{"label": x, "value": x} for x in OVERVIEW_COLUMNS]
        groupby_defaults = ["publisher_id", "developer_domain", "txt_updated_at"]
        options_div = make_options_div(
            tab_id,
            groupby_options=groupby_options,
            groupby_defaults=groupby_defaults,
            switch_options=switch_options,
            switch_defaults=default_values,
            groupby_time=True,
        )
    return options_div


def make_table_div(tab_id):
    table_div = html.Div(
        [
            dash_table.DataTable(
                id=f"{tab_id}-df-table-overview",
                style_header={
                    "overflowX": "scroll",
                    "fontWeight": "bold",
                },
                filter_action="native",
                filter_options={"case": "insensitive"},
                sort_action="native",
                sort_mode="multi",
                page_action="native",
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


def make_plot_div(tab_id):
    second_plot = html.Div()
    if tab_id in ["data-import"]:
        second_plot = html.Div(
            dcc.Graph(
                id=f"{tab_id}-overview-plot2",
                config={"displaylogo": False},
                figure=go.Figure(),
            )
        )

    plot_div = html.Div(
        [
            dcc.Loading(
                children=[
                    dcc.Graph(
                        id=f"{tab_id}-overview-plot",
                        config={"displaylogo": False},
                        figure=go.Figure(),
                    ),
                    second_plot,
                ]
            ),
        ],
        style={
            "padding": "15px",
        },
    )
    return plot_div


def create_tab_layout(tab_id):
    options_div = make_tab_options(tab_id)
    table_div = make_table_div(tab_id)
    plot_div = make_plot_div(tab_id)
    tab_layout = html.Div(
        [
            html.Div(
                [
                    options_div,
                    table_div,
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        plot_div,
                    )
                ]
            ),
        ],
    )
    return tab_layout


def make_groupby_time_column(tab_id: str, groupby_time: bool):
    time_col = dbc.Col([])
    if groupby_time:
        time_col.children.append(
            dbc.Select(
                id=f"{tab_id}-groupby-time",
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
                id=f"{tab_id}-groupby",
                options=groupby_columns,
                multi=True,
                placeholder="Select Groupby...",
                persistence=True,
                persistence_type="memory",
                value=groupby_defaults,
            )
        )
    return groupby_col


def make_switch_options(tab_id, switch_options, switch_defaults):
    checklist_col = dbc.Col([])
    if not switch_defaults:
        switch_defaults = []
    if switch_options:
        checklist_col.children.append(
            dbc.Checklist(
                options=switch_options,
                value=switch_defaults,
                id=f"{tab_id}-switches",
                inline=True,
                switch=True,
            ),
        )
    return checklist_col


def make_options_div(
    tab_id=str,
    groupby_options: list[dict] = None,
    groupby_defaults: list[str] = None,
    switch_options: list[dict] = None,
    switch_defaults: list[str] = None,
    groupby_time: bool = None,
) -> html.Div:
    options_row = dbc.Row([])
    groupby_col = make_groupby_column(tab_id, groupby_options, groupby_defaults)
    options_row.children.append(groupby_col)
    checklist = make_switch_options(tab_id, switch_options, switch_defaults)
    options_row.children.append(checklist)
    time_col = make_groupby_time_column(tab_id, groupby_time)
    options_row.children.append(time_col)
    options_row = html.Div([options_row], style={"padding": "15px"})
    return options_row


def is_percent(name):
    return any(True for x in PERCENT_NAMES if x in name)


def is_dollar(name):
    return any(True for x in DOLLAR_NAMES if x in name)


def make_columns(dimensions, metrics):
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


logger.info("Set layout column defaults")
OVERVIEW_COLUMNS = query_overview(limit=1).columns.tolist()


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

TABS = dbc.Tabs(
    id="tabs-selector",
    persistence=True,
    persistence_type="memory",
    children=[
        dbc.Tab(label="Latest Updates", tab_id="latest-updates"),
    ],
)
TAB_LAYOUT_DICT = {}
tab_tags = [x.tab_id for x in TABS.children]
for tab_tag in tab_tags:
    default_layout = create_tab_layout(tab_tag)
    TAB_LAYOUT_DICT[tab_tag] = default_layout
