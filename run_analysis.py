"""Runs the simulator and writes every number to results/summary.json.

Then build_excel.py turns them into a workbook with native Excel charts,
and render_excel_charts.py exports those charts as PNG images.
"""
import json, pathlib
from dataclasses import replace
import numpy as np
from tokenopt.pricing import CURRENT, SOURCE, RETRIEVED
from tokenopt.cost import Usage, cost, breakeven_reuses
from tokenopt.simulate import Chat, run, total

OUT = pathlib.Path("results")
OUT.mkdir(exist_ok=True)
CONV_PER_MONTH = 1000 * 30
base = Chat()

steps = [("Baseline", base)]
steps.append(("Prompt caching", replace(steps[-1][1], cache=True)))
steps.append(("Compact every 10 turns", replace(steps[-1][1], compact_every=10)))
steps.append(("Replies 400 to 250", replace(steps[-1][1], reply=250)))
per_conv = [total(c) for _, c in steps]
per_conv.append(0.6 * total(replace(steps[-1][1], model="Claude Haiku 5.5")) + 0.4 * per_conv[-1])
labels = [s[0] for s in steps] + ["60% of chats to Haiku 5.5"]


def cumulative(c):
    y = np.zeros(c.turns)
    for e in run(c):
        y[e["turn"] - 1] += e["cost"]
    return list(1000 * np.cumsum(y))


long_chat = replace(base, turns=40)
strategies = {"No caching": long_chat, "Sliding window": replace(long_chat, window=6), "Prompt caching": replace(long_chat, cache=True),
              "Caching + sliding window": replace(long_chat, cache=True, window=6), "Caching + compaction": replace(long_chat, cache=True, compact_every=10)}
P = [512, 1000, 2000, 5000, 10000, 20000, 50000, 100000]
N = [1, 2, 3, 5, 10, 20, 50, 100]
heat = []
for p in P:
    row = []
    for k in N:
        nc = k * cost("Claude Sonnet 5.5", Usage(input=p + 200, output=300))
        cc = cost("Claude Sonnet 5.5", Usage(write5m=p + 200, output=300)) + (k - 1) * cost("Claude Sonnet 5.5", Usage(read=p, write5m=200, output=300))
        row.append(round(100 * (1 - cc / nc), 1))
    heat.append(row)
summary = dict(
    source=SOURCE, retrieved=RETRIEVED, scenario=base.__dict__, conversations_per_month=CONV_PER_MONTH,
    waterfall=dict(zip(labels, [CONV_PER_MONTH * x for x in per_conv])),
    forty_turns_per_1000={k: cumulative(c)[-1] for k, c in strategies.items()},
    cumulative_compaction_per_1000=cumulative(strategies["Caching + compaction"]),
    model_monthly={m: dict(no_cache=CONV_PER_MONTH * total(replace(base, model=m)), cache=CONV_PER_MONTH * total(replace(base, model=m, cache=True))) for m in CURRENT},
    breakeven=dict(cache5m=breakeven_reuses(1.25, .05), cache1h=breakeven_reuses(2, .05)),
    heatmap=dict(prefix=P, reuses=N, saving_pct=heat))
json.dump(summary, open(OUT / "summary.json", "w"), indent=2)
print(json.dumps({k: summary[k] for k in ("waterfall", "forty_turns_per_1000", "breakeven")}, indent=1))
