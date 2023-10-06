import dash
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from flask import render_template_string

from config import get_logger
from server import server

dbc_css = (
    "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.4/dbc.min.css"
)


logger = get_logger(__name__)

logger.info("dash load start")

with server.app_context():
    navbar = render_template_string(open("templates/navbar.html").read())


INDEX_STRING = (
    f"""
<!DOCTYPE html>
<html>
    {navbar}
    <head>
    """
    + """
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>

"""
)


# This loads the theme template from dash-bootstrap-templates library,
# adds it to plotly.io and makes it the default figure template.
load_figure_template("pulse")

app = dash.Dash(
    name=__name__,
    server=server,
    url_base_pathname="/dash/",
    external_stylesheets=[dbc.themes.PULSE, dbc_css],
    suppress_callback_exceptions=True,
    use_pages=True,
    index_string=INDEX_STRING,
)
