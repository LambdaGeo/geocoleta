"""One chart per question, determined by field type."""
import textwrap

import pandas as pd
import plotly.express as px
import streamlit as st

from fielddash.ui.compat import FULL_WIDTH
from fielddash.core.model import Dataset, Field

# Validated categorical palette (fixed order, never recycled); beyond 8 groups, remainder becomes "Other"
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
PRIMARY = PALETTE[0]
MAX_SERIES = len(PALETTE)
OTHERS = "Other"
NO_ANSWER = "No answer"


def _wrap(text, width=60):
    return "<br>".join(textwrap.wrap(str(text), width)) or str(text)


def _layout(fig, height=None):
    fig.update_layout(
        margin=dict(l=8, r=24, t=16, b=8),
        height=height,
        bargap=0.35,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
        hoverlabel=dict(align="left"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.15)")
    return fig


def _show(fig, key):
    # `meta` makes each figure unique without using key= (which turns the chart into a widget)
    fig.update_layout(meta=key)
    st.plotly_chart(fig, **FULL_WIDTH, config={"displayModeBar": False})


def counts(df: pd.DataFrame, f: Field) -> pd.DataFrame:
    """Frequency of each response (in form order) and % of respondents."""
    if f.kind == "multi":
        answered = df[f.column].map(len) > 0
        values = df.loc[answered, f.column].explode()
        total = int(answered.sum())
    else:
        values = df[f.column].dropna()
        total = len(values)
    table = values.value_counts(sort=False).rename_axis("answer").reset_index(name="n")
    if f.kind == "categorical" and isinstance(df[f.column].dtype, pd.CategoricalDtype):
        order = list(df[f.column].cat.categories)
        table["order"] = table["answer"].map({v: i for i, v in enumerate(order)})
        table = table.sort_values("order").drop(columns="order")
    else:
        table = table.sort_values("n", ascending=False)
    table = table[table["n"] > 0]
    table["pct"] = table["n"] / total * 100 if total else 0
    return table


def _bar_counts(df, f, key):
    table = counts(df, f)
    if table.empty:
        st.caption("No responses with the current filters.")
        return
    table["label"] = table.apply(lambda r: f"{r.n} ({r.pct:.0f}%)", axis=1)
    table["answer_q"] = table["answer"].map(lambda v: _wrap(v, 40))
    fig = px.bar(
        table, x="n", y="answer_q", orientation="h", text="label",
        custom_data=["answer", "pct"],
        color_discrete_sequence=[PRIMARY],
    )
    fig.update_traces(
        textposition="outside", cliponaxis=False,
        hovertemplate="%{customdata[0]}<br>%{x} responses (%{customdata[1]:.1f}%)<extra></extra>",
    )
    fig.update_yaxes(title=None, autorange="reversed", categoryorder="array",
                     categoryarray=list(table["answer_q"]))
    fig.update_xaxes(title="responses", showticklabels=False, range=[0, table["n"].max() * 1.3])
    fig = _layout(fig, height=90 + 34 * len(table))
    fig.update_layout(margin_r=72)  # space for "n (%)" label outside the bar
    _show(fig, key)
    note = "Multiple choice: % of respondents; sum may exceed 100%." if f.kind == "multi" else ""
    total = int((df[f.column].map(len) > 0).sum()) if f.kind == "multi" else int(df[f.column].notna().sum())
    st.caption(f"{total} of {len(df)} answered. {note}")


def _fold(series: pd.Series, limit=MAX_SERIES) -> pd.Series:
    """Keeps the most frequent groups and folds the remainder into 'Other'."""
    series = series.astype(object).where(series.notna(), NO_ANSWER)
    top = series.value_counts().index[: limit - 1] if series.nunique() > limit else series.unique()
    return series.where(series.isin(top), OTHERS)


def _bar_crossed(df, f, by: Field, key):
    data = df[[f.column, by.column]].copy()
    if f.kind == "multi":
        data = data[data[f.column].map(len) > 0].explode(f.column)
    data = data.dropna(subset=[f.column])
    if data.empty:
        st.caption("No responses with the current filters.")
        return
    data[by.column] = _fold(data[by.column])
    table = data.groupby([by.column, f.column], observed=True).size().reset_index(name="n")
    table["pct"] = table["n"] / table.groupby(by.column)["n"].transform("sum") * 100

    answer_order = counts(df, f)["answer"].tolist()
    group_order = list(table.groupby(by.column)["n"].sum().sort_values(ascending=False).index)
    if f.kind == "categorical" and isinstance(df[f.column].dtype, pd.CategoricalDtype) and len(answer_order) > MAX_SERIES:
        table[f.column] = _fold(table[f.column].astype(object))
        table = table.groupby([by.column, f.column]).agg(n=("n", "sum"), pct=("pct", "sum")).reset_index()
        answer_order = [a for a in answer_order if a in set(table[f.column])] + [OTHERS]

    fig = px.bar(
        table, x="pct", y=by.column, color=f.column, orientation="h",
        custom_data=[f.column, "n"],
        category_orders={f.column: answer_order, by.column: group_order},
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(
        hovertemplate=f"{_wrap(by.label, 40)}: %{{y}}<br>%{{customdata[0]}}: %{{x:.0f}}% (%{{customdata[1]}})<extra></extra>",
    )
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title="% within group", range=[0, 100], ticksuffix="%")
    fig.update_yaxes(title=None, autorange="reversed")
    fig = _layout(fig, height=150 + 34 * table[by.column].nunique())
    fig.update_layout(margin_t=24 + 22 * ((len(answer_order) + 1) // 2))  # legend above, without covering bars
    _show(fig, key)


def _numeric(df, f, key, by: Field | None = None):
    values = df[f.column].dropna()
    if values.empty:
        st.caption("No responses with the current filters.")
        return
    discrete = (values == values.round()).all() and values.nunique() <= 11
    if by is not None:
        data = df[[f.column, by.column]].dropna(subset=[f.column]).copy()
        data[by.column] = _fold(data[by.column])
        fig = px.box(data, x=f.column, y=by.column, points="all", color_discrete_sequence=[PRIMARY])
        fig.update_yaxes(title=None)
    elif discrete:
        table = values.astype(int).value_counts().sort_index().rename_axis("value").reset_index(name="n")
        fig = px.bar(table, x="value", y="n", text="n", color_discrete_sequence=[PRIMARY])
        fig.update_traces(textposition="outside", cliponaxis=False,
                          hovertemplate="value %{x}: %{y} responses<extra></extra>")
        fig.update_xaxes(dtick=1)
        fig.update_yaxes(range=[0, table["n"].max() * 1.2])
    else:
        fig = px.histogram(values, x=f.column, color_discrete_sequence=[PRIMARY])
        fig.update_layout(showlegend=False)
    fig.update_xaxes(title=None)
    fig.update_yaxes(title="responses")
    _show(_layout(fig, height=280), key)
    st.caption(f"Mean {values.mean():.1f} · median {values.median():g} · {len(values)} responses")


def timeline(df, f: Field, key):
    dates = df[f.column].dropna()
    if dates.empty:
        st.caption("No dates with the current filters.")
        return
    span = (dates.max() - dates.min()).days
    freq, fmt, unit = ("D", "%d/%m/%Y", "day") if span <= 90 else (("W-MON", "week of %d/%m/%Y", "week") if span <= 365 else ("MS", "%b %Y", "month"))
    series = pd.Series(1, index=pd.DatetimeIndex(dates)).resample(freq, label="left", closed="left").sum()
    table = series.rename_axis("period").reset_index(name="n")
    fig = px.bar(table, x="period", y="n", color_discrete_sequence=[PRIMARY])
    fig.update_traces(hovertemplate=f"%{{x|{fmt}}}: %{{y}} entries<extra></extra>")
    st.caption(f"Entries per {unit}")
    fig.update_xaxes(title=None)
    fig.update_yaxes(title="entries")
    _show(_layout(fig, height=260), key)


def _text(df, f, key):
    answers = df[f.column].dropna().astype(str)
    answers = answers[answers.str.strip() != ""]
    if answers.empty:
        st.caption("No responses with the current filters.")
        return
    st.caption(f"{len(answers)} open-ended responses")
    st.dataframe(answers.rename("response").reset_index(drop=True), **FULL_WIDTH,
                 height=min(38 + 35 * len(answers), 300), key=key)


def render_field(dataset: Dataset, df: pd.DataFrame, f: Field, by: Field | None = None, key: str = ""):
    """Renders question `f`, optionally crossed with `by` (categorical field)."""
    key = key or f"chart_{f.column}_{by.column if by else ''}"
    if by is not None and (by.column == f.column or by.kind != "categorical"):
        by = None
    if f.kind in ("categorical", "multi"):
        (_bar_crossed(df, f, by, key) if by else _bar_counts(df, f, key))
    elif f.kind == "numeric":
        _numeric(df, f, key, by)
    elif f.kind == "date":
        timeline(df, f, key)
    elif f.kind == "text":
        _text(df, f, key)
    else:
        st.caption(f"Field type '{f.type}' has no automatic visualization.")
