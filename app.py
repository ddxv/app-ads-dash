import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from server import server
import dash

dbc_css = (
    "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.4/dbc.min.css"
)

# This loads the theme template from dash-bootstrap-templates library,
# adds it to plotly.io and makes it the default figure template.
load_figure_template("vapor")

app = dash.Dash(
    name=__name__,
    server=server,
    url_base_pathname="/dash/",
    external_stylesheets=[dbc.themes.VAPOR, dbc_css],
    suppress_callback_exceptions=True,
)
