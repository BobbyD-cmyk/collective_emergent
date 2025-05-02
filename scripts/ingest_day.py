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
def fetch_reddit(day):
    """Return all Reddit comments for *day* from Pushshift monthly dump.
       Downloads the 2-GB .zst file once, streams & slices the target date."""
    import zstandard as zstd, json, datetime as dt, io, requests
    month_file = pathlib.Path(f"RC_{day:%Y-%m}.zst")
    if not month_file.exists():
        url = f"https://files.pushshift.io/reddit/comments/{month_file.name}"
        print("↓ downloading", month_file.name)
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(month_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=2**20):
                    f.write(chunk)
    rows = []
    tgt = day
    with open(month_file, 'rb') as fh, zstd.ZstdDecompressor().stream_reader(fh) as zr:
        for line in io.TextIOWrapper(zr, encoding='utf-8'):
            c = json.loads(line)
            if dt.datetime.utcfromtimestamp(c['created_utc']).date() == tgt:
                rows.append({k: c.get(k) for k in
                    ('id','created_utc','author','subreddit','body')})
    return pd.DataFrame(rows)
def fetch_wikipedia(day):
    """Return the full top-edited list for a single UTC day."""
    y,m,d = day.year, day.month, day.day
    url = ( "https://wikimedia.org/api/rest_v1/metrics/edited-pages/top/"
            f"en.wikipedia/all-editor-types/all-page-types/{y}/{m:02d}/{d:02d}" )
    r = requests.get(url, timeout=30); r.raise_for_status()
    # items[0]['results'] is the list we actually need
    return pd.DataFrame(r.json()['items'][0]['results'])
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
