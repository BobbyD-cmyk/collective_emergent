#!/usr/bin/env python3
import sys, pathlib, datetime as dt, io, zipfile, warnings
import requests, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW  = ROOT / "data" / "raw"

def need_date():
    if len(sys.argv) != 2:
        sys.exit("usage: ingest_day.py YYYY-MM-DD")
    return dt.date.fromisoformat(sys.argv[1])

def ensure_out(d):
    p = RAW / d.isoformat()
    p.mkdir(parents=True, exist_ok=True)
    return p

# 1 ▸ Reddit (Pushshift ±2 000 comment sample)
def reddit_df(day):
    a = int(dt.datetime.combine(day, dt.time.min ).timestamp())
    b = int(dt.datetime.combine(day, dt.time.max ).timestamp())
    url = f"https://api.pushshift.io/reddit/comment/search/?after={a}&before={b}&size=2000"
    data = requests.get(url, timeout=30).json().get("data", [])
    if not data:
        warnings.warn("Pushshift returned zero rows")
        return pd.DataFrame()
    return pd.DataFrame([{k:c.get(k) for k in ("id","created_utc","author","subreddit","body")}
                         for c in data])

# 2 ▸ Wikipedia edited-pages (month list, covers 2023-10-07)
def wiki_df(day):
    y, m = day.year, day.month
    url = ("https://wikimedia.org/api/rest_v1/metrics/edited-pages/top-by-edits/"
           f"en.wikipedia.org/all-editor-types/all-page-types/{y}/{m:02d}/all-days")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return pd.DataFrame(r.json()["items"][0]["results"])

# 3 ▸ GDELT daily events (S3 mirror, valid cert)
def gdelt_df(day):
    ymd  = day.strftime("%Y%m%d")
    url  = f"https://gdelt-open-data.s3.amazonaws.com/events/{ymd}.export.csv.zip"
    buf  = io.BytesIO(requests.get(url, timeout=60).content)
    with zipfile.ZipFile(buf) as zf, zf.open(zf.namelist()[0]) as f:
        return pd.read_csv(f, sep="\t", low_memory=False)

def main():
    d   = need_date()
    out = ensure_out(d)

    reddit_df(d).to_parquet(out/"reddit.parquet",   compression="zstd", engine="fastparquet")
    wiki_df(d)  .to_parquet(out/"wikipedia.parquet",compression="zstd", engine="fastparquet")
    gdelt_df(d) .to_parquet(out/"gdelt.parquet",    compression="zstd", engine="fastparquet")

    print("✓ ingest complete →", out)

if __name__ == "__main__":
    main()
