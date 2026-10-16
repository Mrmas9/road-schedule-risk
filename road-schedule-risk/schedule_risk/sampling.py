"""Sampling activity durations from three-point estimates."""

import numpy as np


def triangular(rng, low, mode, high, iterations):
    return rng.triangular(low, mode, high, size=(iterations, len(low)))


def pert(rng, low, mode, high, iterations, weight=4.0):
    """Beta-PERT: same three points, smoother shape, thinner tails than the triangular."""
    span = high - low
    alpha = 1 + weight * (mode - low) / span
    beta = 1 + weight * (high - mode) / span
    return low + rng.beta(alpha, beta, size=(iterations, len(low))) * span


SAMPLERS = {"triangular": triangular, "pert": pert}
