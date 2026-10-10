import pandas as pd


def trials_per_phase(df):
    """Count trials in each phase."""
    counts = df["phase"].value_counts().rename_axis("phase").reset_index(name="trials")
    return counts


def avg_enrollment_by_phase(df):
    """Average enrollment per phase. Trials with no enrollment are skipped."""
    out = df.groupby("phase", as_index=False)["enrollment"].mean()
    return out.rename(columns={"enrollment": "avg_enrollment"})


def completion_rate(df):
    """Share of finished trials that ended as 'Completed'.

    Only trials that have reached an end state count. Ongoing trials
    (recruiting, not yet recruiting, etc.) would unfairly lower the rate.
    """
    finished = df[df["status"].isin(["Completed", "Terminated", "Withdrawn"])]
    if len(finished) == 0:
        return None
    return (finished["status"] == "Completed").mean()


def trials_per_year(df):
    """Count trials by start year, sorted chronologically."""
    years = df["start_year"].dropna().astype(int)
    counts = years.value_counts().sort_index()
    return counts.rename_axis("start_year").reset_index(name="trials")

