#!/usr/bin/env python3
import sys, pathlib, pandas as pd, requests, re, datetime as dt
timeline_csv, outparq = map(pathlib.Path, sys.argv[1:])
motifs=pd.read_csv(timeline_csv).motif.unique()
rows=[]
for m in motifs:
    url=f"https://en.wikipedia.org/w/index.php?title={m.capitalize()}&action=history&limit=500&dir=prev"
    html=requests.get(url,timeout=30).text
    for ts in re.findall(r'data-timestamp="([^"]+)"',html):
        rows.append([m, dt.datetime.fromisoformat(ts.replace('Z','+00:00'))])
pd.DataFrame(rows,columns=['motif','ts']).to_parquet(outparq,compression='zstd')
