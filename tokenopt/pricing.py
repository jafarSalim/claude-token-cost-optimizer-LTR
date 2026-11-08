"""Claude API prices in USD per million tokens.

Source: https://platform.claude.com/docs/en/about-claude/pricing
Retrieved 2026-11-09. Prices change, so check the source before relying on them.
Columns: input, 5-minute cache write, 1-hour cache write, cache read, output.
"""
SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing"
RETRIEVED = "2026-11-09"

PRICES = {
    "Claude Fable 5.1": (10, 12.50, 20, 0.25, 50),
    "Claude Mythos 5.1": (10, 12.50, 20, 0.25, 50),
    "Claude Opus 5.5": (4, 5, 8, 0.20, 20),
    "Claude Sonnet 5.5": (2, 2.50, 4, 0.10, 10),
    "Claude Haiku 5.5": (0.10, 0.125, 0.20, 0.01, 0.50),
    "Claude Opus 5": (5, 6.25, 10, 0.50, 25),
    "Claude Sonnet 5": (2, 2.50, 4, 0.20, 10),
    "Claude Opus 4.8": (5, 6.25, 10, 0.50, 25),
    "Claude Sonnet 4.6": (3, 3.75, 6, 0.30, 15),
    "Claude Haiku 4.5": (1, 1.25, 2, 0.10, 5),
    "Claude Opus 4.1": (15, 18.75, 30, 1.50, 75),
}
# Haiku 5.5 charges more when a single prompt is over 100,000 tokens (all input counted)
HAIKU55_LONG = (0.50, 0.625, 1, 0.05, 2.50)

# Smallest prompt that can be cached
MIN_CACHE = {"Claude Fable 5.1": 512, "Claude Mythos 5.1": 512, "Claude Opus 5.5": 512, "Claude Sonnet 5.5": 512,
             "Claude Haiku 5.5": 512, "Claude Opus 5": 512, "Claude Sonnet 5": 1024, "Claude Opus 4.8": 1024,
             "Claude Sonnet 4.6": 1024, "Claude Haiku 4.5": 4096, "Claude Opus 4.1": 1024}

CURRENT = ["Claude Fable 5.1", "Claude Opus 5.5", "Claude Sonnet 5.5", "Claude Haiku 5.5"]
BATCH_DISCOUNT = 0.5


def prices(model, prompt_tokens=0):
    if model == "Claude Haiku 5.5" and prompt_tokens > 100_000:
        return HAIKU55_LONG
    return PRICES[model]
