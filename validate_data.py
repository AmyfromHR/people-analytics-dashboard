"""Quick validation summary for the generated data."""
import pandas as pd
from pathlib import Path

DATA = Path("data")
emp   = pd.read_csv(DATA / "employees.csv", parse_dates=["hire_date", "termination_date", "birth_date"])
comp  = pd.read_csv(DATA / "compensation.csv")
perf  = pd.read_csv(DATA / "performance.csv")
terms = pd.read_csv(DATA / "terminations.csv", parse_dates=["termination_date"])
hires = pd.read_csv(DATA / "hires.csv", parse_dates=["requisition_open_date", "offer_accepted_date", "start_date"])
enps  = pd.read_csv(DATA / "enps_surveys.csv", parse_dates=["survey_date"])
risk  = pd.read_csv(DATA / "flight_risk.csv")

pd.options.display.float_format = "{:.2f}".format
pd.options.display.width = 140

print("=" * 70)
print("FILE SIZES")
print("=" * 70)
for name, df in [("employees", emp), ("compensation", comp), ("performance", perf),
                 ("terminations", terms), ("hires", hires), ("enps_surveys", enps),
                 ("flight_risk", risk)]:
    print(f"  {name:18s} {len(df):>6} rows  |  {len(df.columns)} cols")

print("\n" + "=" * 70)
print("HEADCOUNT BY DEPARTMENT (active)")
print("=" * 70)
print(emp[emp["is_active"]].groupby("department").size().to_string())
print(f"  TOTAL active: {emp['is_active'].sum()}")

print("\n" + "=" * 70)
print("HEADCOUNT BY LEVEL (active)")
print("=" * 70)
lvl_order = ["IC1","IC2","IC3","IC4","IC5","M1","M2","M3","M4"]
lvl = emp[emp["is_active"]].groupby("level").size().reindex(lvl_order)
print(lvl.to_string())

print("\n" + "=" * 70)
print("GENDER MIX (active)")
print("=" * 70)
print(emp[emp["is_active"]].groupby("gender").size().to_string())

print("\n" + "=" * 70)
print("LOCATION DISTRIBUTION (active)")
print("=" * 70)
print(emp[emp["is_active"]].groupby("location").size().sort_values(ascending=False).to_string())

print("\n" + "=" * 70)
print("ATTRITION — last 12 months by department (annualized rate)")
print("=" * 70)
recent_terms = terms[terms["termination_date"] >= pd.Timestamp("2025-05-11")]
dept_term = recent_terms.groupby(["department", "termination_type"]).size().unstack(fill_value=0)
hc_now = emp[emp["is_active"]].groupby("department").size()
dept_term["Total"] = dept_term.sum(axis=1)
dept_term["Headcount"] = hc_now
dept_term["Annual %"] = (dept_term["Total"] / dept_term["Headcount"] * 100).round(1)
print(dept_term.to_string())
print(f"\nRegrettable share of voluntary (last 12 mo): "
      f"{(recent_terms[recent_terms['termination_type']=='Voluntary']['is_regrettable'].mean()*100):.1f}%")

print("\n" + "=" * 70)
print("PAY EQUITY — raw mean salary by gender, by department")
print("=" * 70)
joined = emp[emp["is_active"]].merge(comp, on="employee_id")
pivot = joined.pivot_table(values="base_salary", index="department", columns="gender", aggfunc="mean")
pivot["Gap (F vs M)"] = ((pivot["Female"] - pivot["Male"]) / pivot["Male"] * 100).round(2)
print(pivot.to_string())

print("\n" + "=" * 70)
print("eNPS BY TENURE BAND (most recent survey — Q1 2026)")
print("=" * 70)
latest = enps[enps["survey_date"] == enps["survey_date"].max()].copy()
latest = latest.merge(emp[["employee_id", "hire_date"]], on="employee_id")
latest["tenure_years"] = (latest["survey_date"] - latest["hire_date"]).dt.days / 365.25
def band(t):
    if t < 1: return "0-1 yr"
    if t < 2: return "1-2 yr"
    if t < 4: return "2-4 yr"
    if t < 6: return "4-6 yr"   # the dip band lives here
    if t < 10: return "6-10 yr"
    return "10+ yr"
latest["band"] = latest["tenure_years"].apply(band)
g = latest.groupby("band")["category"].value_counts().unstack(fill_value=0)
g["eNPS"] = ((g.get("Promoter",0) - g.get("Detractor",0)) / g.sum(axis=1) * 100).round(1)
print(g.reindex(["0-1 yr","1-2 yr","2-4 yr","4-6 yr","6-10 yr","10+ yr"]).to_string())

print("\n" + "=" * 70)
print("TIME-TO-HIRE — average days by department (3-yr window)")
print("=" * 70)
print(hires.groupby("department")["time_to_hire_days"].agg(["mean", "median", "count"]).round(1).to_string())

print("\n" + "=" * 70)
print("SPAN OF CONTROL — direct reports per active manager (top/bottom 5)")
print("=" * 70)
rep_counts = emp[emp["is_active"]].groupby("manager_id").size().rename("direct_reports")
mgrs = emp[emp["is_active"] & emp["level"].isin(["M1","M2","M3","M4"])].set_index("employee_id")
mgrs = mgrs.join(rep_counts).fillna({"direct_reports": 0})
mgrs["direct_reports"] = mgrs["direct_reports"].astype(int)
print("Top 5 widest spans:")
print(mgrs.sort_values("direct_reports", ascending=False)[["full_name","department","level","direct_reports"]].head(5).to_string())
print("\nBottom 5 narrowest spans (active managers with <2 reports):")
print(mgrs[mgrs["direct_reports"] < 2][["full_name","department","level","direct_reports"]].head(5).to_string())

print("\n" + "=" * 70)
print("FLIGHT RISK — distribution by band")
print("=" * 70)
print(risk["flight_risk_band"].value_counts().reindex(["Critical","High","Medium","Low"]).to_string())

print("\n" + "=" * 70)
print("SAMPLE ROWS — employees.csv (5 rows)")
print("=" * 70)
print(emp.sample(5, random_state=1)[["employee_id","full_name","gender","department","level","job_title","location","hire_date","is_active","tenure_years"]].to_string(index=False))

print("\n" + "=" * 70)
print("SAMPLE ROWS — compensation.csv (5 rows)")
print("=" * 70)
print(comp.sample(5, random_state=1).to_string(index=False))

print("\n" + "=" * 70)
print("SAMPLE ROWS — flight_risk.csv (top 5 highest-risk)")
print("=" * 70)
top_risk = risk.sort_values("flight_risk_score", ascending=False).head(5)
top_risk = top_risk.merge(emp[["employee_id","full_name","department","level"]], on="employee_id")
print(top_risk[["employee_id","full_name","department","level","flight_risk_score","flight_risk_band","perf_trend","last_enps_score"]].to_string(index=False))
