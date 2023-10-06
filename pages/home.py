import dash
from dash import Input, Output, callback

from config import get_logger
from ids import HOME_TAB
from layout.tab_template import get_tab_layout_dict, make_main_content_list

logger = get_logger(__name__)

dash.register_page(__name__, name="Home", path="/")


HOME_OPTIONS = [
    {"label": "About", "tab_id": HOME_TAB},
]

PAGE_ID = "home"

APP_TABS_DICT = get_tab_layout_dict(page_id=PAGE_ID, tab_options=HOME_OPTIONS)

layout = make_main_content_list(page_id=PAGE_ID, tab_options=HOME_OPTIONS)


# layout = html.Div(
#     children=[
#         html.Div(dcc.Markdown(README_LINES)),
#     ]
# )
@callback(
    Output(PAGE_ID + "-tabs-content", "children"),
    Input(PAGE_ID + "-tabs-selector", "active_tab"),
)
def render_content(tab):
    logger.info(f"Loading tab: {tab}")
    return APP_TABS_DICT[tab]


dash.register_page(__name__, name="About", path="/about", layout=layout)
