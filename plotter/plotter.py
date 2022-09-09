from layout.tab_template import is_dollar, is_percent
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

COLORS = px.colors.qualitative.Alphabet


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
        ordered = df.groupby("id")[bar_column].sum().sort_values(ascending=False)
    else:
        ordered = df.groupby("id")[y_vals[0]].size().sort_values(ascending=False)
    plot_dims = ordered.index.unique().tolist()
    color_dims = True if len(plot_dims) >= len(y_vals) else False
    plot_title = ""
    if len(plot_dims) == 1:
        plot_title = plot_dims[0]
    if title:
        plot_title = title
    y1_tickformat = ""
    y2_tickformat = ""
    # logger.info(f"PLOT TYPE: {bar_column=}")
    if all([True if x == bar_column else False for x in y_vals]):
        show_bar_legend = True
    else:
        show_bar_legend = False
    # logger.warning(f"PLOT TYPE: {bar_column=}, {safe_y_vals=}")
    if xaxis_col in df.columns:
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
            main_color_cat = ordered.head(20).index.tolist()
            for i in range(len(main_color_cat)):
                color = COLORS[i]
                cat = main_color_cat[i]
                df.loc[df.id == cat, "color"] = color
            df.loc[df.color.isnull(), "color"] = COLORS[len(main_color_cat)]
            cdf = df[["id", "color"]].drop_duplicates()
            pdf = pd.pivot_table(
                df, index=[xaxis_col], columns="id", values=y_val
            ).reset_index()
            pdf = pdf.sort_values(xaxis_col)
            missing_plot_columns = [x for x in plot_dims if x not in pdf.columns]
            for mcol in missing_plot_columns:
                pdf[mcol] = np.nan
            for my_id in ordered.index:
                # BAR / Y-AXIS 1
                if y_val == bar_column:
                    yaxis1_col.append(y_val)
                    if is_dollar(y_val):
                        y1_tickformat = "$f"
                    mytype = "bar"
                    temp = df[df.id == my_id]
                    my_dict = dict(
                        type=mytype,
                        x=temp[xaxis_col],
                        y=temp[y_val],
                        name=my_id,
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
                        if len(plot_dims) == 1:
                            name = y_val
                        else:
                            name = y_val + " " + name_id
                        marker_dict = dict(color=COLORS[y_color_int], symbol=symbol_int)
                    # name = name.replace(dims_common_str, "")
                    if is_percent(y_val):
                        y2_tickformat = "%.2f"
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
        bar_type = "group"
    else:
        bar_type = "stack"
    layout = {
        "height": 600,
        "xaxis": {
            "showgrid": False,
            "title": xaxis_col,
        },
        "title": {"text": plot_title},
        "yaxis": {
            "type": "linear",
            "side": "right",
            "title": f"{','.join(set(yaxis1_col))}",
            "tickformat": y1_tickformat,
        },
        "yaxis2": {
            "title": f"{','.join(set(yaxis2_col))}",
            "anchor": "x",
            "overlaying": "y",
            "side": "left",
            "tickformat": y2_tickformat,
        },
        "barmode": bar_type,
        "hoverlabel": {"namelength": -1},
        "hovermode": "x unified",
        "legend": {"orientation": "h"},
    }
    fig.layout = layout
    return fig


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
