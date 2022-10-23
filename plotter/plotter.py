from layout.tab_template import is_dollar, is_percent
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from config import get_logger
import plotly.io as pio

logger = get_logger(__name__)

current_theme = pio.templates.default

theme_colors = list(pio.templates[current_theme]["layout"]["colorway"])
COLORS = list(theme_colors + px.colors.qualitative.Alphabet)
PASTELS = px.colors.qualitative.Pastel1 + px.colors.qualitative.Pastel2


def horizontal_barchart(
    df: pd.DataFrame, xaxis: str, yaxis: str, title: str, xaxis_title: str = None
):
    if not xaxis_title:
        x_title = xaxis
    else:
        x_title = xaxis_title
    default_font_size = 34
    df = df.sort_values(xaxis)
    fig = go.Figure()
    bar_categories = df[yaxis].unique()
    i = 0
    for barcat in bar_categories:
        temp = df[df[yaxis] == barcat]
        my_color = "#ff0082"
        fig = fig.add_trace(
            go.Bar(
                x=temp[xaxis],
                y=temp[yaxis],
                orientation="h",
                marker={"color": my_color},
                text=f"{temp[xaxis].values[0]:.0%}",
                textposition="outside",
                textfont={"size": default_font_size, "color": "white"},
            )
        )
        domain = temp[yaxis].values[0]
        domain = domain.replace(".com", "")
        domain = domain.title()
        if i > 5:
            domain_font_size = default_font_size
        else:
            domain_font_size = int(default_font_size * 0.75)
        fig.add_annotation(
            x=0.01,
            y=i,
            text=domain,
            showarrow=False,
            font={"size": domain_font_size, "color": "white"},
            xanchor="left",
        )
        i += 1
    fig = fig.update_layout(
        {
            "showlegend": False,
            "yaxis": {"showticklabels": False},
            "font": {"size": default_font_size},
            "title": {"text": title, "font": {"size": 48}},
            "height": 800,
            "xaxis": {
                "title": x_title,
                "type": "linear",
                "side": "right",
                "tickformat": ".0%",
            },
        }
    )
    return fig


def treemap(df, path: list[str], values: str | list[str], color: str, title: str):
    df = df.head(len(PASTELS))
    df = df.reset_index(drop=True)
    color_dict = {row.ad_domain_url: PASTELS[i] for i, row in df.iterrows()}
    fig = px.treemap(
        df,
        path=path,
        values=values,
        color=color,
        color_discrete_map=color_dict,
        title=title,
    )
    return fig


def overview_plot(
    df: pd.DataFrame,
    y_vals: list[str],
    bar_column: str = None,
    stack_bars: bool = False,
    xaxis_col: str = None,
    title: str = None,
):
    # logger.info(f"Start Plot: {df.shape}, {y_vals=}")
    fig = go.Figure()
    try:
        assert xaxis_col in df.columns, f"Plotter: xaxis column not in df: {xaxis_col=}"
    except Exception as error:
        logger.error(error)
        return fig
    y_vals = [x for x in y_vals if x in df.columns]
    if df.empty:
        return {}
    yaxis1_col = []
    yaxis2_col = []
    symbol_int = -1
    y_color_int = 0
    if not bar_column:
        bar_column = guess_bar_column(df)
    if bar_column and bar_column in y_vals:
        ordered_ids = df.groupby("id")[bar_column].sum().sort_values(ascending=False)
    else:
        ordered_ids = df.groupby("id")[y_vals[0]].size().sort_values(ascending=False)
    df_ids = ordered_ids.index.unique().tolist()
    color_dims = True if len(df_ids) >= len(y_vals) else False
    plot_title = ""
    if len(df_ids) == 1:
        plot_title = df_ids[0]
    if title:
        plot_title = title
    y1_tickformat = ""
    y2_tickformat = ""
    ids_same_as_xaxis = len(set(df_ids)) == len(set(df[xaxis_col].tolist()))
    # Switch to include bar colors in the legend separately
    if (
        all([True if x == bar_column else False for x in y_vals])
        and not ids_same_as_xaxis
    ):
        show_bar_legend = True
    else:
        show_bar_legend = False
    main_ids_color_cats = ordered_ids.head(20).index.tolist()
    for y_val in y_vals:
        # symbol_int expected order: 0, 101, 302, 3, 104
        if y_val != bar_column:
            symbol_int += 1
            if symbol_int > 100:
                symbol_int += 200
            if symbol_int < 100 and symbol_int > 0:
                symbol_int += 100
            if symbol_int > 400:
                symbol_int -= 500
            # logger.info(f":{symbol_int=}")
            # symbol_int +=1
        for i in range(len(main_ids_color_cats)):
            color = COLORS[i]
            cat = main_ids_color_cats[i]
            df.loc[df.id == cat, "color"] = color
        df.loc[df.color.isnull(), "color"] = COLORS[len(main_ids_color_cats)]
        cdf = df[["id", "color"]].drop_duplicates()
        pdf = pd.pivot_table(
            df, index=[xaxis_col], columns="id", values=y_val
        ).reset_index()
        pdf = pdf.sort_values(xaxis_col)
        missing_plot_columns = [x for x in df_ids if x not in pdf.columns]
        for mcol in missing_plot_columns:
            pdf[mcol] = np.nan
        for my_id in ordered_ids.index:
            # BAR / Y-AXIS 1
            if y_val == bar_column:
                yaxis1_col.append(y_val)
                if is_percent(y_val):
                    y1_tickformat = ".0%"
                elif is_dollar(y_val):
                    y1_tickformat = "$f"
                if len(ordered_ids.index) == 1:
                    value_name = y_val
                else:
                    value_name = my_id
                temp = df[df.id == my_id]
                my_dict = dict(
                    type="bar",
                    x=temp[xaxis_col],
                    y=temp[y_val],
                    name=value_name,
                    opacity=0.8,
                    showlegend=show_bar_legend,
                    legendgroup=my_id,
                    marker=dict(
                        color=temp["color"],
                    ),
                )
            # SCATTER / Y-AXIS 2
            else:
                if stack_bars:
                    name_id = my_id.split(" ")[-1:][0]
                else:
                    name_id = my_id
                if color_dims:
                    if len([x for x in y_vals if x != bar_column]) > 1:
                        name = name_id + " " + y_val
                    else:
                        name = name_id
                    marker_dict = dict(
                        color=cdf[cdf.id == my_id].color.values[0],
                        symbol=symbol_int,
                    )
                else:
                    if len(df_ids) == 1:
                        name = y_val
                    else:
                        name = y_val + " " + name_id
                    marker_dict = dict(color=COLORS[y_color_int], symbol=symbol_int)
                # name = name.replace(dims_common_str, "")
                if is_percent(y_val):
                    y2_tickformat = ".2%"
                if is_dollar(y_val):
                    y2_tickformat = "$.3f"
                if y_val == "count":
                    line_dict = {"shape": "hv"}
                else:
                    line_dict = {"shape": "linear", "width": 1}
                yaxis2_col.append(y_val)
                my_dict = dict(
                    type="scatter",
                    x=pdf[xaxis_col],
                    y=pdf[my_id],
                    opacity=1,
                    marker=marker_dict,
                    line=line_dict,
                    legendgroup=name_id,
                    showlegend=True,
                    name=name,
                    yaxis="y2",
                    mode="markers+lines",
                )
            fig.add_trace(my_dict)
        y_color_int += 1
    if stack_bars:
        bar_type = "stack"
    else:
        bar_type = "group"
    xaxis_title = titlelize(xaxis_col)
    yaxis1_title = titlelize(yaxis1_col)
    yaxis2_title = titlelize(yaxis2_col)
    plot_title = titlelize(plot_title)
    layout = {
        "height": 600,
        "title": {"text": plot_title},
        "xaxis": {
            "title": xaxis_title,
        },
        "yaxis": {
            "title": yaxis1_title,
            "type": "linear",
            "side": "right",
            "tickformat": y1_tickformat,
        },
        "yaxis2": {
            "title": yaxis2_title,
            "anchor": "x",
            "overlaying": "y",
            "side": "left",
            "tickformat": y2_tickformat,
            "rangemode": "tozero",
        },
        "barmode": bar_type,
        "hoverlabel": {"namelength": -1},
        "hovermode": "x unified",
        "legend": {"orientation": "h"},
    }
    fig.layout = layout
    return fig


def titlelize(original: str | list) -> str:
    if isinstance(original, list):
        title = ", ".join([x.replace("_", " ").title() for x in set(original)])
    elif isinstance(original, str):
        title = original.replace("_", " ").title()
    else:
        title = original
    return title


def guess_bar_column(df: pd.DataFrame):
    bar_columns = [
        "size",
    ]
    bar_column = None
    for bc in bar_columns:
        if bc in df.columns:
            bar_column = bc
        else:
            pass
    return bar_column
