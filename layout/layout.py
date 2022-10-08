from ids import (
    DEVELOPERS,
    DEVELOPERS_SEARCH,
    LATEST_UPDATES,
    UPDATED_AT,
    UPDATED_HISTOGRAM,
    TXT_VIEW,
    NETWORKS,
)
from layout.tab_template import create_tab_layout
import datetime
from dash import dcc
import dash_bootstrap_components as dbc


def main_content_list() -> list:
    main_content = [
        dbc.Card(
            [
                dbc.CardHeader(
                    [
                        dbc.Row(  # Top Row tabs
                            [
                                dbc.Col([TABS]),
                                dbc.Col(
                                    [
                                        dcc.DatePickerRange(
                                            id="date-picker-range",
                                            persistence_type="session",
                                            start_date=datetime.datetime.strftime(
                                                datetime.datetime.now()
                                                - datetime.timedelta(days=30),
                                                DATE_FORMAT,
                                            ),
                                            end_date=datetime.datetime.strftime(
                                                datetime.datetime.now(), DATE_FORMAT
                                            ),
                                        ),
                                    ],
                                    width={"size": "auto", "order": "last"},
                                ),
                            ],
                        ),
                        dbc.Row(
                            [
                                dbc.CardBody(id="tabs-content"),
                            ],
                        ),
                    ]
                )
            ]
        )
    ]
    return main_content


def get_tab_layout_dict():
    tab_layout = {}
    tab_tags = [x.tab_id for x in TABS.children]
    for tab_tag in tab_tags:
        default_layout = create_tab_layout(tab_tag)
        tab_layout[tab_tag] = default_layout
    return tab_layout


DATE_FORMAT = "%Y-%m-%d"

TABS = dbc.Tabs(
    id="tabs-selector",
    persistence=True,
    persistence_type="memory",
    children=[
        dbc.Tab(label="Latest Updates", tab_id=LATEST_UPDATES),
        dbc.Tab(label="Developers", tab_id=DEVELOPERS),
        dbc.Tab(label="Ad Networks", tab_id=NETWORKS),
        dbc.Tab(label="Updated Ats", tab_id=UPDATED_AT),
        dbc.Tab(label="Crawler: Updated Counts", tab_id=UPDATED_HISTOGRAM),
        dbc.Tab(label="Search: Developers", tab_id=DEVELOPERS_SEARCH),
        dbc.Tab(label="Search: Ads.txt Shared Publishers", tab_id=TXT_VIEW),
        dbc.Tab(label="Search: App-Ads.txt File ", tab_id=TXT_VIEW),
    ],
)


TAB_LAYOUT_DICT = get_tab_layout_dict()

APP_LAYOUT = dbc.Container(
    main_content_list(),
    fluid=True,
    className="dbc",
)
