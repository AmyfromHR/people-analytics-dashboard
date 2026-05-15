"""Hiring page — time-to-hire and source mix."""
import pandas as pd
import plotly.express as px
import streamlit as st

from lib.data import (COLORS, DEPT_ORDER, LEVEL_ORDER, TODAY, apply_filters,
                       load_employees, load_hires, sidebar_filters)

st.set_page_config(page_title="Hiring", page_icon="🎯", layout="wide")
st.title("Hiring")
st.caption("Time-to-hire from requisition open to offer accepted, plus source mix and hire volume.")

emp = load_employees()
hires = load_hires()
depts, levels = sidebar_filters(emp)
hires_f = apply_filters(hires, depts, levels)

ONE_YEAR_AGO = TODAY - pd.Timedelta(days=365)
recent = hires_f[hires_f["start_date"] >= ONE_YEAR_AGO]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Hires (12 mo)", f"{len(recent):,}")
c2.metric("Avg time-to-hire", f"{recent['time_to_hire_days'].mean():.0f} days" if len(recent) else "—")
c3.metric("Median time-to-hire", f"{recent['time_to_hire_days'].median():.0f} days" if len(recent) else "—")
c4.metric("Hires (3-yr total)", f"{len(hires_f):,}")

st.divider()

# Trend
st.markdown("##### Hiring volume by quarter")
hires_f_q = hires_f.copy()
hires_f_q["quarter"] = hires_f_q["start_date"].dt.to_period("Q").dt.to_timestamp()
vol = hires_f_q.groupby("quarter").size().reset_index(name="hires")
fig = px.bar(vol, x="quarter", y="hires", color_discrete_sequence=[COLORS["primary"]])
fig.update_layout(height=300, margin=dict(t=10, b=0), showlegend=False)
fig.update_yaxes(title=None); fig.update_xaxes(title=None)
st.plotly_chart(fig, width="stretch")

# TTH cuts
ca, cb = st.columns(2)
with ca:
    st.markdown("##### Time-to-hire by department (3-yr avg)")
    by_dept = (hires_f.groupby("department")["time_to_hire_days"].mean()
               .reindex(DEPT_ORDER).reset_index())
    fig = px.bar(by_dept.sort_values("time_to_hire_days"),
                 x="time_to_hire_days", y="department", orientation="h",
                 color_discrete_sequence=[COLORS["primary"]],
                 text="time_to_hire_days")
    fig.update_traces(texttemplate="%{text:.0f} d", textposition="outside")
    fig.update_layout(height=320, margin=dict(t=10, b=0), showlegend=False)
    fig.update_yaxes(title=None); fig.update_xaxes(title="days")
    st.plotly_chart(fig, width="stretch")

with cb:
    st.markdown("##### Time-to-hire by level (3-yr avg)")
    by_lvl = (hires_f.groupby("level")["time_to_hire_days"].mean()
              .reindex(LEVEL_ORDER).reset_index().dropna())
    fig = px.bar(by_lvl, x="level", y="time_to_hire_days",
                 category_orders={"level": LEVEL_ORDER},
                 color_discrete_sequence=[COLORS["primary"]],
                 text="time_to_hire_days")
    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
    fig.update_layout(height=320, margin=dict(t=10, b=0), showlegend=False)
    fig.update_yaxes(title="days"); fig.update_xaxes(title=None)
    st.plotly_chart(fig, width="stretch")

# Source mix
cc, cd = st.columns(2)
with cc:
    st.markdown("##### Hires by source (12 mo)")
    src = recent.groupby("source").size().reset_index(name="count").sort_values("count")
    fig = px.bar(src, x="count", y="source", orientation="h",
                 color_discrete_sequence=[COLORS["primary"]])
    fig.update_layout(height=320, margin=dict(t=10, b=0), showlegend=False)
    fig.update_yaxes(title=None); fig.update_xaxes(title=None)
    st.plotly_chart(fig, width="stretch")
with cd:
    st.markdown("##### TTH distribution (12 mo)")
    fig = px.histogram(recent, x="time_to_hire_days", nbins=25,
                       color_discrete_sequence=[COLORS["primary"]])
    fig.update_layout(height=320, margin=dict(t=10, b=0), showlegend=False, bargap=0.05)
    fig.update_yaxes(title=None); fig.update_xaxes(title="days")
    st.plotly_chart(fig, width="stretch")
