#!/usr/bin/env python3\n"""\nOne-day ingest for Systems-and-Transients prototype\nStreams: Pushshift-Reddit (sample), Wikipedia edited-pages, GDELT daily events\nTarget date passed as YYYY-MM-DD\n"""\n\nimport sys, datetime as dt, pathlib, io, zipfile, warnings\nimport requests, pandas as pd\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nRAW  = ROOT / "data" / "raw"\n\n# ── helpers ──────────────────────────────────────────────────────────────\ndef day_arg() -> dt.date:\n    if len(sys.argv) != 2:\n        sys.exit("Usage: ingest_day.py YYYY-MM-DD")\n    return dt.date.fromisoformat(sys.argv[1])\n\ndef outdir(day: dt.date) -> pathlib.Path:\n    p = RAW / day.isoformat()\n    p.mkdir(parents=True, exist_ok=True)\n    return p\n\n# ── 1 ▸ Reddit sample (≤2 000 comments, no key) ──────────────────────────\ndef fetch_reddit(day):
    """Return all Reddit *submissions* for *day*; fall back to monthly comments if needed."""
    import zstandard as zstd, json, datetime as dt, io, requests, pandas as pd, pathlib
    daily = pathlib.Path(f"RS_{day:%Y-%m-%d}.zst")
    if not daily.exists():
        url = f"https://files.pushshift.io/reddit/submissions/daily/{day:%Y}/{day:%m}/{daily.name}"
        print("↓ downloading", daily.name)
        r = requests.get(url, stream=True, timeout=60)
        if r.status_code == 200:
            with open(daily,'wb') as f:
                for chunk in r.iter_content(2**20): f.write(chunk)
        else:
            # fallback: monthly comments file
            month = pathlib.Path(f"RC_{day:%Y-%m}.zst")
            if not month.exists():
                url = f"https://files.pushshift.io/reddit/comments/full/{month.name}"
                print("↓ downloading", month.name)
                r = requests.get(url, stream=True, timeout=60)
                r.raise_for_status()
                with open(month,'wb') as f:
                    for c in r.iter_content(2**20): f.write(c)
            src = month
        src = daily if daily.exists() else month
    else:
        src = daily
    rows = []
    with open(src,'rb') as fh, zstd.ZstdDecompressor().stream_reader(fh) as zr:
        for line in io.TextIOWrapper(zr, encoding='utf-8'):
            j=json.loads(line)
            if dt.datetime.utcfromtimestamp(j['created_utc']).date()==day:
                rows.append({
                    'id':j.get('id'),
                    'utc':j.get('created_utc'),
                    'author':j.get('author'),
                    'sub':j.get('subreddit'),
                    'title':j.get('title'),
                    'self':j.get('selftext','')
                })
    return pd.DataFrame(rows)\ndef fetch_wikipedia(day):\n    """Return Wikimedia *edited-pages/top* list for exactly one UTC day."""\n    y,m,d = day.year, day.month, day.day\n    url = ("https://wikimedia.org/api/rest_v1/metrics/edited-pages/top/"\n           f"en.wikipedia/all-editor-types/all-page-types/{y}/{m:02d}/{d:02d}")\n    r = requests.get(url, timeout=30); r.raise_for_status()\n    return pd.DataFrame(r.json()['items'][0]['results'])\ndef fetch_gdelt(day):\n    """Download daily GDELT file, trying both .CSV and .csv variants."""\n    ymd = day.strftime("%Y%m%d")\n    for fname in (f"{ymd}.export.CSV.zip", f"{ymd}.export.csv.zip"):\n        url = f"https://gdelt-open-data.s3.amazonaws.com/events/{fname}"\n        r = requests.get(url, timeout=60)\n        if r.status_code == 200:\n            return pd.read_csv(io.BytesIO(r.content),\n                               compression="zip", sep="\t", low_memory=False)\n    raise RuntimeError(f"GDELT file not found in S3 mirror for {ymd}")\n