"""Shared data loading + filter utilities for the dashboard."""
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

DEPT_ORDER = ["Consulting", "Technology", "Sales", "Finance", "Marketing", "People & Culture"]
LEVEL_ORDER = ["IC1", "IC2", "IC3", "IC4", "IC5", "M1", "M2", "M3", "M4"]
TODAY = pd.Timestamp("2026-05-11")

# Consistent palette across pages
COLORS = {
    "primary":     "#5B5FCF",
    "Female":      "#9C6ADE",
    "Male":        "#5B8FF9",
    "Non-binary":  "#13C2C2",
    "Voluntary":   "#F6BD16",
    "Involuntary": "#E8684A",
    "Promoter":    "#2EC27E",
    "Passive":     "#A0A4B8",
    "Detractor":   "#E8684A",
    "Critical":    "#D7263D",
    "High":        "#F46036",
    "Medium":      "#F6BD16",
    "Low":         "#2EC27E",
}


@st.cache_data
def load_employees():
    return pd.read_csv(
        DATA_DIR / "employees.csv",
        parse_dates=["hire_date", "termination_date", "birth_date"],
    )


@st.cache_data
def load_compensation():
    return pd.read_csv(DATA_DIR / "compensation.csv", parse_dates=["last_increase_date"])


@st.cache_data
def load_performance():
    return pd.read_csv(DATA_DIR / "performance.csv")


@st.cache_data
def load_terminations():
    return pd.read_csv(DATA_DIR / "terminations.csv", parse_dates=["termination_date"])


@st.cache_data
def load_hires():
    return pd.read_csv(
        DATA_DIR / "hires.csv",
        parse_dates=["requisition_open_date", "offer_accepted_date", "start_date"],
    )


@st.cache_data
def load_enps():
    return pd.read_csv(DATA_DIR / "enps_surveys.csv", parse_dates=["survey_date"])


@st.cache_data
def load_flight_risk():
    return pd.read_csv(DATA_DIR / "flight_risk.csv")


def sidebar_filters(emp_df, key_prefix=""):
    """Render department + level filters in sidebar. Returns lists."""
    st.sidebar.markdown("### Filters")
    depts = st.sidebar.multiselect(
        "Department", DEPT_ORDER, default=DEPT_ORDER, key=f"{key_prefix}depts"
    )
    levels = st.sidebar.multiselect(
        "Level", LEVEL_ORDER, default=LEVEL_ORDER, key=f"{key_prefix}levels"
    )
    if not depts:
        depts = DEPT_ORDER
    if not levels:
        levels = LEVEL_ORDER
    return depts, levels


def apply_filters(df, depts, levels, dept_col="department", level_col="level"):
    return df[df[dept_col].isin(depts) & df[level_col].isin(levels)]


def tenure_band(years):
    if years < 1:
        return "0-1 yr"
    if years < 2:
        return "1-2 yr"
    if years < 4:
        return "2-4 yr"
    if years < 6:
        return "4-6 yr"
    if years < 10:
        return "6-10 yr"
    return "10+ yr"


TENURE_BAND_ORDER = ["0-1 yr", "1-2 yr", "2-4 yr", "4-6 yr", "6-10 yr", "10+ yr"]
