#!/usr/bin/env python3
# one-day ingest – 7 Oct 2023  (Reddit · Wikipedia · GDELT)

import sys, pathlib, datetime as dt, io, zipfile, requests, pandas as pd, warnings

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW  = ROOT / "data" / "raw"

def arg_day():
    if len(sys.argv) != 2:
        sys.exit("Usage: ./ingest_day.py YYYY-MM-DD")
    return dt.date.fromisoformat(sys.argv[1])

def ensure_out(d):
    p = RAW / d.isoformat(); p.mkdir(parents=True, exist_ok=True); return p

# 1 ▸ Reddit comment slice (Pushshift)
def reddit_df(day):
    a = int(dt.datetime.combine(day, dt.time.min).timestamp())
    b = int(dt.datetime.combine(day, dt.time.max).timestamp())
    url = f"https://api.pushshift.io/reddit/comment/search/?after={a}&before={b}&size=2000"
    resp = requests.get(url, timeout=30).json()
    if "data" not in resp or not resp["data"]:          # API outage or empty window
        warnings.warn("Pushshift returned no data; writing empty reddit.parquet")
        return pd.DataFrame()
    data = resp["data"]
    return pd.DataFrame({
        "id":      [c.get("id")         for c in data],
        "utc":     [c.get("created_utc")for c in data],
        "author":  [c.get("author")     for c in data],
        "sub":     [c.get("subreddit")  for c in data],
        "body":    [c.get("body")       for c in data]
    })

# 2 ▸ Wikipedia edited-pages top
def wiki_df(day):
    y,m,d = day.year, day.month, day.day
    api = ("https://wikimedia.org/api/rest_v1/metrics/edited-pages/top/"
           f"en.wikipedia/all-editor-types/all-page-types/{y}/{m:02d}/{d:02d}")
    r = requests.get(api, timeout=30); r.raise_for_status()
    return pd.DataFrame(r.json()["items"][0]["results"])

# 3 ▸ GDELT events daily CSV.ZIP
def gdelt_df(day):
    zurl = f"https://data.gdeltproject.org/events/{day:%Y%m%d}.export.CSV.zip"
    buf  = io.BytesIO(requests.get(zurl, timeout=60).content)
    with zipfile.ZipFile(buf) as zf, zf.open(zf.namelist()[0]) as f:
        return pd.read_csv(f, sep="\t", low_memory=False)

def main():
    day, out = arg_day(), ensure_out(arg_day())
    print("→ Reddit …");   reddit_df(day).to_parquet(out/"reddit.parquet","zstd", engine="fastparquet")
    print("→ Wikipedia …");wiki_df(day)  .to_parquet(out/"wikipedia.parquet","zstd", engine="fastparquet")
    print("→ GDELT …");    gdelt_df(day) .to_parquet(out/"gdelt.parquet","zstd", engine="fastparquet")
    print(f"✓ ingest complete → {out}")

if __name__ == "__main__":
    main()
