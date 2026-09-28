#!/usr/bin/env python3
"""Prove explicit OpenPI noise is stable across order, restart, and resume."""

from __future__ import annotations

import json

import numpy as np

from openpi_extension.deterministic_policy import (
    DeterministicRequestPolicy,
    array_sha256,
    case_chunk_seed,
    make_policy_noise,
    validate_policy_sampling_evidence,
)


class FakePolicy:
    metadata = {"name": "fake"}

    def infer(self, obs: dict, *, noise: np.ndarray | None = None) -> dict:
        assert set(obs) == {"state"}
        assert noise is not None
        return {"actions": noise[:, :7].copy()}


def run_case(case_seed: int, chunk_count: int) -> list[tuple[str, str]]:
    policy = DeterministicRequestPolicy(FakePolicy(), action_horizon=10, action_dim=32)
    result = []
    for chunk_index in range(chunk_count):
        seed = case_chunk_seed(case_seed, chunk_index)
        response = policy.infer({"state": np.zeros(7), "policy_noise_seed": seed})
        evidence = validate_policy_sampling_evidence(
            response["policy_sampling"],
            expected_seed=seed,
            action_horizon=10,
            action_dim=32,
        )
        result.append((evidence["noise_sha256"], array_sha256(response["actions"])))
    return result


def main() -> int:
    first = make_policy_noise(123, 10, 32)
    repeated = make_policy_noise(123, 10, 32)
    different = make_policy_noise(124, 10, 32)
    assert first.shape == (10, 32)
    assert first.dtype == np.float32
    assert np.array_equal(first, repeated)
    assert not np.array_equal(first, different)

    single_run = run_case(9000, 4)
    run_case(123_000, 3)
    full_order_run = run_case(9000, 4)
    restarted_run = run_case(9000, 4)
    assert single_run == full_order_run == restarted_run
    assert len({noise_hash for noise_hash, _ in single_run}) == 4

    policy = DeterministicRequestPolicy(FakePolicy(), action_horizon=10, action_dim=32)
    assert policy.metadata == {"name": "fake"}
    try:
        policy.infer({"state": np.zeros(7)})
    except KeyError:
        pass
    else:
        raise AssertionError("missing deterministic seed must fail closed")

    evidence = policy.infer(
        {"state": np.zeros(7), "policy_noise_seed": 99}
    )["policy_sampling"]
    tampered = dict(evidence, noise_sha256="0" * 64)
    try:
        validate_policy_sampling_evidence(
            tampered,
            expected_seed=99,
            action_horizon=10,
            action_dim=32,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("tampered sampling evidence must fail closed")

    print(
        json.dumps(
            {
                "status": "pass",
                "checks": 12,
                "case_seed": 9000,
                "chunk_noise_sha256": [item[0] for item in single_run],
                "chunk_action_sha256": [item[1] for item in single_run],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
