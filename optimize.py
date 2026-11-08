"""Compares saving strategies for your own chat workload.

    python optimize.py workloads/support_chatbot.json
"""
import json, sys
from dataclasses import replace
from tokenopt.simulate import Chat, total
from tokenopt.pricing import PRICES

w = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "workloads/support_chatbot.json"))
per_month = w.pop("chats_per_day") * w.pop("days", 30)
c = Chat(**w)
if c.model not in PRICES:
    sys.exit(f"Unknown model {c.model}. Choose from: {', '.join(PRICES)}")
options = {
    "As is": c,
    "Prompt caching": replace(c, cache=True),
    "Caching + compaction every 10 turns": replace(c, cache=True, compact_every=10),
    "Caching + sliding window (6 turns)": replace(c, cache=True, window=6),
    "Sliding window (6 turns), no caching": replace(c, window=6),
    "Caching on Haiku 5.5": replace(c, cache=True, model="Claude Haiku 5.5"),
}
base = total(c) * per_month
print(f"\n{c.model}, {c.turns} turns, {per_month:,} chats a month\n")
print(f"{'Option':40s}{'USD / month':>14s}{'Saving':>10s}")
for name, cfg in sorted(options.items(), key=lambda kv: total(kv[1])):
    m = total(cfg) * per_month
    print(f"{name:40s}{m:>14,.2f}{100 * (1 - m / base):>9.1f}%")
print("\nHaiku 5.5 is a smaller model: check that its answers are good enough for your task before switching.")
