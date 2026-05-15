"""Meridian Analytics — synthetic HR data generator.

Generates 7 CSV files in ./data/ used by the People Analytics Dashboard.
Run from project root:  python data_generator.py
"""

import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

fake = Faker("en_US")
Faker.seed(SEED)

TODAY = date(2026, 5, 11)
HISTORY_START = date(2023, 5, 11)
EARLIEST_HIRE = date(2008, 1, 1)

OUT_DIR = Path("data")
OUT_DIR.mkdir(exist_ok=True)

DEPARTMENTS = {
    "Consulting":       {"size": 360, "salary_mult": 1.00, "tt_hire_mean": 45},
    "Technology":       {"size": 180, "salary_mult": 1.18, "tt_hire_mean": 70},
    "Sales":            {"size": 130, "salary_mult": 1.05, "tt_hire_mean": 35},
    "Finance":          {"size": 90,  "salary_mult": 1.05, "tt_hire_mean": 50},
    "Marketing":        {"size": 80,  "salary_mult": 0.95, "tt_hire_mean": 45},
    "People & Culture": {"size": 60,  "salary_mult": 0.90, "tt_hire_mean": 40},
}

CITIES = {
    "New York":      {"weight": 0.30, "col_mult": 1.10},
    "Chicago":       {"weight": 0.18, "col_mult": 1.00},
    "San Francisco": {"weight": 0.15, "col_mult": 1.18},
    "Boston":        {"weight": 0.12, "col_mult": 1.05},
    "Atlanta":       {"weight": 0.13, "col_mult": 0.92},
    "Austin":        {"weight": 0.12, "col_mult": 0.95},
}

LEVEL_MIX = {
    "IC1": 0.14, "IC2": 0.20, "IC3": 0.22, "IC4": 0.13, "IC5": 0.07,
    "M1":  0.13, "M2":  0.07, "M3":  0.03, "M4":  0.01,
}
LEVEL_ORDER = ["IC1", "IC2", "IC3", "IC4", "IC5", "M1", "M2", "M3", "M4"]
MANAGER_LEVELS = ["M1", "M2", "M3", "M4"]

SALARY_BAND = {
    "IC1": (55_000,  75_000),
    "IC2": (72_000,  98_000),
    "IC3": (95_000,  130_000),
    "IC4": (125_000, 170_000),
    "IC5": (160_000, 220_000),
    "M1":  (130_000, 175_000),
    "M2":  (165_000, 215_000),
    "M3":  (210_000, 285_000),
    "M4":  (290_000, 410_000),
}

JOB_TITLES = {
    "Consulting": {
        "IC1": "Analyst", "IC2": "Senior Analyst", "IC3": "Consultant",
        "IC4": "Senior Consultant", "IC5": "Principal Consultant",
        "M1": "Engagement Manager", "M2": "Senior Engagement Manager",
        "M3": "Director of Consulting", "M4": "VP, Consulting",
    },
    "Technology": {
        "IC1": "Junior Engineer", "IC2": "Software Engineer", "IC3": "Senior Engineer",
        "IC4": "Staff Engineer", "IC5": "Principal Engineer",
        "M1": "Engineering Manager", "M2": "Senior Engineering Manager",
        "M3": "Director of Engineering", "M4": "VP, Technology",
    },
    "Sales": {
        "IC1": "Sales Development Rep", "IC2": "Account Executive", "IC3": "Senior Account Executive",
        "IC4": "Strategic Account Executive", "IC5": "Principal Account Executive",
        "M1": "Sales Manager", "M2": "Senior Sales Manager",
        "M3": "Director of Sales", "M4": "VP, Sales",
    },
    "Finance": {
        "IC1": "Financial Analyst", "IC2": "Senior Financial Analyst", "IC3": "Finance Lead",
        "IC4": "Senior Finance Lead", "IC5": "Principal Finance Lead",
        "M1": "Finance Manager", "M2": "Senior Finance Manager",
        "M3": "Director of Finance", "M4": "VP, Finance",
    },
    "Marketing": {
        "IC1": "Marketing Coordinator", "IC2": "Marketing Specialist", "IC3": "Senior Marketing Specialist",
        "IC4": "Marketing Lead", "IC5": "Principal Marketing Lead",
        "M1": "Marketing Manager", "M2": "Senior Marketing Manager",
        "M3": "Director of Marketing", "M4": "VP, Marketing",
    },
    "People & Culture": {
        "IC1": "People Coordinator", "IC2": "People Specialist", "IC3": "Senior People Specialist",
        "IC4": "People Partner", "IC5": "Senior People Partner",
        "M1": "People Manager", "M2": "Senior People Manager",
        "M3": "Director of People & Culture", "M4": "VP, People & Culture",
    },
}

DEPT_ATTRITION_RATE = {
    "Consulting":       0.18,
    "Technology":       0.13,
    "Sales":            0.20,
    "Finance":          0.10,
    "Marketing":        0.19,
    "People & Culture": 0.09,
}

VOLUNTARY_SHARE = 0.78
VOLUNTARY_REASONS = [
    ("Better opportunity", 0.32), ("Compensation", 0.18), ("Career growth", 0.18),
    ("Manager / team", 0.10), ("Work-life balance", 0.10),
    ("Relocation", 0.06), ("Personal", 0.06),
]
INVOLUNTARY_REASONS = [
    ("Performance", 0.55), ("Restructuring", 0.35), ("Misconduct", 0.10),
]

LEVEL_MGR_TARGET = {
    "IC1": ["M1", "M2"], "IC2": ["M1", "M2"], "IC3": ["M1", "M2"],
    "IC4": ["M2", "M3"], "IC5": ["M2", "M3"],
    "M1":  ["M2", "M3"], "M2":  ["M3", "M4"], "M3":  ["M4"], "M4":  [],
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def weighted_choice(options):
    values, weights = zip(*options)
    return random.choices(values, weights=weights, k=1)[0]


def random_date_between(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(0, delta)))


def pick_city():
    cities, weights = zip(*[(c, info["weight"]) for c, info in CITIES.items()])
    return random.choices(cities, weights=weights, k=1)[0]


def pick_gender():
    return random.choices(["Female", "Male", "Non-binary"], weights=[0.52, 0.47, 0.01], k=1)[0]


def pick_first_name(gender):
    if gender == "Female":
        return fake.first_name_female()
    if gender == "Male":
        return fake.first_name_male()
    return fake.first_name()


def days_to_date(td_days: float, anchor: date) -> date:
    return anchor - timedelta(days=int(td_days))


# ---------------------------------------------------------------------------
# 1. Employees (active + termed)
# ---------------------------------------------------------------------------
def build_employees():
    rows = []
    next_id = 10001

    # Active
    for dept, info in DEPARTMENTS.items():
        for level, frac in LEVEL_MIX.items():
            count = max(1, round(info["size"] * frac)) if level == "M4" else round(info["size"] * frac)
            count = max(0, count)
            for _ in range(count):
                gender = pick_gender()
                first = pick_first_name(gender)
                last = fake.last_name()
                tenure_years = float(np.clip(np.random.lognormal(0.9, 0.7), 0.05, 18))
                hire_date = days_to_date(tenure_years * 365, TODAY)
                if hire_date < EARLIEST_HIRE:
                    hire_date = EARLIEST_HIRE
                age_at_hire = random.randint(22, 55)
                birth_date = days_to_date(age_at_hire * 365, hire_date)
                rows.append({
                    "employee_id": f"E{next_id:05d}",
                    "first_name": first, "last_name": last,
                    "full_name": f"{first} {last}",
                    "gender": gender, "department": dept, "level": level,
                    "job_title": JOB_TITLES[dept][level],
                    "hire_date": hire_date, "termination_date": None,
                    "is_active": True, "manager_id": None,
                    "location": pick_city(), "birth_date": birth_date,
                })
                next_id += 1

    # Terminated (3 years)
    termed_level_mix = [
        ("IC1", 0.16), ("IC2", 0.22), ("IC3", 0.22), ("IC4", 0.12), ("IC5", 0.06),
        ("M1", 0.12), ("M2", 0.06), ("M3", 0.03), ("M4", 0.01),
    ]
    for dept, info in DEPARTMENTS.items():
        total_termed = int(info["size"] * DEPT_ATTRITION_RATE[dept]) * 3
        for _ in range(total_termed):
            gender = pick_gender()
            first = pick_first_name(gender)
            last = fake.last_name()
            level = weighted_choice(termed_level_mix)
            term_date = random_date_between(HISTORY_START, TODAY)
            tenure_at_term = float(np.clip(np.random.lognormal(0.7, 0.8), 0.2, 15))
            hire_date = days_to_date(tenure_at_term * 365, term_date)
            if hire_date < EARLIEST_HIRE:
                hire_date = EARLIEST_HIRE
            age_at_hire = random.randint(22, 55)
            birth_date = days_to_date(age_at_hire * 365, hire_date)
            rows.append({
                "employee_id": f"E{next_id:05d}",
                "first_name": first, "last_name": last,
                "full_name": f"{first} {last}",
                "gender": gender, "department": dept, "level": level,
                "job_title": JOB_TITLES[dept][level],
                "hire_date": hire_date, "termination_date": term_date,
                "is_active": False, "manager_id": None,
                "location": pick_city(), "birth_date": birth_date,
            })
            next_id += 1

    df = pd.DataFrame(rows)
    df["tenure_years"] = df.apply(
        lambda r: round(((r["termination_date"] if pd.notna(r["termination_date"]) else TODAY) - r["hire_date"]).days / 365.25, 2),
        axis=1,
    )
    return df


# ---------------------------------------------------------------------------
# 2. Manager hierarchy
# ---------------------------------------------------------------------------
def assign_managers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    active_mask = df["is_active"]
    for dept in DEPARTMENTS:
        dept_active = df[active_mask & (df["department"] == dept)]
        for idx, row in dept_active.iterrows():
            target_levels = LEVEL_MGR_TARGET[row["level"]]
            if not target_levels:
                continue
            cands = dept_active[
                dept_active["level"].isin(target_levels)
                & (dept_active["employee_id"] != row["employee_id"])
            ]
            if len(cands) == 0:
                cands = dept_active[
                    dept_active["level"].isin(MANAGER_LEVELS)
                    & (dept_active["employee_id"] != row["employee_id"])
                ]
            if len(cands) == 0:
                continue
            df.at[idx, "manager_id"] = cands.sample(1).iloc[0]["employee_id"]

    # Inject one over-spanned manager (M2 in Consulting → many IC3s)
    m2_consulting = df[(df["department"] == "Consulting") & (df["level"] == "M2") & active_mask]
    if len(m2_consulting) > 0:
        big_mgr = m2_consulting.iloc[0]["employee_id"]
        ic_pool = df[(df["department"] == "Consulting") & (df["level"] == "IC3") & active_mask].head(18)
        df.loc[df["employee_id"].isin(ic_pool["employee_id"]), "manager_id"] = big_mgr

    # Inject one under-spanned manager (M1 in Marketing → only 1 report)
    m1_marketing = df[(df["department"] == "Marketing") & (df["level"] == "M1") & active_mask]
    if len(m1_marketing) > 0:
        narrow_mgr = m1_marketing.iloc[0]["employee_id"]
        their_reports = df[df["manager_id"] == narrow_mgr].index.tolist()
        backup_mgrs = df[
            (df["department"] == "Marketing")
            & df["level"].isin(["M1", "M2"]) & active_mask
            & (df["employee_id"] != narrow_mgr)
        ]
        if len(backup_mgrs) > 0:
            for idx in their_reports[1:]:
                df.at[idx, "manager_id"] = backup_mgrs.sample(1).iloc[0]["employee_id"]

    return df


# ---------------------------------------------------------------------------
# 3. Compensation
# ---------------------------------------------------------------------------
def build_compensation(emp_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, e in emp_df.iterrows():
        low, high = SALARY_BAND[e["level"]]
        dept_mult = DEPARTMENTS[e["department"]]["salary_mult"]
        col_mult = CITIES[e["location"]]["col_mult"]
        midpoint = (low + high) / 2 * dept_mult * col_mult
        salary = midpoint * np.random.normal(1.0, 0.10)

        # Embedded gender pay gaps
        if e["department"] in ("Sales", "Technology") and e["gender"] == "Female":
            salary *= np.random.uniform(0.91, 0.97)
        if (e["department"] == "Consulting" and e["gender"] == "Female"
                and e["level"] in ("IC4", "IC5", "M2", "M3")):
            salary *= np.random.uniform(0.94, 0.99)

        salary = max(low * dept_mult * col_mult * 0.85, salary)
        salary = round(salary / 500) * 500
        midpoint = round(midpoint / 500) * 500
        comp_ratio = round(salary / midpoint, 3)

        if e["is_active"]:
            months_since = random.randint(2, 28)
            last_inc_date = TODAY - timedelta(days=months_since * 30)
            last_inc_pct = round(np.random.uniform(0.02, 0.07), 3)
        else:
            last_inc_date = None
            last_inc_pct = None

        rows.append({
            "employee_id": e["employee_id"],
            "base_salary": int(salary),
            "market_midpoint": int(midpoint),
            "comp_ratio": comp_ratio,
            "pay_band_low": int(round(low * dept_mult * col_mult / 500) * 500),
            "pay_band_high": int(round(high * dept_mult * col_mult / 500) * 500),
            "last_increase_date": last_inc_date,
            "last_increase_pct": last_inc_pct,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4. Performance (annual)
# ---------------------------------------------------------------------------
def build_performance(emp_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    rating_choices = [1, 2, 3, 4, 5]
    rating_weights = [0.03, 0.10, 0.45, 0.32, 0.10]
    for year in (2023, 2024, 2025):
        anchor = date(year, 12, 1)
        for _, e in emp_df.iterrows():
            if e["hire_date"] > anchor:
                continue
            if pd.notna(e["termination_date"]) and e["termination_date"] < anchor:
                continue
            rating = random.choices(rating_choices, weights=rating_weights, k=1)[0]
            promoted = rating >= 4 and random.random() < 0.18
            rows.append({
                "employee_id": e["employee_id"],
                "review_year": year, "rating": rating, "promoted": promoted,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 5. Terminations
# ---------------------------------------------------------------------------
def build_terminations(emp_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    termed = emp_df[~emp_df["is_active"]]
    for _, e in termed.iterrows():
        is_voluntary = random.random() < VOLUNTARY_SHARE
        if e["department"] == "Marketing" and e["termination_date"] >= date(2025, 5, 1):
            is_voluntary = random.random() < 0.88
        if is_voluntary:
            term_type = "Voluntary"
            reason = weighted_choice(VOLUNTARY_REASONS)
            base_reg = {"Technology": 0.75, "Consulting": 0.68,
                        "People & Culture": 0.55}.get(e["department"], 0.62)
            regrettable = random.random() < base_reg
        else:
            term_type = "Involuntary"
            reason = weighted_choice(INVOLUNTARY_REASONS)
            regrettable = False
        rows.append({
            "employee_id": e["employee_id"],
            "termination_date": e["termination_date"],
            "termination_type": term_type,
            "is_regrettable": regrettable,
            "reason": reason,
            "tenure_at_term_years": e["tenure_years"],
            "department": e["department"],
            "level": e["level"],
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 6. Hires
# ---------------------------------------------------------------------------
def build_hires(emp_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    sources = [
        ("Referral", 0.25), ("LinkedIn", 0.30), ("Agency", 0.15),
        ("Job board", 0.18), ("Direct", 0.07), ("University", 0.05),
    ]
    for _, e in emp_df.iterrows():
        if e["hire_date"] < HISTORY_START:
            continue
        dept_mean = DEPARTMENTS[e["department"]]["tt_hire_mean"]
        tth = max(7, int(np.random.normal(dept_mean, dept_mean * 0.30)))
        req_open = e["hire_date"] - timedelta(days=tth)
        offer_lead = random.randint(7, 21)
        offer_accepted = e["hire_date"] - timedelta(days=offer_lead)
        rows.append({
            "employee_id": e["employee_id"],
            "department": e["department"], "level": e["level"],
            "requisition_open_date": req_open,
            "offer_accepted_date": offer_accepted,
            "start_date": e["hire_date"],
            "time_to_hire_days": (offer_accepted - req_open).days,
            "source": weighted_choice(sources),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 7. eNPS surveys (quarterly)
# ---------------------------------------------------------------------------
def build_enps(emp_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    survey_dates = []
    y, m = 2023, 9
    while date(y, m, 15) <= TODAY:
        survey_dates.append(date(y, m, 15))
        m += 3
        if m > 12:
            m -= 12
            y += 1
    dept_baseline = {
        "Consulting": 7.0, "Technology": 7.6, "Sales": 7.2,
        "Finance": 7.8, "Marketing": 7.4, "People & Culture": 8.3,
    }
    for _, e in emp_df.iterrows():
        for survey in survey_dates:
            if e["hire_date"] > survey:
                continue
            if pd.notna(e["termination_date"]) and e["termination_date"] < survey:
                continue
            if random.random() > 0.70:
                continue
            tenure_now = (survey - e["hire_date"]).days / 365.25
            base = dept_baseline[e["department"]]
            if 4.0 <= tenure_now <= 5.5:
                base -= 1.1
            if e["department"] == "Consulting" and survey >= date(2025, 6, 1):
                base -= 0.6
            if e["department"] == "Marketing" and survey >= date(2025, 9, 1):
                base -= 0.7
            score = int(round(np.clip(np.random.normal(base, 1.5), 0, 10)))
            if score >= 9:
                category = "Promoter"
            elif score >= 7:
                category = "Passive"
            else:
                category = "Detractor"
            rows.append({
                "employee_id": e["employee_id"],
                "survey_date": survey, "score": score, "category": category,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 8. Flight risk (current employees)
# ---------------------------------------------------------------------------
def build_flight_risk(emp_df, comp_df, perf_df, enps_df):
    active = emp_df[emp_df["is_active"]].copy()

    perf_sorted = perf_df.sort_values(["employee_id", "review_year"])
    last_rating = perf_sorted.groupby("employee_id")["rating"].last().rename("last_rating")
    prior_rating = perf_sorted.groupby("employee_id").apply(
        lambda g: g["rating"].iloc[-2] if len(g) >= 2 else np.nan,
        include_groups=False,
    ).rename("prior_rating")

    promoted_yrs = (perf_df[perf_df["promoted"]].groupby("employee_id")["review_year"].max()
                    .rename("last_promoted_year"))
    last_enps = enps_df.sort_values("survey_date").groupby("employee_id")["score"].last().rename("last_enps_score")

    df = (active.merge(last_rating, on="employee_id", how="left")
                .merge(prior_rating, on="employee_id", how="left")
                .merge(promoted_yrs, on="employee_id", how="left")
                .merge(last_enps, on="employee_id", how="left")
                .merge(comp_df[["employee_id", "comp_ratio"]], on="employee_id", how="left"))

    def months_since_promo(r):
        if pd.notna(r.get("last_promoted_year")):
            return int(((TODAY - date(int(r["last_promoted_year"]), 12, 1)).days) / 30)
        return int(min(60, r["tenure_years"] * 12))
    df["months_since_promotion"] = df.apply(months_since_promo, axis=1)
    df["manager_change_12mo"] = np.random.random(len(df)) < 0.18

    def trend(r):
        if pd.isna(r["last_rating"]) or pd.isna(r["prior_rating"]):
            return "Unknown"
        if r["last_rating"] > r["prior_rating"]:
            return "Improving"
        if r["last_rating"] < r["prior_rating"]:
            return "Declining"
        return "Flat"
    df["perf_trend"] = df.apply(trend, axis=1)

    score = np.zeros(len(df))
    score += np.where((df["tenure_years"] >= 2) & (df["tenure_years"] <= 4), 18, 0)
    score += np.where(df["tenure_years"] > 4, 8, 0)
    score += np.where(df["months_since_promotion"] >= 24, 18, 0)
    score += np.where(df["comp_ratio"] < 0.95, 15, 0)
    score += np.where(df["comp_ratio"].between(0.95, 1.0), 6, 0)
    score += np.where(df["last_enps_score"] <= 6, 18, 0)
    score += np.where(df["last_enps_score"].between(7, 8), 6, 0)
    score += np.where(df["perf_trend"] == "Declining", 12, 0)
    score += np.where(df["manager_change_12mo"], 8, 0)
    score += np.random.normal(0, 5, len(df))
    score = np.clip(score, 0, 100).round(1)
    df["flight_risk_score"] = score

    def band(s):
        if s >= 65: return "Critical"
        if s >= 45: return "High"
        if s >= 25: return "Medium"
        return "Low"
    df["flight_risk_band"] = df["flight_risk_score"].apply(band)

    return df[[
        "employee_id", "tenure_years", "months_since_promotion",
        "manager_change_12mo", "comp_ratio", "last_enps_score",
        "perf_trend", "flight_risk_score", "flight_risk_band",
    ]]


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
def main():
    print(">> Building employees...")
    emp = build_employees()
    print(f"   {len(emp)} records ({emp['is_active'].sum()} active, {(~emp['is_active']).sum()} terminated)")

    print(">> Assigning manager hierarchy...")
    emp = assign_managers(emp)

    print(">> Building compensation...")
    comp = build_compensation(emp)

    print(">> Building performance ratings...")
    perf = build_performance(emp)

    print(">> Building terminations...")
    terms = build_terminations(emp)

    print(">> Building hires...")
    hires = build_hires(emp)

    print(">> Building eNPS surveys...")
    enps = build_enps(emp)

    print(">> Building flight risk scores...")
    risk = build_flight_risk(emp, comp, perf, enps)

    emp_out = emp[[
        "employee_id", "full_name", "first_name", "last_name", "gender",
        "department", "level", "job_title", "location",
        "hire_date", "termination_date", "is_active", "tenure_years",
        "manager_id", "birth_date",
    ]]
    emp_out.to_csv(OUT_DIR / "employees.csv", index=False)
    comp.to_csv(OUT_DIR / "compensation.csv", index=False)
    perf.to_csv(OUT_DIR / "performance.csv", index=False)
    terms.to_csv(OUT_DIR / "terminations.csv", index=False)
    hires.to_csv(OUT_DIR / "hires.csv", index=False)
    enps.to_csv(OUT_DIR / "enps_surveys.csv", index=False)
    risk.to_csv(OUT_DIR / "flight_risk.csv", index=False)

    print(f"\nWrote 7 CSVs to {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
