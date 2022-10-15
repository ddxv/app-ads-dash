import dash
import dash_bootstrap_components as dbc
from dash import dcc
from config import get_logger
from server import server
from dash_bootstrap_templates import load_figure_template


logger = get_logger(__name__)

dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"


# This loads the "cyborg" themed figure template from dash-bootstrap-templates library,
# adds it to plotly.io and makes it the default figure template.
load_figure_template("darkly")

app = dash.Dash(
    name=__name__,
    server=server,
    external_stylesheets=[dbc.themes.DARKLY, dbc_css],
    use_pages=True,
    suppress_callback_exceptions=True,
)


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
