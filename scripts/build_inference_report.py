#!/usr/bin/env python3
"""
Produce docs/step6_inference.md:
• rank motifs by shortest micro→macro lag
• report degree-centrality in the closure graph
• embed timeline statistics
"""
import pathlib, pickle, pandas as pd, networkx as nx, datetime as dt, textwrap

BASE   = pathlib.Path('data/raw/2023-10-07')
GRAPH  = pickle.load(open(BASE/'closure_graph.gpickle','rb'))
LAGS   = pd.read_csv('docs/step5_validation.csv')
TLINES = pd.read_csv('timelines.csv')

deg = pd.Series(dict(GRAPH.degree()), name='deg')
deg.index = deg.index.str.split(':',1).str[1]          # strip tier prefix

inf = (LAGS.merge(deg, left_on='motif', right_index=True, how='left')
            .sort_values('micro_to_macro_s')
            .reset_index(drop=True))

out = pathlib.Path('docs/step6_inference.md')
with open(out,'w') as f:
    f.write("# Step 6 – Inferential synthesis\n\n")
    f.write(f"*Generated {dt.date.today()}*\n\n")
    f.write("| rank | motif | micro→macro s | degree |\n|---|---|---|---|\n")
    for i,row in inf.iterrows():
        f.write(f"| {i+1} | **{row.motif}** | {int(row.micro_to_macro_s) if pd.notna(row.micro_to_macro_s) else '—'} | {row.deg} |\n")
    f.write("\n---\n\n")
    f.write("## Notes\n")
    f.write(textwrap.dedent("""\
        * Motifs are ranked by the fastest micro→macro propagation.
        * Degree = total cross-tier connections in the closure graph.
        * Use these rankings to prioritise qualitative narrative expansion.
        """))
print("✓ inference report →", out)
