"""eNPS page — score by tenure, department, and trend."""
import pandas as pd
import plotly.express as px
import streamlit as st

from lib.data import (COLORS, DEPT_ORDER, TODAY, apply_filters,
                       load_employees, load_enps, sidebar_filters,
                       tenure_band, TENURE_BAND_ORDER)

st.set_page_config(page_title="eNPS", page_icon="🟢", layout="wide")
st.title("Employee Net Promoter Score (eNPS)")
st.caption(
    "Quarterly survey. eNPS = % Promoters (9–10) − % Detractors (0–6). "
    "Above 0 is good; above +20 is healthy; above +40 is exceptional."
)

emp = load_employees()
enps = load_enps()
depts, levels = sidebar_filters(emp)

emp_meta = emp[["employee_id","department","level","gender","hire_date"]]
enps_full = enps.merge(emp_meta, on="employee_id")
enps_f = apply_filters(enps_full, depts, levels)

latest_date = enps_f["survey_date"].max()
latest = enps_f[enps_f["survey_date"] == latest_date]

def score(df):
    if len(df) == 0:
        return 0.0
    return (df["category"].eq("Promoter").sum() - df["category"].eq("Detractor").sum()) / len(df) * 100

overall = score(latest)
prev_quarter = sorted(enps_f["survey_date"].unique())[-2] if len(enps_f["survey_date"].unique()) > 1 else latest_date
prev = score(enps_f[enps_f["survey_date"] == prev_quarter])
delta = overall - prev

c1, c2, c3, c4 = st.columns(4)
c1.metric("eNPS (latest)", f"{overall:+.0f}", f"{delta:+.0f} vs prev qtr")
c2.metric("Responses (latest)", f"{len(latest):,}")
c3.metric("Promoters", f"{(latest['category']=='Promoter').sum()}",
          f"{(latest['category']=='Promoter').mean()*100:.0f}%")
c4.metric("Detractors", f"{(latest['category']=='Detractor').sum()}",
          f"{(latest['category']=='Detractor').mean()*100:.0f}%", delta_color="inverse")

st.divider()

# Trend overall
st.markdown("##### eNPS trend by quarter")
qtr = enps_f.groupby("survey_date").apply(
    lambda g: pd.Series({"eNPS": score(g), "responses": len(g)}),
    include_groups=False,
).reset_index()
fig = px.line(qtr, x="survey_date", y="eNPS", markers=True)
fig.update_traces(line=dict(color=COLORS["primary"], width=3))
fig.add_hline(y=0, line_dash="dot", line_color="gray")
fig.update_layout(height=300, margin=dict(t=10, b=0))
fig.update_yaxes(title=None); fig.update_xaxes(title=None)
st.plotly_chart(fig, width="stretch")

# By dept and by tenure band
ca, cb = st.columns(2)
with ca:
    st.markdown("##### eNPS by department (latest)")
    by_dept = latest.groupby("department").apply(
        lambda g: pd.Series({"eNPS": score(g), "n": len(g)}),
        include_groups=False,
    ).reset_index()
    by_dept = by_dept.sort_values("eNPS")
    fig = px.bar(by_dept, x="eNPS", y="department", orientation="h",
                 color="eNPS", color_continuous_scale=["#D7263D","#F6BD16","#2EC27E"],
                 range_color=[-60, 60], text="eNPS")
    fig.update_traces(texttemplate="%{text:+.0f}", textposition="outside")
    fig.update_layout(height=320, margin=dict(t=10, b=0), coloraxis_showscale=False)
    fig.update_yaxes(title=None); fig.update_xaxes(title=None)
    st.plotly_chart(fig, width="stretch")

with cb:
    st.markdown("##### eNPS by tenure band (latest)")
    latest_tb = latest.copy()
    latest_tb["tenure_yrs"] = (latest_tb["survey_date"] - latest_tb["hire_date"]).dt.days / 365.25
    latest_tb["band"] = latest_tb["tenure_yrs"].apply(tenure_band)
    by_band = latest_tb.groupby("band").apply(
        lambda g: pd.Series({"eNPS": score(g), "n": len(g)}),
        include_groups=False,
    ).reset_index()
    by_band["band"] = pd.Categorical(by_band["band"], categories=TENURE_BAND_ORDER, ordered=True)
    by_band = by_band.sort_values("band")
    fig = px.bar(by_band, x="band", y="eNPS",
                 category_orders={"band": TENURE_BAND_ORDER},
                 color="eNPS", color_continuous_scale=["#D7263D","#F6BD16","#2EC27E"],
                 range_color=[-60, 60], text="eNPS")
    fig.update_traces(texttemplate="%{text:+.0f}", textposition="outside")
    fig.update_layout(height=320, margin=dict(t=10, b=0), coloraxis_showscale=False)
    fig.update_yaxes(title=None); fig.update_xaxes(title=None)
    st.plotly_chart(fig, width="stretch")

# Category mix latest
st.markdown("##### Promoter / Passive / Detractor mix by department (latest)")
cat_mix = latest.groupby(["department","category"]).size().reset_index(name="count")
totals = cat_mix.groupby("department")["count"].transform("sum")
cat_mix["pct"] = cat_mix["count"] / totals * 100
fig = px.bar(cat_mix, x="pct", y="department", color="category", orientation="h",
             color_discrete_map=COLORS,
             category_orders={"department": DEPT_ORDER, "category": ["Detractor","Passive","Promoter"]})
fig.update_layout(height=320, margin=dict(t=10, b=0), barmode="stack", legend_title=None)
fig.update_yaxes(title=None); fig.update_xaxes(title="% of respondents")
st.plotly_chart(fig, width="stretch")
