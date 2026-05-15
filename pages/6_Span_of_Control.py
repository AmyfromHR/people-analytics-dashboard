"""Span of control page — direct reports per manager."""
import pandas as pd
import plotly.express as px
import streamlit as st

from lib.data import (COLORS, DEPT_ORDER, LEVEL_ORDER, apply_filters,
                       load_employees, sidebar_filters)

st.set_page_config(page_title="Span of Control", page_icon="🪜", layout="wide")
st.title("Span of Control")
st.caption(
    "How many direct reports each manager has. Healthy span is typically 5–10. "
    "Below 3 may signal redundant management; above 12 may signal under-resourced managers."
)

emp = load_employees()
depts, levels = sidebar_filters(emp)
active = emp[emp["is_active"]]
active_f = apply_filters(active, depts, levels)

# Reports per manager (count any active employee with this manager_id, scoped to filters via the manager's dept)
reports = active.groupby("manager_id").size().rename("direct_reports")
mgrs = active_f[active_f["level"].isin(["M1","M2","M3","M4"])].set_index("employee_id")
mgrs = mgrs.join(reports)
mgrs["direct_reports"] = mgrs["direct_reports"].fillna(0).astype(int)

# Counts
narrow = (mgrs["direct_reports"] < 3).sum()
healthy = ((mgrs["direct_reports"] >= 3) & (mgrs["direct_reports"] <= 10)).sum()
wide = (mgrs["direct_reports"] > 10).sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Active managers", f"{len(mgrs):,}")
c2.metric("Avg span", f"{mgrs['direct_reports'].mean():.1f}")
c3.metric("Too narrow (<3)", f"{narrow:,}")
c4.metric("Too wide (>10)", f"{wide:,}")

st.divider()

# Distribution
st.markdown("##### Span distribution (all managers in scope)")
fig = px.histogram(mgrs, x="direct_reports", nbins=20,
                   color_discrete_sequence=[COLORS["primary"]])
fig.add_vrect(x0=3, x1=10, fillcolor=COLORS["Promoter"], opacity=0.10, line_width=0,
              annotation_text="healthy zone (3-10)", annotation_position="top left")
fig.update_layout(height=300, margin=dict(t=10, b=0), showlegend=False, bargap=0.05)
fig.update_xaxes(title="direct reports"); fig.update_yaxes(title="managers")
st.plotly_chart(fig, width="stretch")

# Avg span by level and dept
ca, cb = st.columns(2)
with ca:
    st.markdown("##### Avg span by manager level")
    by_lvl = mgrs.groupby("level")["direct_reports"].mean().reindex(["M1","M2","M3","M4"]).reset_index()
    fig = px.bar(by_lvl, x="level", y="direct_reports",
                 color_discrete_sequence=[COLORS["primary"]],
                 text="direct_reports")
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(height=320, margin=dict(t=10, b=0), showlegend=False)
    fig.update_yaxes(title="avg reports"); fig.update_xaxes(title=None)
    st.plotly_chart(fig, width="stretch")
with cb:
    st.markdown("##### Avg span by department")
    by_dept = mgrs.groupby("department")["direct_reports"].mean().reindex(DEPT_ORDER).reset_index()
    fig = px.bar(by_dept.sort_values("direct_reports"),
                 x="direct_reports", y="department", orientation="h",
                 color_discrete_sequence=[COLORS["primary"]],
                 text="direct_reports")
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(height=320, margin=dict(t=10, b=0), showlegend=False)
    fig.update_yaxes(title=None); fig.update_xaxes(title="avg reports")
    st.plotly_chart(fig, width="stretch")

# Outlier list
st.markdown("##### Outlier managers (sorted by span)")
mgrs_out = mgrs.drop(columns=["manager_id"]).reset_index().rename(columns={"employee_id": "manager_id"})
mgrs_out["zone"] = mgrs_out["direct_reports"].apply(
    lambda r: "Too wide" if r > 10 else "Too narrow" if r < 3 else "Healthy"
)
st.dataframe(
    mgrs_out[["manager_id","full_name","department","level","direct_reports","zone"]]
    .sort_values("direct_reports", ascending=False),
    width="stretch", hide_index=True,
)
