"""Small statistics layer, kept separate so it can be pointed at during Q&A.

The whole credibility argument for Portal 2 is that a feature only earns a risk
flag when the data actually supports it. Three guards do that work:

  1. minimum support  — never flag from a handful of trials
  2. shrinkage        — pull small-sample rates toward the disease base rate
  3. Wilson lower bd  — the *lower* end of the interval must still exceed base
"""
from __future__ import annotations

import math

Z95 = 1.959963985


def wilson_interval(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion. Well-behaved at n small
    and k in {0, n}, where the normal approximation is not."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, center - half), min(1.0, center + half))


def shrink(k: int, n: int, prior_rate: float, prior_weight: float = 10.0) -> float:
    """Empirical-Bayes point estimate: a Beta prior centred on the disease-wide
    base rate, worth `prior_weight` pseudo-trials. With n=3 you get roughly the
    base rate back; by n=40 the observed rate dominates."""
    if n <= 0:
        return prior_rate
    return (k + prior_weight * prior_rate) / (n + prior_weight)


def logit(p: float, eps: float = 1e-6) -> float:
    p = min(max(p, eps), 1 - eps)
    return math.log(p / (1 - p))


def inv_logit(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))
