import dash
import dash_bootstrap_components as dbc

from app import app
from config import get_logger

logger = get_logger(__name__)


app.layout = dbc.Container(
    [
        dash.page_container,
    ],
    fluid=True,
    className="dbc",
)


if __name__ == "__main__":
    app.run_server(debug=True)
