"""Attrition page — voluntary, involuntary, regrettable."""
import pandas as pd
import plotly.express as px
import streamlit as st

from lib.data import (COLORS, DEPT_ORDER, LEVEL_ORDER, TODAY, apply_filters,
                       load_employees, load_terminations, sidebar_filters,
                       tenure_band, TENURE_BAND_ORDER)

st.set_page_config(page_title="Attrition", page_icon="📉", layout="wide")
st.title("Attrition")
st.caption("Voluntary, involuntary, and regrettable attrition over the last 3 years.")

emp = load_employees()
terms = load_terminations()
depts, levels = sidebar_filters(emp)

terms_full = terms.merge(emp[["employee_id","gender","hire_date"]], on="employee_id")
terms_f = apply_filters(terms_full, depts, levels)

ONE_YEAR_AGO = TODAY - pd.Timedelta(days=365)
recent = terms_f[terms_f["termination_date"] >= ONE_YEAR_AGO]
active_f = apply_filters(emp[emp["is_active"]], depts, levels)
one_yr_ago_active = apply_filters(
    emp[(emp["hire_date"] <= ONE_YEAR_AGO)
        & (emp["termination_date"].isna() | (emp["termination_date"] > ONE_YEAR_AGO))],
    depts, levels,
)
denom = max(1, (len(active_f) + len(one_yr_ago_active)) / 2)

vol_count = (recent["termination_type"] == "Voluntary").sum()
invol_count = (recent["termination_type"] == "Involuntary").sum()
reg_count = recent["is_regrettable"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Attrition (12 mo)", f"{len(recent):,}", f"{len(recent)/denom*100:.1f}% rate")
c2.metric("Voluntary", f"{vol_count:,}", f"{vol_count/denom*100:.1f}% rate")
c3.metric("Involuntary", f"{invol_count:,}", f"{invol_count/denom*100:.1f}% rate")
c4.metric("Regrettable", f"{reg_count:,}", f"{reg_count/max(1,vol_count)*100:.0f}% of voluntary")

st.divider()

# Trend
st.markdown("##### Monthly trend (last 36 months)")
terms_f_m = terms_f.copy()
terms_f_m["month"] = terms_f_m["termination_date"].dt.to_period("M").dt.to_timestamp()
trend = terms_f_m.groupby(["month","termination_type"]).size().reset_index(name="count")
fig = px.bar(trend, x="month", y="count", color="termination_type",
             color_discrete_map=COLORS,
             category_orders={"termination_type": ["Voluntary","Involuntary"]})
fig.update_layout(height=320, margin=dict(t=10, b=0), barmode="stack", legend_title=None)
fig.update_yaxes(title=None); fig.update_xaxes(title=None)
st.plotly_chart(fig, width="stretch")

# Dept and level cuts (last 12 mo)
ca, cb = st.columns(2)
with ca:
    st.markdown("##### Attrition rate by department (12 mo)")
    by_dept = (recent.groupby("department").size()
               .reindex(DEPT_ORDER, fill_value=0).reset_index(name="leavers"))
    hc_dept = active_f.groupby("department").size().reindex(DEPT_ORDER, fill_value=0)
    by_dept["rate"] = (by_dept["leavers"] / hc_dept.values * 100).round(1)
    fig = px.bar(by_dept.sort_values("rate"), x="rate", y="department", orientation="h",
                 color_discrete_sequence=[COLORS["Voluntary"]],
                 text="rate")
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(height=320, margin=dict(t=10, b=0), showlegend=False)
    fig.update_yaxes(title=None); fig.update_xaxes(title="%")
    st.plotly_chart(fig, width="stretch")

with cb:
    st.markdown("##### Voluntary vs involuntary by department (12 mo)")
    type_dept = recent.groupby(["department","termination_type"]).size().reset_index(name="count")
    fig = px.bar(type_dept, x="department", y="count", color="termination_type",
                 color_discrete_map=COLORS,
                 category_orders={"department": DEPT_ORDER, "termination_type": ["Voluntary","Involuntary"]})
    fig.update_layout(height=320, margin=dict(t=10, b=0), barmode="stack", legend_title=None)
    fig.update_yaxes(title=None); fig.update_xaxes(title=None)
    st.plotly_chart(fig, width="stretch")

# Reasons + tenure at term
cc, cd = st.columns(2)
with cc:
    st.markdown("##### Top exit reasons (12 mo)")
    reasons = recent.groupby(["termination_type","reason"]).size().reset_index(name="count")
    reasons = reasons.sort_values("count", ascending=True).tail(12)
    fig = px.bar(reasons, x="count", y="reason", color="termination_type", orientation="h",
                 color_discrete_map=COLORS)
    fig.update_layout(height=320, margin=dict(t=10, b=0), legend_title=None)
    fig.update_yaxes(title=None); fig.update_xaxes(title=None)
    st.plotly_chart(fig, width="stretch")

with cd:
    st.markdown("##### Attrition by tenure band (12 mo)")
    rec_tb = recent.copy()
    rec_tb["band"] = rec_tb["tenure_at_term_years"].apply(tenure_band)
    by_band = (rec_tb.groupby(["band","termination_type"]).size().reset_index(name="count"))
    fig = px.bar(by_band, x="band", y="count", color="termination_type",
                 color_discrete_map=COLORS,
                 category_orders={"band": TENURE_BAND_ORDER, "termination_type": ["Voluntary","Involuntary"]})
    fig.update_layout(height=320, margin=dict(t=10, b=0), barmode="stack", legend_title=None)
    fig.update_yaxes(title=None); fig.update_xaxes(title=None)
    st.plotly_chart(fig, width="stretch")

st.markdown("##### Recent leavers (last 12 months)")
detail = recent[["employee_id","full_name","department","level","termination_date","termination_type","is_regrettable","reason","tenure_at_term_years"]] \
    if False else None
detail_cols = ["employee_id","department","level","termination_date","termination_type","is_regrettable","reason","tenure_at_term_years"]
# include name from emp join
recent_with_name = recent.merge(emp[["employee_id","full_name"]], on="employee_id")
st.dataframe(
    recent_with_name[["employee_id","full_name"] + detail_cols[1:]].sort_values("termination_date", ascending=False),
    width="stretch", hide_index=True,
    column_config={
        "termination_date": st.column_config.DateColumn("Term date", format="YYYY-MM-DD"),
        "is_regrettable": st.column_config.CheckboxColumn("Regrettable"),
        "tenure_at_term_years": st.column_config.NumberColumn("Tenure (yrs)", format="%.1f"),
    },
)
