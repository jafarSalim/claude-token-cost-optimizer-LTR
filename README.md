<div align="center">

# Claude Token Cost Optimizer

### Cut your Claude API bill by up to 91% with caching, batching, compaction and routing, with the math to prove it

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Excel](https://img.shields.io/badge/Excel-live%20formulas%20%2B%20charts-217346?logo=microsoftexcel&logoColor=white)
![Claude](https://img.shields.io/badge/Claude%20API-pricing%20Nov%202026-D97757)
![Tests](https://img.shields.io/badge/Tests-passing-2ea44f)
![Formulas](https://img.shields.io/badge/Excel%20formulas-1%2C000%2B%2C%200%20errors-blue)

![Overview](results/overview.png)

</div>

> Every chart below is a **native Excel chart** from [`excel/claude_token_costs.xlsx`](excel/claude_token_costs.xlsx). Change any blue input cell and every table and chart updates.

## Contents

- [The problem](#the-problem)
- [Key results](#key-results)
- [The math](#the-math)
- [Which saving should I use?](#which-saving-should-i-use)
- [Result gallery](#result-gallery)
- [Run it](#run-it)
- [Project layout](#project-layout)
- [Limits](#limits)

## The problem

The Claude API is stateless, so a chat resends its **whole history on every turn**. Cost per turn grows with the turn number, and cost per chat grows with its square. Most of the bill is text the model has already seen.

| Where the tokens go | Where the money goes |
|---|---|
| ![Tokens](results/donut_tokens.png) | ![Cost](results/donut_cost.png) |

In one 20-turn support chat, history, tools and the system prompt make up **95% of the tokens**. Replies are only 4% of tokens, but **16% of the cost**, because output costs 5× input.

## Key results

Scenario: a support chatbot on Claude Sonnet 5.5, with 2,000 tokens of tool definitions, a 3,000-token system prompt, 150-token questions, 400-token replies, 20 turns per chat and 1,000 chats a day.

![Waterfall](results/waterfall.png)

| Step | USD per month | Change |
|---|---:|---:|
| Baseline | 14,850 | |
| + Prompt caching | 4,146 | **−72%** |
| + Compact history every 10 turns | 4,258 | +3% |
| + Shorter replies, 400 → 250 tokens | 3,108 | −27% |
| + Send 60% of chats to Haiku 5.5 | **1,349** | −57% |

What this shows:

- **Prompt caching is the biggest single win**, at 72% off, and needs no change to what the model sees.
- **Compaction did not pay at 20 turns:** it cost 3% more, because the summary call and the cache rewrite cost more than they saved. Over 40 turns it is slightly cheaper.
- **A sliding window and caching fight each other.** Dropping old turns changes the prefix, so the cache misses. Over 40 turns, caching alone costs $287 per 1,000 chats, and caching with a 6-turn window costs $486.
- **The 5-minute cache pays from the 2nd request, and the 1-hour cache from the 3rd.**
- Routing to Haiku 5.5 saves the most of all, but only if its answers are good enough for the task.

## The math

**Cost of one request.** All prices are in USD per million tokens:

$$C = \frac{N_{in}\,p_{in} + N_{w}\,p_{w} + N_{r}\,p_{r} + N_{out}\,p_{out}}{10^6}$$

**History grows quadratically.** With a fixed prefix $S$, user message $u$ and reply $a$, the input tokens over $T$ turns are:

$$N_{in}(T) = \sum_{t=1}^{T}\big(S + (t-1)(u+a) + u\big) = T(S+u) + (u+a)\frac{T(T-1)}{2}$$

**With caching**, turn $t$ reads the previous prompt and writes only the new part:

$$N_r(t) = S + (t-2)(u+a) + u, \qquad N_w(t) = u + a$$

**Break-even for caching.** A prefix of $P$ tokens shared by $n$ requests, with write multiplier $w$ and read multiplier $r$:

$$\underbrace{n\,P\,p}_{\text{no cache}} \;>\; \underbrace{w\,P\,p + (n-1)\,r\,P\,p}_{\text{cache}} \iff n > \frac{w-r}{1-r}$$

For Sonnet 5.5 ($r = 0.05$): 5-minute cache ($w = 1.25$) pays from $n = 2$, and 1-hour cache ($w = 2$) from $n = 3$.

**Batch API** multiplies every price by 0.5, and it stacks with caching.

## Which saving should I use?

<p align="center"><img src="results/flowchart.png" width="420" alt="Decision flowchart"></p>

## Result gallery

### Why chats get expensive

| Cost of each turn | 40 turns, five strategies |
|---|---|
| ![Per turn](results/cost_per_turn.png) | ![Strategies](results/strategies_over_turns.png) |

### Caching

| When caching pays off | Saving by prefix size and reuse |
|---|---|
| ![Break-even](results/cache_breakeven.png) | ![Heatmap](results/caching_heatmap.png) |

Caching loses money only when a prefix is used once, because writing costs 1.25×. With a 100,000-token prefix shared by 100 requests, it saves 92%.

### Models and batch jobs

| Same chat on each model | Claude price map |
|---|---|
| ![Models](results/model_costs.png) | ![Price map](results/price_map.png) |

![Offline job](results/batch_and_cache.png)

An offline job of 10,000 documents drops from $190 to $95 with the Batch API and to $65 with batch plus caching. Cache hits inside batches are best effort, and the docs report 30% to 98%, so the last bar is an upper bound.

### Prices used

| Model | Input | 5-min write | 1-hour write | Cache read | Output |
|---|---:|---:|---:|---:|---:|
| Fable 5.1 | $10 | $12.50 | $20 | $0.25 | $50 |
| Opus 5.5 | $4 | $5 | $8 | $0.20 | $20 |
| Sonnet 5.5 | $2 | $2.50 | $4 | $0.10 | $10 |
| Haiku 5.5, prompts up to 100k tokens | $0.10 | $0.125 | $0.20 | $0.01 | $0.50 |

USD per million tokens, from the [official pricing page](https://platform.claude.com/docs/en/about-claude/pricing), retrieved 9 November 2026. Prices change, so check the source.

## Run it

```bash
pip install -r requirements.txt

# Compare strategies for your own workload
python optimize.py workloads/support_chatbot.json
python optimize.py workloads/coding_agent.json

# Rebuild everything: numbers, Excel workbook, chart images
python run_analysis.py
python build_excel.py
python render_excel_charts.py     # needs LibreOffice

# Exact token count with your own key (free endpoint)
python count_tokens.py my_prompt.txt --model claude-sonnet-5-5 --name "Claude Sonnet 5.5"

pytest tests
```

Example output of `optimize.py` for the coding agent workload (Opus 5.5, 40 turns, 200 sessions a day):

```text
Option                                     USD / month    Saving
Caching on Haiku 5.5                            779.52     98.9%
Caching + compaction every 10 turns          11,010.12     84.5%
Prompt caching                               12,510.24     82.4%
Caching + sliding window (6 turns)           24,948.60     65.0%
Sliding window (6 turns), no caching         34,831.20     51.1%
As is                                        71,184.00      0.0%
```

## Project layout

```text
tokenopt/pricing.py          Official prices and cache minimums
tokenopt/cost.py             Cost of one request, break-even formula
tokenopt/simulate.py         Turn-by-turn chat simulator with caching
run_analysis.py              Runs the studies, writes results/summary.json
build_excel.py               Builds the workbook with formulas and Excel charts
render_excel_charts.py       Exports the Excel charts as PNG
optimize.py                  Strategy comparison for your workload
count_tokens.py              Exact counts through the official API
workloads/                   Example workloads
excel/claude_token_costs.xlsx
```

## Limits

- **These are cost calculations, not measured bills.** Token sizes are assumptions for a typical workload. Use `count_tokens.py` to measure yours.
- Caching assumes each turn arrives within the 5-minute cache lifetime.
- Shorter replies and routing to Haiku are what-if settings. Their effect on answer quality was not measured.
- Compaction assumes a 600-token summary, and its quality was not measured.
- `count_tokens.py` was not run here, because no API key was used to build this project.

## Author

**Jaafar Salim**, University of Technology, Iraq
