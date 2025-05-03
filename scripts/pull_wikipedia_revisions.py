#!/usr/bin/env python3
import sys, csv, re, requests, datetime as dt, pathlib, pandas as pd
timeline_csv, outparq = map(pathlib.Path, sys.argv[1:])
motifs=set(pd.read_csv(timeline_csv).motif.unique())
def revs(title):
    url=f"https://en.wikipedia.org/w/index.php?title={title}&action=history&limit=500&offset=&dir=prev"
    html=requests.get(url,timeout=30).text
    return re.findall(r'data-timestamp="([^"]+)"',html)
rows=[]
for m in motifs:
    r=revs(m.capitalize())
    for ts in r:
        rows.append([m,dt.datetime.fromisoformat(ts.replace('Z','+00:00'))])
pd.DataFrame(rows,columns=['motif','ts']).to_parquet(outparq,compression='zstd')
