import dash
import dash_bootstrap_components as dbc
from dash import dcc

from app import app
from config import get_logger

logger = get_logger(__name__)


app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(dcc.Link(page["name"], href=page["relative_path"]))
                for page in dash.page_registry.values()
            ]
        ),
        dash.page_container,
    ],
    fluid=True,
    className="dbc",
)


if __name__ == "__main__":
    app.run_server(debug=True)
