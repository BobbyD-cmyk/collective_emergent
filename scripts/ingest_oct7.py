#!/usr/bin/env python3
import datetime as dt, pathlib, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW  = ROOT / "data" / "raw" / "2023-10-07"
RAW.mkdir(parents=True, exist_ok=True)
DAY  = dt.date(2023, 10, 7)

# ── micro ▸ Mastodon (OSoMe BigQuery, anonymous creds) ───────────────────────
def ingest_mastodon():
    from google.oauth2 import anonymous_credentials
    import pandas_gbq as gbq
    q = f"""
      SELECT  id,
              created_at,
              account.acct                          AS acct,
              lang,
              REGEXP_REPLACE(content, '<[^>]+>', '') AS content,
              ARRAY_TO_STRING(hashtags, ',')        AS hashtags
      FROM   `osome_mastodon.toots`
      WHERE  DATE(created_at) = '{DAY:%Y-%m-%d}'
    """
    creds = anonymous_credentials.AnonymousCredentials()
    df = gbq.read_gbq(q, project_id="bigquery-public-data",
                      credentials=creds, progress_bar_type=None)
    df.to_parquet(RAW/"mastodon.parquet", compression="zstd", engine="fastparquet")
    print("✓ mastodon.parquet rows =", len(df))

# ── meso ▸ Wikipedia edited pages (new daily endpoint) ───────────────────────
def ingest_wikipedia():
    import requests
    url = ("https://wikimedia.org/api/rest_v1/metrics/edited-pages/top/"
           "en.wikipedia/all-editor-types/all-page-types/daily/20231007/20231007")
    df  = pd.DataFrame(requests.get(url, timeout=30).json()['rows'])
    df.to_parquet(RAW/"wikipedia.parquet", compression="zstd", engine="fastparquet")
    print("✓ wikipedia.parquet rows =", len(df))

def main():
    ingest_mastodon()
    ingest_wikipedia()
    # gdelt.parquet already exists; verify presence
    g = RAW/"gdelt.parquet"
    if g.exists():
        print("✓ gdelt.parquet present (macro tier)")
    else:
        print("⚠ gdelt.parquet missing – copy the 5.9 MB file here before Step 3")

if __name__ == "__main__":
    main()
