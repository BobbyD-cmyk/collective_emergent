#!/usr/bin/env python3
import sys, pandas as pd

tl_csv, wiki_parq, out_csv = sys.argv[1:]

def make_dt(s):
    """Handle ISO strings or bare 8-digit YYYYMMDD ints."""
    s = str(s)
    if len(s) == 8 and s.isdigit():
        return pd.to_datetime(s, format="%Y%m%d")
    return pd.to_datetime(s, errors="coerce")

tl = pd.read_csv(tl_csv)
tl['first'] = tl['first'].apply(make_dt)

wiki_df = pd.read_parquet(wiki_parq)
if len(wiki_df):
    wiki = (wiki_df.assign(first=wiki_df.ts.apply(make_dt))
                     .groupby('motif', as_index=False)['first'].min())
    wiki['tier'] = 'meso'
    df = pd.concat([tl[['motif','tier','first']], wiki], ignore_index=True)
else:
    df = tl[['motif','tier','first']]

wide = df.pivot(index='motif', columns='tier', values='first')

def lag(a,b):
    if a in wide and b in wide:
        return (wide[b] - wide[a]).dt.total_seconds()
    return None

out = pd.DataFrame({
    'motif': wide.index,
    'micro_to_meso_s':  lag('micro','meso'),
    'micro_to_macro_s': lag('micro','macro'),
    'meso_to_macro_s':  lag('meso','macro')
})

out.to_csv(out_csv, index=False)
print("✓ lags written →", out_csv, "| rows:", len(out))
