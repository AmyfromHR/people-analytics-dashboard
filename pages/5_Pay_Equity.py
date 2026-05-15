"""Pay equity page — comp ratio + raw and adjusted gender pay gap."""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from lib.data import (COLORS, DEPT_ORDER, LEVEL_ORDER, apply_filters,
                       load_compensation, load_employees, sidebar_filters)

st.set_page_config(page_title="Pay Equity", page_icon="⚖️", layout="wide")
st.title("Pay Equity")
st.caption(
    "Compares men and women on base salary. **Raw gap** = simple average difference. "
    "**Adjusted gap** = average difference after accounting for level, department, and location — "
    "i.e. the gap among comparable people. A negative gap means women earn less."
)

emp = load_employees()
comp = load_compensation()
depts, levels = sidebar_filters(emp)

joined = emp[emp["is_active"]].merge(comp, on="employee_id")
joined = apply_filters(joined, depts, levels)

# KPIs
female = joined[joined["gender"] == "Female"]
male = joined[joined["gender"] == "Male"]
raw_gap_pct = (female["base_salary"].mean() - male["base_salary"].mean()) / male["base_salary"].mean() * 100

# Adjusted gap: avg female-male diff within (department, level, location) cells, weighted by cell size
cells = joined.groupby(["department","level","location","gender"])["base_salary"].mean().unstack("gender")
cells_n = joined.groupby(["department","level","location"]).size().rename("n")
if "Female" in cells.columns and "Male" in cells.columns:
    cells["diff_pct"] = (cells["Female"] - cells["Male"]) / cells["Male"] * 100
    cells_full = cells.dropna(subset=["diff_pct"]).join(cells_n)
    if cells_full["n"].sum() > 0:
        adj_gap_pct = (cells_full["diff_pct"] * cells_full["n"]).sum() / cells_full["n"].sum()
    else:
        adj_gap_pct = float("nan")
else:
    adj_gap_pct = float("nan")

below_band = (joined["comp_ratio"] < 0.95).sum()
above_band = (joined["comp_ratio"] > 1.10).sum()
median_cr = joined["comp_ratio"].median()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Raw gender pay gap", f"{raw_gap_pct:+.1f}%",
          help="Female mean salary minus Male mean salary, divided by Male mean")
c2.metric("Adjusted gap (controlling for role)", f"{adj_gap_pct:+.1f}%" if not np.isnan(adj_gap_pct) else "—",
          help="Within-cell female-male diff weighted by cell size")
c3.metric("Median comp ratio", f"{median_cr:.2f}")
c4.metric("Below band (CR < 0.95)", f"{below_band:,}")

st.divider()

# Comp ratio distribution
st.markdown("##### Comp ratio distribution")
fig = px.histogram(joined, x="comp_ratio", nbins=40,
                   color_discrete_sequence=[COLORS["primary"]])
fig.add_vline(x=0.95, line_dash="dash", line_color="gray", annotation_text="Below band 0.95", annotation_position="top left")
fig.add_vline(x=1.10, line_dash="dash", line_color="gray", annotation_text="Above band 1.10", annotation_position="top right")
fig.update_layout(height=300, margin=dict(t=10, b=0), showlegend=False, bargap=0.05)
fig.update_yaxes(title="employees"); fig.update_xaxes(title="comp ratio (salary / market midpoint)")
st.plotly_chart(fig, width="stretch")

# Gender pay gap by department: raw vs adjusted
st.markdown("##### Gender pay gap by department")
rows = []
for dept in DEPT_ORDER:
    if dept not in joined["department"].values:
        continue
    sub = joined[joined["department"] == dept]
    f = sub[sub["gender"] == "Female"]["base_salary"]
    m = sub[sub["gender"] == "Male"]["base_salary"]
    raw = (f.mean() - m.mean()) / m.mean() * 100 if len(m) and len(f) else np.nan
    # adjusted: within (level, location)
    cells_d = sub.groupby(["level","location","gender"])["base_salary"].mean().unstack("gender")
    n_d = sub.groupby(["level","location"]).size().rename("n")
    if "Female" in cells_d.columns and "Male" in cells_d.columns:
        cells_d["diff_pct"] = (cells_d["Female"] - cells_d["Male"]) / cells_d["Male"] * 100
        cells_d = cells_d.dropna(subset=["diff_pct"]).join(n_d)
        adj = (cells_d["diff_pct"] * cells_d["n"]).sum() / cells_d["n"].sum() if cells_d["n"].sum() else np.nan
    else:
        adj = np.nan
    rows.append({"department": dept, "Raw gap %": raw, "Adjusted gap %": adj,
                 "Female n": len(f), "Male n": len(m)})
gap_df = pd.DataFrame(rows)
gap_long = gap_df.melt(id_vars=["department","Female n","Male n"],
                       value_vars=["Raw gap %","Adjusted gap %"],
                       var_name="Type", value_name="Gap %")
fig = px.bar(gap_long, x="Gap %", y="department", color="Type", orientation="h", barmode="group",
             color_discrete_sequence=["#5B8FF9","#9C6ADE"],
             category_orders={"department": DEPT_ORDER})
fig.add_vline(x=0, line_color="gray")
fig.update_layout(height=380, margin=dict(t=10, b=0), legend_title=None)
fig.update_yaxes(title=None); fig.update_xaxes(title="% (negative = women paid less)")
st.plotly_chart(fig, width="stretch")

st.dataframe(
    gap_df.style.format({"Raw gap %": "{:+.1f}", "Adjusted gap %": "{:+.1f}"}),
    width="stretch", hide_index=True,
)

st.markdown("##### Mean comp ratio by gender × department")
heat = joined.pivot_table(values="comp_ratio", index="department", columns="gender", aggfunc="mean")
heat = heat.reindex(DEPT_ORDER)
fig = px.imshow(heat.round(3), text_auto=".2f", aspect="auto",
                color_continuous_scale="RdYlGn", zmin=0.85, zmax=1.10)
fig.update_layout(height=300, margin=dict(t=10, b=0))
fig.update_xaxes(title=None); fig.update_yaxes(title=None)
st.plotly_chart(fig, width="stretch")
