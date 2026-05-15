"""Flight risk page — scored list with drivers."""
import pandas as pd
import plotly.express as px
import streamlit as st

from lib.data import (COLORS, DEPT_ORDER, LEVEL_ORDER, apply_filters,
                       load_compensation, load_employees, load_flight_risk,
                       sidebar_filters)

st.set_page_config(page_title="Flight Risk", page_icon="🚨", layout="wide")
st.title("Flight Risk")
st.caption(
    "A composite score (0–100) of how likely a current employee is to leave in the next 12 months. "
    "Drivers: tenure (peak risk 2–4 yrs), months since promotion, comp ratio vs market, recent eNPS, "
    "performance trend, and whether they've had a manager change. **This is illustrative — not a hiring decision tool.**"
)

emp = load_employees()
risk = load_flight_risk()
comp = load_compensation()
depts, levels = sidebar_filters(emp)
active_f = apply_filters(emp[emp["is_active"]], depts, levels)

risk_f = risk.merge(active_f[["employee_id","full_name","department","level","gender","location","job_title"]], on="employee_id")
risk_f = risk_f.merge(comp[["employee_id","base_salary"]], on="employee_id")

bands = ["Critical","High","Medium","Low"]
band_counts = risk_f["flight_risk_band"].value_counts().reindex(bands, fill_value=0)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Critical", f"{band_counts['Critical']:,}",
          f"{band_counts['Critical']/max(1,len(risk_f))*100:.0f}% of HC")
c2.metric("High", f"{band_counts['High']:,}",
          f"{band_counts['High']/max(1,len(risk_f))*100:.0f}% of HC")
c3.metric("Medium", f"{band_counts['Medium']:,}",
          f"{band_counts['Medium']/max(1,len(risk_f))*100:.0f}% of HC")
c4.metric("Low", f"{band_counts['Low']:,}",
          f"{band_counts['Low']/max(1,len(risk_f))*100:.0f}% of HC")

st.divider()

# Risk band distribution
ca, cb = st.columns(2)
with ca:
    st.markdown("##### Risk band distribution")
    band_df = band_counts.reset_index()
    band_df.columns = ["band","count"]
    fig = px.bar(band_df, x="band", y="count",
                 category_orders={"band": bands},
                 color="band", color_discrete_map=COLORS,
                 text="count")
    fig.update_traces(textposition="outside")
    fig.update_layout(height=300, margin=dict(t=10, b=0), showlegend=False)
    fig.update_yaxes(title=None); fig.update_xaxes(title=None)
    st.plotly_chart(fig, width="stretch")

with cb:
    st.markdown("##### High + Critical by department")
    high = risk_f[risk_f["flight_risk_band"].isin(["Critical","High"])]
    by_dept = high.groupby("department").size().reindex(DEPT_ORDER, fill_value=0).reset_index(name="count")
    fig = px.bar(by_dept.sort_values("count"), x="count", y="department", orientation="h",
                 color_discrete_sequence=[COLORS["High"]], text="count")
    fig.update_traces(textposition="outside")
    fig.update_layout(height=300, margin=dict(t=10, b=0), showlegend=False)
    fig.update_yaxes(title=None); fig.update_xaxes(title=None)
    st.plotly_chart(fig, width="stretch")

# Driver prevalence among high+critical
st.markdown("##### Most common drivers among High + Critical risk employees")
high = risk_f[risk_f["flight_risk_band"].isin(["Critical","High"])]
n = max(1, len(high))
drivers = pd.DataFrame({
    "Driver": [
        "Tenure 2-4 yrs (peak risk band)",
        "24+ months since promotion",
        "Below-market comp (CR < 0.95)",
        "Recent eNPS Detractor (≤6)",
        "Declining performance trend",
        "Manager change in last 12 months",
    ],
    "Share": [
        ((high["tenure_years"] >= 2) & (high["tenure_years"] <= 4)).mean() * 100,
        (high["months_since_promotion"] >= 24).mean() * 100,
        (high["comp_ratio"] < 0.95).mean() * 100,
        (high["last_enps_score"] <= 6).mean() * 100,
        (high["perf_trend"] == "Declining").mean() * 100,
        (high["manager_change_12mo"]).mean() * 100,
    ],
})
drivers = drivers.sort_values("Share")
fig = px.bar(drivers, x="Share", y="Driver", orientation="h",
             color_discrete_sequence=[COLORS["High"]], text="Share")
fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
fig.update_layout(height=320, margin=dict(t=10, b=0), showlegend=False)
fig.update_yaxes(title=None); fig.update_xaxes(title="% of high/critical risk")
st.plotly_chart(fig, width="stretch")

# Sortable table
st.markdown("##### Employees by risk score (sortable, exportable)")
table = risk_f[[
    "employee_id","full_name","department","level","job_title",
    "flight_risk_score","flight_risk_band","tenure_years",
    "months_since_promotion","comp_ratio","last_enps_score","perf_trend",
    "manager_change_12mo","base_salary",
]].sort_values("flight_risk_score", ascending=False)

st.dataframe(
    table, width="stretch", hide_index=True,
    column_config={
        "flight_risk_score": st.column_config.ProgressColumn(
            "Risk score", format="%.0f", min_value=0, max_value=100,
        ),
        "comp_ratio": st.column_config.NumberColumn("Comp ratio", format="%.2f"),
        "tenure_years": st.column_config.NumberColumn("Tenure (yrs)", format="%.1f"),
        "last_enps_score": st.column_config.NumberColumn("Last eNPS", format="%.0f"),
        "base_salary": st.column_config.NumberColumn("Salary", format="$%d"),
        "manager_change_12mo": st.column_config.CheckboxColumn("Mgr change 12mo"),
    },
)
