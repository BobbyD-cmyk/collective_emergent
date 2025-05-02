#!/usr/bin/env python3\n"""\nOne-day ingest for Systems-and-Transients prototype\nStreams: Pushshift-Reddit (sample), Wikipedia edited-pages, GDELT daily events\nTarget date passed as YYYY-MM-DD\n"""\n\nimport sys, datetime as dt, pathlib, io, zipfile, warnings\nimport requests, pandas as pd\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nRAW  = ROOT / "data" / "raw"\n\n# ── helpers ──────────────────────────────────────────────────────────────\ndef day_arg() -> dt.date:\n    if len(sys.argv) != 2:\n        sys.exit("Usage: ingest_day.py YYYY-MM-DD")\n    return dt.date.fromisoformat(sys.argv[1])\n\ndef outdir(day: dt.date) -> pathlib.Path:\n    p = RAW / day.isoformat()\n    p.mkdir(parents=True, exist_ok=True)\n    return p\n\n# ── 1 ▸ Reddit sample (≤2 000 comments, no key) ──────────────────────────\ndef fetch_reddit(day):\n    """Return all Reddit *submissions* for *day*; fall back to monthly comments if needed."""\n    import zstandard as zstd, json, datetime as dt, io, requests, pandas as pd, pathlib\n    daily = pathlib.Path(f"RS_{day:%Y-%m-%d}.zst")\n    if not daily.exists():\n        url = f"https://files.pushshift.io/reddit/submissions/daily/{day:%Y}/{day:%m}/{daily.name}"\n        print("↓ downloading", daily.name)\n        r = requests.get(url, stream=True, timeout=60)\n        if r.status_code == 200:\n            with open(daily,'wb') as f:\n                for chunk in r.iter_content(2**20): f.write(chunk)\n        else:\n            # fallback: monthly comments file\n            month = pathlib.Path(f"RC_{day:%Y-%m}.zst")\n            if not month.exists():\n                url = f"https://files.pushshift.io/reddit/comments/full/{month.name}"\n                print("↓ downloading", month.name)\n                r = requests.get(url, stream=True, timeout=60)\n                r.raise_for_status()\n                with open(month,'wb') as f:\n                    for c in r.iter_content(2**20): f.write(c)\n            src = month\n        src = daily if daily.exists() else month\n    else:\n        src = daily\n    rows = []\n    with open(src,'rb') as fh, zstd.ZstdDecompressor().stream_reader(fh) as zr:\n        for line in io.TextIOWrapper(zr, encoding='utf-8'):\n            j=json.loads(line)\n            if dt.datetime.utcfromtimestamp(j['created_utc']).date()==day:\n                rows.append({\n                    'id':j.get('id'),\n                    'utc':j.get('created_utc'),\n                    'author':j.get('author'),\n                    'sub':j.get('subreddit'),\n                    'title':j.get('title'),\n                    'self':j.get('selftext','')\n                })\n    return pd.DataFrame(rows)\ndef fetch_wikipedia(day):\n    """Return Wikimedia *edited-pages/top* list for exactly one UTC day."""\n    y,m,d = day.year, day.month, day.day\n    url = ("https://wikimedia.org/api/rest_v1/metrics/edited-pages/top/"\n           f"en.wikipedia/all-editor-types/all-page-types/{y}/{m:02d}/{d:02d}")\n    r = requests.get(url, timeout=30); r.raise_for_status()\n    return pd.DataFrame(r.json()['items'][0]['results'])\ndef fetch_gdelt(day):\n    """Download daily GDELT file, trying both .CSV and .csv variants."""\n    ymd = day.strftime("%Y%m%d")\n    for fname in (f"{ymd}.export.CSV.zip", f"{ymd}.export.csv.zip"):\n        url = f"https://gdelt-open-data.s3.amazonaws.com/events/{fname}"\n        r = requests.get(url, timeout=60)\n        if r.status_code == 200:\n            return pd.read_csv(io.BytesIO(r.content),\n                               compression="zip", sep="\t", low_memory=False)\n    raise RuntimeError(f"GDELT file not found in S3 mirror for {ymd}")\n\n
# ------------- micro-tier: Reddit submissions ---------------------------
def fetch_reddit(day):
    """Return all Reddit *submissions* for one UTC day using Pushshift monthly dump."""
    import zstandard as zstd, json, datetime as dt, io, requests, pandas as pd
    dump = pathlib.Path(f"RS_{day:%Y-%m}.zst")
    if not dump.exists():
        url = f"https://files.pushshift.io/reddit/submissions/full/{dump.name}"
        print("↓ downloading", dump.name)
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(dump,'wb') as f:
                for chunk in r.iter_content(2**20):
                    f.write(chunk)
    rows=[]
    with open(dump,'rb') as fh, zstd.ZstdDecompressor().stream_reader(fh) as zr:
        for line in io.TextIOWrapper(zr, encoding='utf-8'):
            j=json.loads(line)
            if dt.datetime.utcfromtimestamp(j['created_utc']).date()==day:
                rows.append({
                    'id':j['id'],
                    'utc':j['created_utc'],
                    'author':j['author'],
                    'sub':j['subreddit'],
                    'title':j.get('title',''),
                    'self':j.get('selftext','')
                })
    return pd.DataFrame(rows)

