#!/usr/bin/env python3
import sys, pandas as pd

tl_csv, wiki_parq, out_csv = sys.argv[1:]

tl = pd.read_csv(tl_csv, parse_dates=['first','last'])

wiki_df = pd.read_parquet(wiki_parq)
if len(wiki_df):
    wiki = (wiki_df.assign(first=pd.to_datetime(wiki_df.ts))
                      .groupby('motif', as_index=False)['first'].min())
    wiki['tier'] = 'meso'
    df = pd.concat([tl[['motif','tier','first']], wiki], ignore_index=True)
else:
    df = tl[['motif','tier','first']]

# ensure first-column is datetime
df['first'] = pd.to_datetime(df['first'])

wide = df.pivot(index='motif', columns='tier', values='first')

def lag(a, b):
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
