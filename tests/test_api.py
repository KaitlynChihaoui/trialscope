import json
from pathlib import Path

import pytest
import requests

from trialscope.api import fetch_trials, studies_to_dataframe

FIXTURE = Path(__file__).parent / "fixtures" / "diabetes_sample.json"


class FakeResponse:
    """Stands in for the object requests.get() returns."""

    def __init__(self, payload, error=None):
        self.payload = payload
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error

    def json(self):
        return self.payload


def make_studies(n, start=0):
    return [{"id": i} for i in range(start, start + n)]


# ---------- studies_to_dataframe (uses your real saved data) ----------

def test_studies_to_dataframe_on_real_fixture():
    with open(FIXTURE, encoding="utf-8") as f:
        studies = json.load(f)

    df = studies_to_dataframe(studies)

    assert len(df) == 20
    assert list(df.columns) == [
        "nct_id", "title", "status", "start_date", "completion_date",
        "phase", "enrollment", "sponsor", "sponsor_class",
    ]
    assert df["nct_id"].notna().all()


def test_studies_to_dataframe_handles_missing_fields():
    df = studies_to_dataframe([{}])  # a trial with nothing filled in
    assert len(df) == 1
    assert df.loc[0, "nct_id"] is None
    assert df.loc[0, "phase"] is None


# ---------- fetch_trials (the internet is faked) ----------

def test_fetch_trials_follows_pagination(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append(dict(params))
        if "pageToken" not in params:
            return FakeResponse({"studies": make_studies(2), "nextPageToken": "abc"})
        return FakeResponse({"studies": make_studies(1, start=2)})

    monkeypatch.setattr("trialscope.api.requests.get", fake_get)

    result = fetch_trials("diabetes", max_trials=100)

    assert len(result) == 3
    assert len(calls) == 2                      # it asked for two pages
    assert calls[1]["pageToken"] == "abc"       # and passed the bookmark along
    assert calls[0]["query.cond"] == "diabetes"


def test_fetch_trials_respects_max_trials(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return FakeResponse({"studies": make_studies(5), "nextPageToken": "more"})

    monkeypatch.setattr("trialscope.api.requests.get", fake_get)

    assert len(fetch_trials("diabetes", max_trials=3)) == 3


def test_fetch_trials_raises_on_http_error(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return FakeResponse({}, error=requests.HTTPError("500 Server Error"))

    monkeypatch.setattr("trialscope.api.requests.get", fake_get)

    with pytest.raises(requests.HTTPError):
        fetch_trials("diabetes")