#!/usr/bin/env python
"""
24 h ingest: GDELT · Wikipedia · Mastodon
Run:   python ingest_day.py YYYY-MM-DD   # UTC date
Output: data/<source>/YYYY-MM-DD.parquet
"""
import sys, pathlib, subprocess, datetime as dt, time, zipfile, shutil, gzip, bz2, json, duckdb
from mastodon import Mastodon, StreamListener

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA, TMP = ROOT/'data', ROOT/'tmp_ingest'
DATA.mkdir(exist_ok=True); TMP.mkdir(exist_ok=True)

CONN = duckdb.connect(str(ROOT/'collective.db'))
CONN.execute("PRAGMA threads=4; SET memory_limit='4GB'")

INST="https://mastodon.social"
TOKEN="bX687CvtzRoR-NpERAoUGhfO5hsf27S8eTdgyHnx7-M"
SNAPSHOT="2025-03"                              # latest Wikimedia snapshot

def curl(url: str, dest: pathlib.Path) -> bool:
    r = subprocess.run(["curl","-sS","--http1.1","-L","--fail",
                        "--retry","3","--retry-delay","5",
                        "--output",str(dest),str(url)])
    return r.returncode == 0 and dest.stat().st_size

# ── GDELT ───────────────────────────────────────────────────────────
def ingest_gdelt(day: dt.datetime):
    zip_fp = TMP/'gdelt.zip'; tsv = TMP/'gdelt.tsv'
    if not curl(f"http://data.gdeltproject.org/events/{day:%Y%m%d}.export.CSV.zip", zip_fp):
        print("⚠  GDELT ZIP missing"); return
    with zipfile.ZipFile(zip_fp) as z:
        member = z.namelist()[0]
        with z.open(member) as src, tsv.open('wb') as dst: dst.write(src.read())
    CONN.execute(f"CREATE OR REPLACE TEMP VIEW g AS SELECT * FROM read_csv_auto('{tsv}', delim='\\t')")
    out = DATA/'gdelt'/f"{day:%Y-%m-%d}.parquet"; out.parent.mkdir(exist_ok=True)
    CONN.execute(f"COPY g TO '{out}' (FORMAT PARQUET)")
    zip_fp.unlink(); tsv.unlink()
    print("✓ GDELT done")

# ── Wikipedia ───────────────────────────────────────────────────────
def ingest_wiki(day: dt.datetime):
    if (dt.datetime.now(dt.timezone.utc) - day).days < 60:
        # --- EventStreams (recent) ---
        base="https://stream.wikimedia.org/v2/stream/revision-create"
        json_files=[]
        for h in range(24):
            since=int(day.replace(hour=h).timestamp()); until=since+3600
            fp=TMP/f"w{h:02d}.json"
            if curl(f"{base}?since={since}&until={until}",fp): json_files.append(str(fp))
        if not json_files: print("⚠ EventStreams unavailable"); return
        flist=",".join(f"'{p}'" for p in json_files)
        CONN.execute(f"""CREATE OR REPLACE TEMP VIEW w AS
                         SELECT *, json_extract(meta,'$.domain') AS wiki
                         FROM read_json_auto([{flist}])""")
        for p in json_files: pathlib.Path(p).unlink()
    else:
        # --- Monthly dump slice (historical) ---
        bz2_fp = TMP/f"{SNAPSHOT}.enwiki.{day:%Y-%m}.tsv.bz2"
        url = f"https://dumps.wikimedia.org/other/mediawiki_history/{SNAPSHOT}/enwiki/{bz2_fp.name}"
        if not curl(url, bz2_fp): print("⚠ Wiki dump missing"); return
        tsv = TMP/'wiki.tsv'
        with bz2.open(bz2_fp,'rb') as src, tsv.open('wb') as dst: shutil.copyfileobj(src,dst)
        CONN.execute(f"CREATE OR REPLACE TEMP VIEW w_raw AS "
                     f"SELECT * FROM read_csv_auto('{tsv}', delim='\\t', header=True)")
        cols = [row[1] for row in CONN.execute("PRAGMA table_info('w_raw')").fetchall()]
        ts_col = next((c for c in cols if c.endswith('_timestamp')), None)
        if ts_col is None: print("⚠ No *_timestamp column"); bz2_fp.unlink(); tsv.unlink(); return
        s=day.strftime('%Y-%m-%d 00:00:00'); e=(day+dt.timedelta(days=1)).strftime('%Y-%m-%d 00:00:00')
        CONN.execute(f"""CREATE OR REPLACE TEMP VIEW w AS
                         SELECT *, to_timestamp({ts_col}) AS ts FROM w_raw
                         WHERE ts >= '{s}' AND ts < '{e}'""")
        bz2_fp.unlink(); tsv.unlink()
    rows = CONN.execute("SELECT COUNT(*) FROM w").fetchone()[0]
    out  = DATA/'wiki'/f"{day:%Y-%m-%d}.parquet"; out.parent.mkdir(exist_ok=True)
    CONN.execute(f"COPY w TO '{out}' (FORMAT PARQUET)")
    print(f"✓ Wikipedia done ({rows} rows)")

# ── Mastodon ────────────────────────────────────────────────────────
def ingest_mastodon(day: dt.datetime):
    out = DATA/'mastodon'/f"{day:%Y-%m-%d}.parquet"; out.parent.mkdir(exist_ok=True)
    if day.date()==dt.datetime.now(dt.timezone.utc).date():   # live
        stop=day+dt.timedelta(days=1); jl=TMP/'live.jsonl'; cnt=0
        api=Mastodon(api_base_url=INST, access_token=TOKEN, ratelimit_method='wait')
        with jl.open('w',encoding='utf-8') as f:
            class L(StreamListener):
                def on_update(self,s):
                    nonlocal cnt
                    if s['created_at']>=stop: raise SystemExit
                    f.write(json.dumps(s)+'\\n'); cnt+=1
            api.stream_public(listener=L(), run_async=False)
        CONN.execute(f"CREATE OR REPLACE TEMP VIEW m AS SELECT * FROM read_json_auto('{jl}')")
        CONN.execute(f"COPY m TO '{out}' (FORMAT PARQUET)"); jl.unlink()
        print(f"✓ Mastodon live ({cnt})"); return
    gz=TMP/'m.gz'; jl=TMP/'m.jsonl'
    ia=f"https://archive.org/download/mastodon-public-{day:%Y-%m-%d}/mastodon-public-{day:%Y-%m-%d}.json.gz"
    if not curl(ia,gz): print("⚠ Mastodon archive missing"); return
    with gzip.open(gz,'rb') as src, jl.open('wb') as dst: shutil.copyfileobj(src,dst)
    CONN.execute(f"CREATE OR REPLACE TEMP VIEW m AS SELECT * FROM read_json_auto('{jl}')")
    rows=CONN.execute("SELECT COUNT(*) FROM m").fetchone()[0]
    CONN.execute(f"COPY m TO '{out}' (FORMAT PARQUET)"); gz.unlink(); jl.unlink()
    print(f"✓ Mastodon archive ({rows})")

# ── orchestrator ────────────────────────────────────────────────────
def main():
    if len(sys.argv)!=2: sys.exit("Usage: ingest_day.py YYYY-MM-DD")
    day=dt.datetime.strptime(sys.argv[1],'%Y-%m-%d').replace(tzinfo=dt.timezone.utc)
    try:
        ingest_gdelt(day); ingest_wiki(day); ingest_mastodon(day)
        print("✔ Finished", day.date())
    finally:
        shutil.rmtree(TMP, ignore_errors=True)

if __name__=="__main__": main()
