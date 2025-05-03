#!/usr/bin/env python3
import sys, pandas as pd, pathlib, pickle
base, gkgf, gdeltf, graphf, outcsv = map(pathlib.Path, sys.argv[1:])
gkg   = pd.read_parquet(base / gkgf)
gdelt = pd.read_parquet(base / gdeltf)
motifs = set()
edge_tier = pickle.load(open(base/graphf,'rb')).edges(data='tier')
for u,v,t in edge_tier: motifs.add(u.split(':',1)[1]); motifs.add(v.split(':',1)[1])
rows=[]
for m in motifs:
    mg=gkg[gkg.Themes.str.contains(m,case=False,na=False)]
    md=gdelt[gdelt.apply(lambda r: m in str(r.values).lower(), axis=1)]
    if len(mg): rows.append([m,'micro',mg.Date.min(),mg.Date.max(),len(mg)])
    if len(md): rows.append([m,'macro',md.MonthYear.min(),md.MonthYear.max(),len(md)])
pd.DataFrame(rows,columns=['motif','tier','first','last','rows']).to_csv(outcsv,index=False)
