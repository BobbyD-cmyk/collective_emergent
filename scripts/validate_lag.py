#!/usr/bin/env python3
import sys, pandas as pd

tl_csv, wiki_parq, out_csv = sys.argv[1:]

tl   = pd.read_csv(tl_csv, parse_dates=['first','last'])
wiki = pd.read_parquet(wiki_parq)
if len(wiki):
    wiki = (wiki.assign(first=pd.to_datetime(wiki.ts))
                 .groupby('motif',as_index=False)['first'].min()
                 .assign(tier='meso'))
    df = pd.concat([tl[['motif','tier','first']], wiki], ignore_index=True)
else:
    df = tl[['motif','tier','first']]

wide = df.pivot(index='motif', columns='tier', values='first')

def safe_lag(a,b):
    return (wide[b] - wide[a]).dt.total_seconds() if a in wide and b in wide else None

out = pd.DataFrame({
    'motif': wide.index,
    'micro→meso':  safe_lag('micro','meso'),
    'micro→macro': safe_lag('micro','macro'),
    'meso→macro':  safe_lag('meso','macro')
})

out.to_csv(out_csv, index=False)
print("✓ lags written →", out_csv, "| rows:", len(out))
