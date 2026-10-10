import requests
import pandas as pd

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"


def fetch_trials(condition, max_trials=500, page_size=100):
    """Fetch trials for a condition from ClinicalTrials.gov.

    The API returns results in pages, so we keep following the
    'nextPageToken' until we have enough trials or run out.
    """
    studies = []
    params = {
        "query.cond": condition,
        "pageSize": page_size,
        "format": "json",
    }

    while len(studies) < max_trials:
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        studies.extend(data.get("studies", []))

        next_token = data.get("nextPageToken")
        if not next_token:
            break
        params["pageToken"] = next_token

    return studies[:max_trials]


def studies_to_dataframe(studies):
    """Flatten the API's deeply nested JSON into one row per trial."""
    rows = []
    for study in studies:
        p = study.get("protocolSection", {})
        ident = p.get("identificationModule", {})
        status = p.get("statusModule", {})
        design = p.get("designModule", {})
        sponsor = p.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {})

        rows.append({
            "nct_id": ident.get("nctId"),
            "title": ident.get("briefTitle"),
            "status": status.get("overallStatus"),
            "start_date": status.get("startDateStruct", {}).get("date"),
            "completion_date": status.get("completionDateStruct", {}).get("date"),
            "phase": ", ".join(design.get("phases", [])) or None,
            "enrollment": design.get("enrollmentInfo", {}).get("count"),
            "sponsor": sponsor.get("name"),
            "sponsor_class": sponsor.get("class"),
        })

    return pd.DataFrame(rows)