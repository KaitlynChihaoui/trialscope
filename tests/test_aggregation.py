import pandas as pd
import pytest

from trialscope.aggregation import (
    trials_per_phase,
    avg_enrollment_by_phase,
    completion_rate,
    trials_per_year,
)


def make_df():
    """A tiny hand-built table in the same shape clean_trials() produces."""
    return pd.DataFrame({
        "phase": ["Phase 1", "Phase 1", "Phase 2", "Not applicable"],
        "enrollment": [10.0, 30.0, 100.0, None],
        "status": ["Completed", "Terminated", "Recruiting", "Completed"],
        "start_year": [2019.0, 2020.0, 2020.0, None],
    })


def test_trials_per_phase_counts():
    result = trials_per_phase(make_df())
    counts = dict(zip(result["phase"], result["trials"]))
    assert counts == {"Phase 1": 2, "Phase 2": 1, "Not applicable": 1}


def test_avg_enrollment_skips_missing():
    result = avg_enrollment_by_phase(make_df())
    avg = dict(zip(result["phase"], result["avg_enrollment"]))
    assert avg["Phase 1"] == 20.0
    assert avg["Phase 2"] == 100.0
    assert pd.isna(avg["Not applicable"])


def test_completion_rate_ignores_ongoing_trials():
    # Finished trials: Completed, Terminated, Completed -> 2 of 3.
    # The "Recruiting" trial must not count against the rate.
    assert completion_rate(make_df()) == pytest.approx(2 / 3)


def test_completion_rate_returns_none_when_nothing_finished():
    df = pd.DataFrame({"status": ["Recruiting", "Not yet recruiting"]})
    assert completion_rate(df) is None


def test_trials_per_year_sorted_and_skips_missing():
    result = trials_per_year(make_df())
    assert list(result["start_year"]) == [2019, 2020]
    assert list(result["trials"]) == [1, 2]