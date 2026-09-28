"""Deterministic per-request sampling for stochastic OpenPI policies."""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np


POLICY_NOISE_SEED_KEY = "policy_noise_seed"
POLICY_SAMPLING_MODE = "explicit_numpy_gaussian_noise_v1"


def _require_non_negative_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise TypeError(f"{name} must be an integer")
    result = int(value)
    if result < 0:
        raise ValueError(f"{name} must be non-negative")
    return result


def make_policy_noise(seed: int, action_horizon: int, action_dim: int) -> np.ndarray:
    """Create request-local float32 Gaussian noise without shared RNG state."""

    checked_seed = _require_non_negative_integer(seed, POLICY_NOISE_SEED_KEY)
    checked_horizon = _require_non_negative_integer(action_horizon, "action_horizon")
    checked_dim = _require_non_negative_integer(action_dim, "action_dim")
    if checked_horizon == 0 or checked_dim == 0:
        raise ValueError("action_horizon and action_dim must be positive")
    rng = np.random.default_rng(checked_seed)
    return rng.standard_normal((checked_horizon, checked_dim), dtype=np.float32)


def array_sha256(array: np.ndarray) -> str:
    """Hash an array's C-order bytes for compact bit-exact evidence."""

    contiguous = np.ascontiguousarray(array)
    return hashlib.sha256(contiguous.tobytes(order="C")).hexdigest()


def policy_sampling_evidence(seed: int, action_horizon: int, action_dim: int) -> dict:
    """Return the evidence expected for one explicit-noise inference request."""

    noise = make_policy_noise(seed, action_horizon, action_dim)
    return {
        "mode": POLICY_SAMPLING_MODE,
        "seed": int(seed),
        "shape": list(noise.shape),
        "dtype": str(noise.dtype),
        "noise_sha256": array_sha256(noise),
    }


def validate_policy_sampling_evidence(
    evidence: Any,
    *,
    expected_seed: int,
    action_horizon: int,
    action_dim: int,
) -> dict:
    """Fail closed unless server evidence matches locally regenerated noise."""

    if not isinstance(evidence, dict):
        raise ValueError("policy response is missing policy_sampling evidence")
    expected = policy_sampling_evidence(expected_seed, action_horizon, action_dim)
    mismatches = {
        key: {"expected": value, "actual": evidence.get(key)}
        for key, value in expected.items()
        if evidence.get(key) != value
    }
    if mismatches:
        raise ValueError(f"policy sampling evidence mismatch: {mismatches}")
    return expected


def case_chunk_seed(case_seed: int, chunk_index: int) -> int:
    """Map an evaluation case and zero-based action chunk to a stable seed."""

    checked_case_seed = _require_non_negative_integer(case_seed, "case_seed")
    checked_chunk_index = _require_non_negative_integer(chunk_index, "chunk_index")
    return checked_case_seed + checked_chunk_index


class DeterministicRequestPolicy:
    """Pass explicit noise to OpenPI so request order cannot change a case."""

    def __init__(self, policy: Any, *, action_horizon: int, action_dim: int):
        self._policy = policy
        self._action_horizon = _require_non_negative_integer(action_horizon, "action_horizon")
        self._action_dim = _require_non_negative_integer(action_dim, "action_dim")
        if self._action_horizon == 0 or self._action_dim == 0:
            raise ValueError("action_horizon and action_dim must be positive")

    def infer(self, obs: dict) -> dict:
        request = dict(obs)
        if POLICY_NOISE_SEED_KEY not in request:
            raise KeyError(
                f"missing {POLICY_NOISE_SEED_KEY}; deterministic simulation inference requires it"
            )
        seed = request.pop(POLICY_NOISE_SEED_KEY)
        noise = make_policy_noise(seed, self._action_horizon, self._action_dim)
        result = self._policy.infer(request, noise=noise)
        if not isinstance(result, dict):
            raise TypeError("wrapped OpenPI policy must return a dictionary")
        response = dict(result)
        response["policy_sampling"] = policy_sampling_evidence(
            seed, self._action_horizon, self._action_dim
        )
        return response

    @property
    def metadata(self) -> dict:
        return self._policy.metadata
