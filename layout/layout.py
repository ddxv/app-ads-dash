import dash_bootstrap_components as dbc

from layout.tab_template import TABS


def main_content_list() -> list:
    main_content = [
        dbc.Card(
            [
                dbc.CardHeader(
                    [
                        dbc.Row(  # Top Row tabs
                            [
                                dbc.Col([TABS]),
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


APP_LAYOUT = dbc.Container(
    main_content_list(),
    fluid=True,
    className="dbc",
)
