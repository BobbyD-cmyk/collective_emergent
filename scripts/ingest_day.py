#!/usr/bin/env python3
import sys, pathlib, datetime as dt, io, zipfile, requests, pandas as pd, warnings
ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW  = ROOT / "data" / "raw"

def arg_day():
    if len(sys.argv)!=2: sys.exit("Usage: ./ingest_day.py YYYY-MM-DD")
    return dt.date.fromisoformat(sys.argv[1])

def outdir(d):
    p = RAW / d.isoformat(); p.mkdir(parents=True, exist_ok=True); return p

def reddit_df(day):
    a = int(dt.datetime.combine(day,dt.time.min).timestamp())
    b = int(dt.datetime.combine(day,dt.time.max).timestamp())
    url = f"https://api.pushshift.io/reddit/comment/search/?after={a}&before={b}&size=2000"
    js  = requests.get(url,timeout=30).json(); data = js.get("data", [])
    if not data:
        warnings.warn("Pushshift empty; writing zero-row Parquet"); return pd.DataFrame()
    return pd.DataFrame([{k:c.get(k) for k in ("id","created_utc","author","subreddit","body")} for c in data])

def wiki_df(day):
    # month-level top-by-edits (daily list is not available)
    y,m = day.year, day.month
    url = ( "https://wikimedia.org/api/rest_v1/metrics/edited-pages/top-by-edits/"
            f"en.wikipedia.org/all-editor-types/all-page-types/{y}/{m:02d}/all-days")
    r = requests.get(url, timeout=30); r.raise_for_status()
    return pd.DataFrame(r.json()["items"][0]["results"])

def gdelt_df(day):
    ymd = day.strftime("%Y%m%d")
    url = f"https://gdelt-open-data.s3.amazonaws.com/events/{ymd}.export.csv.zip"
    return pd.read_csv(url, compression="zip", sep="\t", low_memory=False)
    d = arg_day(); tgt = outdir(d)
    reddit_df(d).to_parquet(tgt/"reddit.parquet",   compression="zstd", engine="fastparquet")
    wiki_df(d)  .to_parquet(tgt/"wikipedia.parquet",compression="zstd", engine="fastparquet")
    gdelt_df(d) .to_parquet(tgt/"gdelt.parquet",    compression="zstd", engine="fastparquet")
    print(f"✓ ingest complete → {tgt}")

if __name__=="__main__": main()
