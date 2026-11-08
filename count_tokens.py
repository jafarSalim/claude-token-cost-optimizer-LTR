"""Exact input tokens and cost of a prompt, from the official token counting endpoint.

Needs your own API key:  export ANTHROPIC_API_KEY=...   pip install anthropic
    python count_tokens.py prompt.txt --model claude-sonnet-5-5 --name "Claude Sonnet 5.5"
Token counting is free. Not tested here, because this project was built without an API key.
"""
import argparse
import anthropic
from tokenopt.pricing import PRICES

ap = argparse.ArgumentParser()
ap.add_argument("file")
ap.add_argument("--model", default="claude-sonnet-5-5", help="API model id")
ap.add_argument("--name", default="Claude Sonnet 5.5", help="Name in tokenopt/pricing.py")
ap.add_argument("--system", default=None, help="Optional system prompt file")
a = ap.parse_args()
text = open(a.file, encoding="utf8").read()
kw = dict(model=a.model, messages=[{"role": "user", "content": text}])
if a.system:
    kw["system"] = open(a.system, encoding="utf8").read()
n = anthropic.Anthropic().messages.count_tokens(**kw).input_tokens
p_in, p_w5, _, p_r, _ = PRICES[a.name]
print(f"Input tokens: {n:,}")
print(f"Cost per request, no cache:   ${n * p_in / 1e6:.5f}")
print(f"Cost per request, cache read: ${n * p_r / 1e6:.5f}")
print(f"Characters per token: {len(text) / max(n, 1):.2f}")
