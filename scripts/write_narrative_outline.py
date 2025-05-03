#!/usr/bin/env python3
import sys, pathlib, pickle, datetime as dt
folder, outfile = map(pathlib.Path, sys.argv[1:])
G=pickle.load(open(folder/'closure_graph.gpickle','rb'))
with open(outfile,'w') as f:
    f.write("# Narrative outline — "+dt.date.today().isoformat()+"\n\n")
    for (u,v),tier in G.edges(data='tier'):
        tok=u.split(':',1)[1]
        f.write(f"* **{tok}**  –  cross-tier: {tier}\n")
print("outline written →", outfile)
