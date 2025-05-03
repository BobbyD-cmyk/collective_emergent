#!/usr/bin/env python3
"""
Compute lag (in seconds) between tiers for each motif that appears
in at least two of the three layers.

usage:
    validate_lag.py timelines.csv wikipedia_revisions.parquet output.csv
"""
import sys, pandas as pd

tl_csv, wiki_parq, out_csv = sys.argv[1:]

# timelines.csv  → motif,tier,first,last,rows
tl = pd.read_csv(tl_csv, parse_dates=['first','last'])

# wikipedia revisions → motif, ts
wiki = pd.read_parquet(wiki_parq)
wiki['first'] = pd.to_datetime(wiki['ts'])
wiki = wiki.groupby('motif', as_index=False)['first'].min()
wiki['tier'] = 'meso'

# merge earliest timestamps per tier
df   = pd.concat([tl[['motif','tier','first']], wiki[['motif','tier','first']]],
                 ignore_index=True)
wide = df.pivot(index='motif', columns='tier', values='first')

def lag(a, b):
    return (wide[b] - wide[a]).dt.total_seconds()

out = pd.DataFrame({
    'motif': wide.index,
    'micro→meso':  lag('micro', 'meso'),
    'micro→macro': lag('micro', 'macro'),
    'meso→macro':  lag('meso',  'macro')
}).dropna(how='all', subset=['micro→meso','micro→macro','meso→macro'])

out.to_csv(out_csv, index=False)
print("✓ lags written →", out_csv, "| rows:", len(out))
