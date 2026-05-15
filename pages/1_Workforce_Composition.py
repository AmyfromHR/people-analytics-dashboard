"""Workforce composition page."""
import pandas as pd
import plotly.express as px
import streamlit as st

from lib.data import (COLORS, DEPT_ORDER, LEVEL_ORDER, TODAY, apply_filters,
                       load_employees, sidebar_filters, tenure_band, TENURE_BAND_ORDER)

st.set_page_config(page_title="Workforce Composition", page_icon="👥", layout="wide")
st.title("Workforce Composition")
st.caption("How the active workforce breaks down by department, level, location, gender, and tenure.")

emp = load_employees()
depts, levels = sidebar_filters(emp)
active = apply_filters(emp[emp["is_active"]], depts, levels)

# KPIs row
c1, c2, c3, c4 = st.columns(4)
c1.metric("Active Headcount", f"{len(active):,}")
female_pct = (active["gender"] == "Female").mean() * 100
c2.metric("% Female", f"{female_pct:.1f}%")
mgr_pct = active["level"].str.startswith("M").mean() * 100
c3.metric("% in Mgmt", f"{mgr_pct:.1f}%")
median_tenure = active["tenure_years"].median()
c4.metric("Median Tenure", f"{median_tenure:.1f} yrs")

st.divider()

# Department / level
ca, cb = st.columns(2)
with ca:
    st.markdown("##### Headcount by department")
    by_dept = active.groupby("department").size().reindex(DEPT_ORDER, fill_value=0).reset_index(name="count")
    fig = px.bar(by_dept, x="count", y="department", orientation="h",
                 color_discrete_sequence=[COLORS["primary"]])
    fig.update_layout(height=300, margin=dict(t=10, b=0), showlegend=False)
    fig.update_yaxes(title=None, categoryorder="total ascending")
    fig.update_xaxes(title=None)
    st.plotly_chart(fig, width="stretch")
with cb:
    st.markdown("##### Headcount by level")
    by_lvl = active.groupby("level").size().reindex(LEVEL_ORDER, fill_value=0).reset_index(name="count")
    fig = px.bar(by_lvl, x="level", y="count", category_orders={"level": LEVEL_ORDER},
                 color_discrete_sequence=[COLORS["primary"]])
    fig.update_layout(height=300, margin=dict(t=10, b=0), showlegend=False)
    fig.update_yaxes(title=None); fig.update_xaxes(title=None)
    st.plotly_chart(fig, width="stretch")

# Gender × department, gender × level
cc, cd = st.columns(2)
with cc:
    st.markdown("##### Gender mix by department")
    g_dept = active.groupby(["department", "gender"]).size().reset_index(name="count")
    fig = px.bar(g_dept, x="department", y="count", color="gender",
                 color_discrete_map=COLORS,
                 category_orders={"department": DEPT_ORDER, "gender": ["Female","Male","Non-binary"]})
    fig.update_layout(height=320, margin=dict(t=10, b=0), barmode="stack")
    fig.update_yaxes(title=None); fig.update_xaxes(title=None)
    st.plotly_chart(fig, width="stretch")
with cd:
    st.markdown("##### Gender mix by level")
    g_lvl = active.groupby(["level", "gender"]).size().reset_index(name="count")
    fig = px.bar(g_lvl, x="level", y="count", color="gender",
                 color_discrete_map=COLORS,
                 category_orders={"level": LEVEL_ORDER, "gender": ["Female","Male","Non-binary"]})
    fig.update_layout(height=320, margin=dict(t=10, b=0), barmode="stack")
    fig.update_yaxes(title=None); fig.update_xaxes(title=None)
    st.plotly_chart(fig, width="stretch")

# Location / tenure
ce, cf = st.columns(2)
with ce:
    st.markdown("##### Headcount by location")
    by_loc = active.groupby("location").size().reset_index(name="count").sort_values("count")
    fig = px.bar(by_loc, x="count", y="location", orientation="h",
                 color_discrete_sequence=[COLORS["primary"]])
    fig.update_layout(height=320, margin=dict(t=10, b=0), showlegend=False)
    fig.update_yaxes(title=None); fig.update_xaxes(title=None)
    st.plotly_chart(fig, width="stretch")
with cf:
    st.markdown("##### Tenure distribution")
    active_tb = active.copy()
    active_tb["band"] = active_tb["tenure_years"].apply(tenure_band)
    by_band = active_tb.groupby("band").size().reindex(TENURE_BAND_ORDER, fill_value=0).reset_index(name="count")
    fig = px.bar(by_band, x="band", y="count",
                 category_orders={"band": TENURE_BAND_ORDER},
                 color_discrete_sequence=[COLORS["primary"]])
    fig.update_layout(height=320, margin=dict(t=10, b=0), showlegend=False)
    fig.update_yaxes(title=None); fig.update_xaxes(title=None)
    st.plotly_chart(fig, width="stretch")

st.markdown("##### Employee directory (filtered)")
st.dataframe(
    active[["employee_id","full_name","gender","department","level","job_title","location","hire_date","tenure_years"]]
    .sort_values(["department","level","full_name"]),
    width="stretch", hide_index=True,
    column_config={
        "hire_date": st.column_config.DateColumn("Hire date", format="YYYY-MM-DD"),
        "tenure_years": st.column_config.NumberColumn("Tenure (yrs)", format="%.1f"),
    },
)
