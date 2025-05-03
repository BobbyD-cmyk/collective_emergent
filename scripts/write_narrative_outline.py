#!/usr/bin/env python3
import sys, pathlib, pickle, datetime as dt
graph=pickle.load(open(sys.argv[1]+'/closure_graph.gpickle','rb'))
out  = pathlib.Path(sys.argv[2]); out.parent.mkdir(parents=True,exist_ok=True)
with open(out,'w') as f:
    f.write("# Narrative outline — "+dt.date.today().isoformat()+"\n\n")
    for (u,v),tier in graph.edges(data='tier'):
        token=u.split(':',1)[1]
        f.write(f"* **{token}**  –  cross-tier: {tier}\n")
print("outline written →",out)
