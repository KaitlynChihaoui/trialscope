import numpy as np
import pandas as pd

from trialscope.cleaning import clean_phase, clean_trials


def test_clean_phase_single():
    assert clean_phase("PHASE2") == "Phase 2"


def test_clean_phase_early():
    assert clean_phase("EARLY_PHASE1") == "Early Phase 1"


def test_clean_phase_combined():
    assert clean_phase("PHASE1, PHASE2") == "Phase 1/2"


def test_clean_phase_not_applicable():
    assert clean_phase("NA") == "Not applicable"


def test_clean_phase_missing():
    assert clean_phase(None) == "Not reported"
    assert clean_phase(np.nan) == "Not reported"


def test_clean_trials_keeps_missing_enrollment_as_nan():
    raw = pd.DataFrame({
        "phase": ["PHASE1"],
        "start_date": ["2021-03"],
        "completion_date": [None],
        "enrollment": [None],
        "status": ["ACTIVE_NOT_RECRUITING"],
    })
    clean = clean_trials(raw)
    assert pd.isna(clean.loc[0, "enrollment"])
    assert clean.loc[0, "status"] == "Active not recruiting"
    assert clean.loc[0, "start_year"] == 2021


def test_clean_trials_does_not_change_original():
    raw = pd.DataFrame({
        "phase": ["PHASE1"],
        "start_date": ["2021-03"],
        "completion_date": ["2022-01"],
        "enrollment": [10],
        "status": ["COMPLETED"],
    })
    clean_trials(raw)
    assert raw.loc[0, "phase"] == "PHASE1"