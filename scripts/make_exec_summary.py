#!/usr/bin/env python3
import sys, pathlib, datetime as dt, textwrap

narrative_md, inference_md, out_md = map(pathlib.Path, sys.argv[1:])
body  = narrative_md.read_text()
table = inference_md.read_text()

out_md.write_text(textwrap.dedent(f"""\
    # Executive Summary  
    *Generated {dt.date.today()}*

    ## Key cross-tier motifs  
    <details><summary>Ranked table</summary>

    {table}

    </details>

    ## Narrative synthesis  
    {body}
    """))
print("✓ executive summary →", out_md)
