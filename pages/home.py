from dash import html
import dash

dash.register_page(__name__, name="Home", path="/")

layout = html.Div(
    children=[
        html.H1(children="This is our Home page"),
        html.Div(
            children="""
        This is our Home page content.
    """
        ),
    ]
)

dash.register_page(__name__, name="Home", path="/", layout=layout)
