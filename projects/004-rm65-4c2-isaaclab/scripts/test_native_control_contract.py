"""Reject native state/command unit, joint-order and hidden clipping mistakes."""
import json
from pathlib import Path
import sys

import numpy as np
import pytest

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P))
from openpi_extension.native_control_contract import (
    ARM_NAMES, CONTROLLED_NAMES, FOLLOWERS, MASTER, load_control_contract,
    feedback_to_state, absolute_action_to_targets,
)


@pytest.fixture
def contract():
    return load_control_contract(P/'config/native_control_contract_v1.json',
        source_urdf=P/'generated/native_surface_source_limits_001/native.urdf')


def measured(grip=.82):
    return {**dict.fromkeys(ARM_NAMES, 0.), MASTER: grip, **dict.fromkeys(FOLLOWERS, grip)}


def test_feedback_uses_names_actual_master_and_no_clipping(contract):
    q = measured(); q['joint_5'] = 1.5
    names = list(reversed(q))
    actual = feedback_to_state(contract, names, [q[n] for n in names])
    assert np.allclose(actual['state'], [0, 0, 0, 0, 1.5, 0, .82/.865])
    assert actual['state'][-1] != 1 and actual['state_was_clipped'] is False


@pytest.mark.parametrize('mode', ['missing', 'duplicate', 'nan', 'limit', 'mimic'])
def test_bad_actual_feedback_rejected(contract, mode):
    q = measured(); names = list(q)
    if mode == 'missing': names.pop()
    if mode == 'duplicate': names[-1] = names[0]
    if mode == 'nan': q[MASTER] = np.nan
    if mode == 'limit': q['joint_1'] = 20.
    if mode == 'mimic': q[FOLLOWERS[0]] -= .04
    with pytest.raises(ValueError): feedback_to_state(contract, names, [q[n] for n in names])


def test_float_limit_residual_recorded_not_hidden(contract):
    q = measured(-5e-8)
    result = feedback_to_state(contract, list(q), list(q.values()))
    assert result['state'][-1] < 0
    assert result['limit_violation_rad'][MASTER] == 5e-8
    q[MASTER] = -2e-6
    with pytest.raises(ValueError): feedback_to_state(contract, list(q), list(q.values()))


def test_only_master_is_commanded_and_roundtrip(contract):
    previous = {**dict.fromkeys(ARM_NAMES, 0.), MASTER: .8}
    targets = absolute_action_to_targets(contract, [0, 0, 0, 0, 0, .02, .82/.865],
        previous_targets_rad=previous, command_interval_s=.05)
    assert set(targets) == set(CONTROLLED_NAMES)
    assert set(targets).isdisjoint(FOLLOWERS)
    assert targets[MASTER] == pytest.approx(.82)


@pytest.mark.parametrize('action', [
    [0]*6, [0]*8, [0]*6+[np.nan], [0]*6+[-.01], [0]*6+[1.01],
    [10, 0, 0, 0, 0, 0, 0], [.03, 0, 0, 0, 0, 0, 0], [0]*6+[.2],
])
def test_bad_targets_or_command_jumps_rejected(contract, action):
    with pytest.raises(ValueError):
        absolute_action_to_targets(contract, action,
            previous_targets_rad=dict.fromkeys(CONTROLLED_NAMES, 0.), command_interval_s=.05)


@pytest.mark.parametrize('period', [None, 0, -.1, float('inf'), True])
def test_no_invented_control_period(contract, period):
    with pytest.raises((ValueError, TypeError)):
        absolute_action_to_targets(contract, [0]*7,
            previous_targets_rad=dict.fromkeys(CONTROLLED_NAMES, 0.), command_interval_s=period)


def test_reject_changed_source_bytes_and_wrong_units(contract, tmp_path):
    data = (P/'config/native_control_contract_v1.json').read_text()
    cfg = tmp_path/'control.json'; cfg.write_text(data)
    urdf = tmp_path/'source.urdf'
    urdf.write_bytes((P/'generated/native_surface_source_limits_001/native.urdf').read_bytes()+b'\n')
    with pytest.raises(ValueError, match='identity'):
        load_control_contract(cfg, source_urdf=urdf)
    changed = json.loads(data); changed['arm_units'] = 'degree'
    cfg.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match='arm_units'):
        load_control_contract(cfg, source_urdf=P/'generated/native_surface_source_limits_001/native.urdf')


def test_training_flag_cannot_be_enabled_by_contract_edit(contract, tmp_path):
    changed = json.loads((P/'config/native_control_contract_v1.json').read_text())
    changed['policy_training_admitted'] = True
    cfg = tmp_path/'control.json'; cfg.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match='policy_training_admitted'):
        load_control_contract(cfg, source_urdf=P/'generated/native_surface_source_limits_001/native.urdf')
