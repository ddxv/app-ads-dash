from layout.tab_template import TABS
import datetime
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

DATE_FORMAT = "%Y-%m-%d"


top_padding = 15
main_content_list = html.Div(
    [
        html.Div(
            [
                dcc.DatePickerRange(
                    id="date-picker-range",
                    persistence_type="session",
                    start_date=datetime.datetime.strftime(
                        datetime.datetime.now() - datetime.timedelta(days=30),
                        DATE_FORMAT,
                    ),
                    end_date=datetime.datetime.strftime(
                        datetime.datetime.now(), DATE_FORMAT
                    ),
                ),
            ],
            style={
                "display": "inline-block",
                "padding-top": f"{top_padding}px",
                "float": "right",
            },
        ),
        html.Div(
            [
                TABS,
                html.Div(id="tabs-content"),
            ],
            style={"display": "block", "padding-top": "20px"},
        ),
    ]
)

APP_LAYOUT = dbc.Container(
    [main_content_list],
    fluid=True,
    className="dbc",
)
