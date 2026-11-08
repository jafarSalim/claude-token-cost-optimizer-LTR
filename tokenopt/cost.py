"""Cost of one request.

    cost = (N_in p_in + N_w5 p_w5 + N_w1h p_w1h + N_r p_r + N_out p_out) / 10^6
"""
from dataclasses import dataclass, field
from .pricing import prices, BATCH_DISCOUNT


@dataclass
class Usage:
    input: int = 0          # uncached input tokens
    write5m: int = 0        # tokens written to a 5-minute cache
    write1h: int = 0        # tokens written to a 1-hour cache
    read: int = 0           # tokens read from cache
    output: int = 0

    @property
    def prompt(self):
        return self.input + self.write5m + self.write1h + self.read

    def __add__(self, o):
        return Usage(self.input + o.input, self.write5m + o.write5m, self.write1h + o.write1h,
                     self.read + o.read, self.output + o.output)


def cost(model, u: Usage, batch=False):
    p_in, p_w5, p_w1, p_r, p_out = prices(model, u.prompt)
    c = (u.input * p_in + u.write5m * p_w5 + u.write1h * p_w1 + u.read * p_r + u.output * p_out) / 1e6
    return c * (BATCH_DISCOUNT if batch else 1)


def breakeven_reuses(write_mult, read_mult):
    """Smallest number of requests n sharing a prefix where caching is cheaper.

    no cache: n P p        cache: w P p + (n - 1) r P p
    cheaper when n > (w - r) / (1 - r)
    """
    import math
    x = (write_mult - read_mult) / (1 - read_mult)
    return math.floor(x) + 1
