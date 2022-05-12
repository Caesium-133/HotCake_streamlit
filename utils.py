import streamlit as st
import altair as alt

def space(num_lines=1):
    for _ in range(num_lines):
        st.write("")

def drawLine(data,x="",_x="",y="",_y="",title=""):
    hover = alt.selection_single(
        fields=[data.index],
        nearest=True,
        on="mouseover",
        empty="none",
    )

    lines = (
        alt.Chart(data, title=title)
            .mark_line()
            .encode(
            x=x,
            y=y,
            color="symbol",
            strokeDash="symbol",
        )
    )

    # Draw points on the line, and highlight based on selection
    points = lines.transform_filter(hover).mark_circle(size=65)

    # Draw a rule at the location of the selection
    tooltips = (
        alt.Chart(data)
            .mark_rule()
            .encode(
            x=x,
            y=y,
            opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
            tooltip=[
                alt.Tooltip(x, title=_x),
                alt.Tooltip(y, title=_y),
            ],
        )
            .add_selection(hover)
    )

    return (lines + points + tooltips).interactive()
