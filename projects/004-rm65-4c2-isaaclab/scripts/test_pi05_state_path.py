"""Regression for numerical-state conditioning, no weights or GPU required."""
import numpy as np
import pytest

from audit_pi05_state_path import probe
from openpi import transforms
from openpi_extension.rm65_training_config import (
    make_pi05_rm65_lora_config, make_pi05_rm65_native_lora_config,
)


def test_legacy_behavior_is_frozen_not_silently_changed():
    config = make_pi05_rm65_lora_config(repo_id='local/legacy_audit')
    assert config.name == 'pi05_rm65_lora'
    assert config.model.max_token_len == 64
    assert probe(config.model)['status'] == 'fail'


def test_native_candidate_receives_state_and_has_new_identity():
    config = make_pi05_rm65_native_lora_config(repo_id='local/new_data_required')
    assert config.name != 'pi05_rm65_lora'
    assert config.model.pi05 and config.model.discrete_state_input
    assert config.model.max_token_len == 200
    assert config.weight_loader.params_path == 'gs://openpi-assets/checkpoints/pi05_base/params'
    assert probe(config.model)['status'] == 'pass'


@pytest.mark.parametrize('repo_id', ['', '   '])
def test_native_requires_dataset_identity(repo_id):
    with pytest.raises(ValueError):
        make_pi05_rm65_native_lora_config(repo_id=repo_id)


def test_absolute_delta_roundtrip_keeps_gripper_absolute():
    mask = transforms.make_bool_mask(6, -1)
    state = np.array([.1, -.2, .3, -.4, .5, -.6, .75], dtype=np.float32)
    action = np.tile(state + .05, (10, 1))
    delta = transforms.DeltaActions(mask)({'state': state.copy(), 'actions': action.copy()})
    np.testing.assert_allclose(delta['actions'][:, :6], .05, atol=1e-7)
    np.testing.assert_array_equal(delta['actions'][:, 6], action[:, 6])
    absolute = transforms.AbsoluteActions(mask)(delta)
    np.testing.assert_allclose(absolute['actions'], action, atol=1e-7)
