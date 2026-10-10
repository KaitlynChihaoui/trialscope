import streamlit as st
import plotly.express as px

from trialscope.api import fetch_trials, studies_to_dataframe
from trialscope.cleaning import clean_trials
from trialscope.aggregation import (
    trials_per_phase,
    avg_enrollment_by_phase,
    completion_rate,
    trials_per_year,
)

st.set_page_config(page_title="TrialScope", layout="wide")


@st.cache_data(ttl=3600, show_spinner="Fetching trials from ClinicalTrials.gov...")
def load_trials(condition, max_trials):
    """Fetch and clean trials. Cached so repeat searches are instant."""
    studies = fetch_trials(condition, max_trials=max_trials)
    if not studies:
        return None
    return clean_trials(studies_to_dataframe(studies))


st.title("TrialScope")
st.caption("Explore the clinical trial landscape for a condition, using ClinicalTrials.gov data.")

# ---------- Sidebar: search ----------
with st.sidebar:
    st.header("Search")
    condition = st.text_input("Condition", value="diabetes")
    max_trials = st.slider("Max trials to fetch", 100, 1000, 300, step=100)

if not condition.strip():
    st.info("Enter a condition in the sidebar to get started.")
    st.stop()

try:
    df = load_trials(condition.strip(), max_trials)
except Exception as e:
    st.error(f"Couldn't reach ClinicalTrials.gov: {e}")
    st.stop()

if df is None:
    st.warning(f"No trials found for '{condition}'. Try a broader term.")
    st.stop()

# ---------- Sidebar: filters ----------
with st.sidebar:
    st.header("Filters")
    all_phases = sorted(df["phase"].unique())
    phases = st.multiselect("Phase", all_phases, default=all_phases)

    all_statuses = sorted(df["status"].dropna().unique())
    statuses = st.multiselect("Status", all_statuses, default=all_statuses)

    years = df["start_year"].dropna()
    if not years.empty:
        lo, hi = int(years.min()), int(years.max())
        if lo < hi:
            year_range = st.slider("Start year", lo, hi, (lo, hi))
            st.caption("Trials with no start date are hidden when this filter is narrowed.")
        else:
            year_range = (lo, hi)
    else:
        year_range = None

filtered = df[df["phase"].isin(phases) & df["status"].isin(statuses)]
if year_range is not None:
    in_range = filtered["start_year"].between(*year_range)
    full_range = year_range == (int(years.min()), int(years.max()))
    # Only drop undated trials if the user actually narrowed the range
    filtered = filtered if full_range else filtered[in_range]

if filtered.empty:
    st.warning("No trials match these filters.")
    st.stop()

# ---------- Headline numbers ----------
rate = completion_rate(filtered)
col1, col2, col3 = st.columns(3)
col1.metric("Trials", f"{len(filtered):,}")
col2.metric("Median enrollment", f"{filtered['enrollment'].median():,.0f}"
            if filtered["enrollment"].notna().any() else "n/a")
col3.metric("Completion rate", f"{rate:.0%}" if rate is not None else "n/a",
            help="Completed trials as a share of finished trials (completed, terminated, withdrawn). Ongoing trials are excluded.")

# ---------- Charts ----------
left, right = st.columns(2)

with left:
    phase_counts = trials_per_phase(filtered)
    fig = px.bar(phase_counts, x="phase", y="trials", title="Trials by phase")
    st.plotly_chart(fig, use_container_width=True)

with right:
    enroll = avg_enrollment_by_phase(filtered).dropna(subset=["avg_enrollment"])
    fig = px.bar(enroll, x="phase", y="avg_enrollment", title="Average enrollment by phase")
    st.plotly_chart(fig, use_container_width=True)

yearly = trials_per_year(filtered)
if not yearly.empty:
    fig = px.line(yearly, x="start_year", y="trials", markers=True, title="Trials started per year")
    st.plotly_chart(fig, use_container_width=True)

# ---------- Data table ----------
st.subheader("Trial details")
table = filtered[["nct_id", "title", "phase", "status", "enrollment", "start_date", "sponsor"]]
st.dataframe(table, use_container_width=True, hide_index=True)
st.download_button(
    "Download filtered results (CSV)",
    table.to_csv(index=False).encode("utf-8"),
    file_name=f"trialscope_{condition.strip().replace(' ', '_')}.csv",
    mime="text/csv",
)