import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tokenopt.cost import Usage, cost, breakeven_reuses
from tokenopt.simulate import Chat, run, total


def test_price_formula():
    u = Usage(input=1_000_000, output=1_000_000)
    assert abs(cost("Claude Sonnet 5.5", u) - 12.0) < 1e-9
    assert abs(cost("Claude Sonnet 5.5", u, batch=True) - 6.0) < 1e-9


def test_haiku_long_prompt_tier():
    short = cost("Claude Haiku 5.5", Usage(input=100_000))
    long_ = cost("Claude Haiku 5.5", Usage(input=100_001))
    assert long_ / short > 4.9


def test_breakeven():
    assert breakeven_reuses(1.25, 0.1) == 2
    assert breakeven_reuses(2.0, 0.1) == 3


def test_history_grows_quadratically():
    c = Chat(turns=10, tools=0, system=0, user=100, reply=100)
    tokens = sum(r["usage"].prompt for r in run(c))
    T, u, a = 10, 100, 100
    assert tokens == T * u + (u + a) * T * (T - 1) // 2


def test_cache_reads_previous_prompt():
    r = run(Chat(turns=3, cache=True))
    assert r[0]["usage"].read == 0
    assert r[1]["usage"].read == 2000 + 3000 + 150
    assert r[1]["usage"].write5m == 400 + 150


def test_caching_saves_money():
    assert total(Chat(cache=True)) < total(Chat())
