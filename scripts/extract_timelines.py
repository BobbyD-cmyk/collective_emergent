#!/usr/bin/env python3
import sys, pathlib, pandas as pd, pickle, re

base, gkgf, gdeltf, graphf, outcsv = map(pathlib.Path, sys.argv[1:])

def date_col(df):
    for c in df.columns:
        if re.fullmatch(r'.*date.*', c, re.I):
            return c
        if pd.api.types.is_numeric_dtype(df[c]) and df[c].astype(str).str.len().min()==8:
            return c
    raise ValueError("no date column found")

gkg   = pd.read_parquet(base / gkgf)
gdelt = pd.read_parquet(base / gdeltf)

gkg_date   = date_col(gkg)
gdelt_date = date_col(gdelt)

motifs=set()
for u,v,_ in pickle.load(open(base/graphf,'rb')).edges(data=True):
    motifs.add(u.split(':',1)[1]); motifs.add(v.split(':',1)[1])

rows=[]
for m in motifs:
    mg=gkg[gkg.Themes.str.contains(m,case=False,na=False)]
    md=gdelt[gdelt.apply(lambda r: m in str(r.values).lower(), axis=1)]
    if len(mg): rows.append([m,'micro',mg[gkg_date].min(),mg[gkg_date].max(),len(mg)])
    if len(md): rows.append([m,'macro',md[gdelt_date].min(),md[gdelt_date].max(),len(md)])

pd.DataFrame(rows,columns=['motif','tier','first','last','rows']).to_csv(outcsv,index=False)
print("✓ timelines.csv written —", len(rows), "rows")
