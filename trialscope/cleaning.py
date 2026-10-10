import pandas as pd

PHASE_LABELS = {
    "EARLY_PHASE1": "Early Phase 1",
    "PHASE1": "Phase 1",
    "PHASE2": "Phase 2",
    "PHASE3": "Phase 3",
    "PHASE4": "Phase 4",
}


def clean_phase(raw):
    """Turn a raw API phase string into a readable label."""
    if raw is None or pd.isna(raw):
        return "Not reported"
    if raw == "NA":
        return "Not applicable"

    labels = [PHASE_LABELS.get(p.strip(), p.strip()) for p in raw.split(",")]
    if len(labels) == 1:
        return labels[0]

    # Combined phases: ["Phase 1", "Phase 2"] -> "Phase 1/2"
    numbers = [label.replace("Phase ", "") for label in labels]
    return "Phase " + "/".join(numbers)


def clean_trials(df):
    """Return a cleaned copy of the trials table."""
    out = df.copy()

    out["phase"] = out["phase"].apply(clean_phase)

    # Dates come as "2021-03" or "2021-03-15", so allow mixed formats.
    # Anything unparseable becomes NaT instead of crashing.
    for col in ["start_date", "completion_date"]:
        out[col] = pd.to_datetime(out[col], errors="coerce", format="mixed")

    # Keep missing enrollment as NaN. Filling with 0 would drag averages down.
    out["enrollment"] = pd.to_numeric(out["enrollment"], errors="coerce")

    # "ACTIVE_NOT_RECRUITING" -> "Active not recruiting"
    out["status"] = out["status"].str.replace("_", " ").str.capitalize()

    out["start_year"] = out["start_date"].dt.year

    return out