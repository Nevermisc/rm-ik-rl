import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpi_extension.training_admission import check_training_admission
from openpi_extension.task_instruction import require_task_prompt, TaskPromptPolicy


def test_legacy_is_only_legacy():
    evidence = check_training_admission({'metadata': {'task_success': True}})
    assert evidence['mode'] == 'legacy_reproduction'
    assert evidence['household_training_certified'] is False


@pytest.mark.parametrize('field,value', [
    ('task_success', False), ('training_eligible', False), ('training_ready', False),
    ('training_eligible', 'true'), ('unassisted_full_task_complete', False),
    ('diagnostic_only', True), ('evaluation_scope', 'multi_object_development_only'),
    ('evaluation_only', True),
    ('training_blocker', 'unreviewed'), ('object_probe', {'object_id': 'ycb_banana'}),
])
def test_reject_exclusions(field, value):
    with pytest.raises(ValueError):
        check_training_admission({'metadata': {'task_success': True, field: value}})


@pytest.mark.parametrize('report', [
    {'training_ready': False}, {'expert_episode': {'training_ready': False}},
    {'object_probe': {'object_id': 'ycb_mug'}},
    {'evaluation_scope': 'multi_object_development_only'},
])
def test_report_exclusion_cannot_be_hidden_by_manifest(report):
    with pytest.raises(ValueError):
        check_training_admission({'metadata': {'task_success': True, 'training_eligible': True}}, report)


@pytest.mark.parametrize('obs', [{}, {'prompt': ''}, {'prompt': None}, {'prompt': 3}])
def test_no_silent_block_task(obs):
    with pytest.raises(ValueError):
        require_task_prompt(obs)


def test_explicit_task_and_wrapper():
    class FakePolicy:
        metadata = {'fake': True}
        def infer(self, obs):
            return obs
    wrapper = TaskPromptPolicy(FakePolicy(), 'pick up the mug')
    assert wrapper.infer({})['prompt'] == 'pick up the mug'
    obs = {'prompt': 'pick up the banana'}
    assert wrapper.infer(obs)['prompt'] == obs['prompt']
    assert wrapper.metadata == {'fake': True}
