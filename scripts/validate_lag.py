#!/usr/bin/env python3
"""
Compute time-lags (seconds) between tiers for every motif that appears in ≥2 tiers.

usage: validate_lag.py timelines.csv wikipedia_revisions.parquet output.csv
"""
import sys, pandas as pd
tl_csv, wiki_parq, out_csv = sys.argv[1:]

# timelines: motif,tier,first,last,rows
tl  = pd.read_csv(tl_csv, parse_dates=['first','last'])
wiki = pd.read_parquet(wiki_parq)   # motif, ts
wiki['tier']  = 'meso'
wiki.rename(columns={'ts':'first'}, inplace=True)
wiki = wiki.groupby('motif',as_index=False)['first'].min()[['motif','tier','first']]

# merge micro, meso, macro earliest times
early = (pd.concat([tl[['motif','tier','first']], wiki], ignore_index=True)
           .pivot_table(index='motif', columns='tier', values='first', aggfunc='min'))

def lag(a,b):                       # seconds b-after-a (NaN if any missing)
    return (early[b] - early[a]).dt.total_seconds()

res = pd.DataFrame({
    'motif': early.index,
    'micro→meso':  lag('micro','meso'),
    'micro→macro': lag('micro','macro'),
    'meso→macro':  lag('meso','macro')
}).dropna(how='all', subset=['micro→meso','micro→macro','meso→macro'])

res.to_csv(out_csv, index=False)
print("✓ lags written →", out_csv, "| rows:", len(res))
