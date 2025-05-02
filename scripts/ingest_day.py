#!/usr/bin/env python3
"""
One-day ingest for Systems-and-Transients prototype
Streams: Pushshift-Reddit (sample), Wikipedia edited-pages, GDELT daily events
Target date passed as YYYY-MM-DD
"""

import sys, datetime as dt, pathlib, io, zipfile, warnings
import requests, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW  = ROOT / "data" / "raw"

# ── helpers ──────────────────────────────────────────────────────────────
def day_arg() -> dt.date:
    if len(sys.argv) != 2:
        sys.exit("Usage: ingest_day.py YYYY-MM-DD")
    return dt.date.fromisoformat(sys.argv[1])

def outdir(day: dt.date) -> pathlib.Path:
    p = RAW / day.isoformat()
    p.mkdir(parents=True, exist_ok=True)
    return p

# ── 1 ▸ Reddit sample (≤2 000 comments, no key) ──────────────────────────
def fetch_reddit(day: dt.date) -> pd.DataFrame:
    after  = int(dt.datetime.combine(day, dt.time.min).timestamp())
    before = int(dt.datetime.combine(day, dt.time.max).timestamp())
    url = (f"https://api.pushshift.io/reddit/comment/search/"
           f"?after={after}&before={before}&size=2000")
    js   = requests.get(url, timeout=30).json()
    data = js.get("data", [])
    if not data:
        warnings.warn("Pushshift returned zero rows")
        return pd.DataFrame()
    return pd.DataFrame([{
        "id":        c.get("id"),
        "created_utc": c.get("created_utc"),
        "author":    c.get("author"),
        "subreddit": c.get("subreddit"),
        "body":      c.get("body")
    } for c in data])

# ── 2 ▸ Wikipedia edited-pages (month list covers any day) ───────────────
def fetch_wikipedia(day: dt.date) -> pd.DataFrame:
    y, m = day.year, day.month
    url = ("https://wikimedia.org/api/rest_v1/metrics/edited-pages/top-by-edits/"
           f"en.wikipedia.org/all-editor-types/all-page-types/{y}/{m:02d}/all-days")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return pd.DataFrame(r.json()["items"][0]["results"])

# ── 3 ▸ GDELT daily events (S3 mirror, valid cert) ───────────────────────
def fetch_gdelt(day):
    """Download daily GDELT file, trying both .CSV and .csv variants."""
    ymd = day.strftime("%Y%m%d")
    for fname in (f"{ymd}.export.CSV.zip", f"{ymd}.export.csv.zip"):
        url = f"https://gdelt-open-data.s3.amazonaws.com/events/{fname}"
        r = requests.get(url, timeout=60)
        if r.status_code == 200:
            return pd.read_csv(io.BytesIO(r.content),
                               compression="zip", sep="\t", low_memory=False)
    raise RuntimeError(f"GDELT file not found in S3 mirror for {ymd}")
