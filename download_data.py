"""Download the DOSM parquet files the pipeline uses into ./data and log
retrieval time, size and SHA-256 (cite these in the report). Run: python3 download_data.py"""
import datetime as dt
import hashlib
import urllib.request
from pathlib import Path

FILES = {
    "hh_income_district": "hies", "hh_poverty_district": "hies", "hh_access_amenities": "hies",
    "hies_state": "hies", "hh_poverty_state": "hies", "lfs_district": "labour", "lfs_state_sex": "labour",
    "population_district": "population", "hh_lq_state": "demography",
}
out = Path(__file__).parent / "data"; out.mkdir(exist_ok=True)
log = ["dataset,url,retrieved_utc,bytes,sha256"]
for name, folder in FILES.items():
    url = f"https://storage.dosm.gov.my/{folder}/{name}.parquet"
    data = urllib.request.urlopen(url, timeout=60).read()
    (out / f"{name}.parquet").write_bytes(data)
    log.append(f"{name},{url},{dt.datetime.utcnow():%Y-%m-%dT%H:%MZ},{len(data)},{hashlib.sha256(data).hexdigest()}")
    print("ok", name, len(data))
(out / "retrieval_log.csv").write_text("\n".join(log) + "\n")
