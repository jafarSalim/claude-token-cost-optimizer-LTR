"""Turn-by-turn simulation of a chat conversation.

Each request sends: tools + system + history + new user message.
With caching, a breakpoint sits at the end of the system prompt and at the end
of the newest message. A request reads the longest prefix already cached and
writes everything after it. Turns are assumed to arrive inside the cache lifetime.
"""
from dataclasses import dataclass, replace
from .cost import Usage, cost
from .pricing import MIN_CACHE


@dataclass
class Chat:
    model: str = "Claude Sonnet 5.5"
    tools: int = 2000
    system: int = 3000
    user: int = 150
    reply: int = 400
    turns: int = 20
    cache: bool = False
    window: int = 0            # keep only the last N turns of history (0 = all)
    compact_every: int = 0     # summarize history every N turns (0 = never)
    summary: int = 600
    compact_prompt: int = 60


def _prefix_len(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += x[1]
    return n


def run(c: Chat):
    """Returns a list of per-request dicts: kind, usage, cost and token parts."""
    base = [("tools", c.tools), ("system", c.system)]
    history, out, cached = [], [], []
    seq = 0

    def request(prompt, output, kind, turn):
        nonlocal cached
        total = sum(t for _, t in prompt)
        u = Usage(output=output)
        if c.cache:
            read = max([_prefix_len(p, prompt) for p in cached if len(p) <= len(prompt)] + [0])
            if total >= MIN_CACHE[c.model]:
                u.read, u.write5m = read, total - read
                for p in (base, prompt):
                    if sum(t for _, t in p) >= MIN_CACHE[c.model] and p not in cached:
                        cached.append(list(p))
            else:
                u.input = total
        else:
            u.input = total
        hist = sum(t for k, t in prompt if k.startswith(("u", "a", "s")) and k != "system")
        out.append(dict(kind=kind, turn=turn, usage=u, cost=cost(c.model, u),
                        parts=dict(tools=c.tools, system=c.system, history=hist - prompt[-1][1] if kind == "turn" else hist,
                                   new=prompt[-1][1] if kind == "turn" else c.compact_prompt, output=output)))

    for t in range(1, c.turns + 1):
        if c.compact_every and t > 1 and (t - 1) % c.compact_every == 0:
            seq += 1
            request(base + history + [(f"cmp{seq}", c.compact_prompt)], c.summary, "compact", t)
            history = [(f"sum{seq}", c.summary)]
        seq += 1
        msg = (f"u{seq}", c.user)
        hist = history if not c.window else history[-2 * c.window:]
        request(base + hist + [msg], c.reply, "turn", t)
        history = history + [msg, (f"a{seq}", c.reply)]
    return out


def total(c: Chat):
    return sum(r["cost"] for r in run(c))
