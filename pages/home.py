from dash import html, dcc
import dash

dash.register_page(__name__, name="Home", path="/")

with open("README.md") as f:
    README_LINES = f.readlines()

layout = html.Div(
    children=[
        html.Div(dcc.Markdown(README_LINES)),
    ]
)

dash.register_page(__name__, name="Home", path="/", layout=layout)
