"""Download the extra DOSM / data.gov.my files used by the B40 -> M40 layer into
./data and log retrieval time, size and SHA-256 in data/retrieval_log_mobility.csv.
Kept separate from download_data.py so the original snapshot stays untouched.
Run: python download_mobility.py"""
import datetime as dt
import hashlib
import io
import json
import urllib.request
from pathlib import Path

import pandas as pd

PARQUET = {
    "hies_malaysia_percentile": "hies",  # national income percentiles -> B40/M40 lines
    "hies_state_percentile": "hies",     # state income percentiles -> state lines
    "hies_district": "hies",             # district mean/median income, expenditure, Gini
    "hh_inequality_district": "hies",    # district Gini 2019, 2022, 2024
    "cpi_2d_state": "cpi",               # state CPI, monthly
    "formal_wages_state": "labour",      # state formal-sector median wage, monthly
}
# Not on storage.dosm.gov.my: Ministry of Education data via the data.gov.my API
API = {"completion_school_district": "https://api.data.gov.my/data-catalogue?id=completion_school_district&limit=100000"}

out = Path(__file__).parent / "data"
out.mkdir(exist_ok=True)
log = ["dataset,url,retrieved_utc,bytes,sha256"]


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "dash-uchiha-atlas"})
    return urllib.request.urlopen(req, timeout=120).read()


def _record(name: str, url: str, data: bytes) -> None:
    now = dt.datetime.now(dt.timezone.utc)
    log.append(f"{name},{url},{now:%Y-%m-%dT%H:%MZ},{len(data)},{hashlib.sha256(data).hexdigest()}")
    print("ok", name, len(data))


for name, folder in PARQUET.items():
    url = f"https://storage.dosm.gov.my/{folder}/{name}.parquet"
    data = _get(url)
    (out / f"{name}.parquet").write_bytes(data)
    _record(name, url, data)

for name, url in API.items():
    data = _get(url)
    df = pd.DataFrame(json.loads(data))
    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    (out / f"{name}.parquet").write_bytes(buf.getvalue())
    _record(name, url, data)  # hash of the raw API response

(out / "retrieval_log_mobility.csv").write_text("\n".join(log) + "\n")
