import pytest
from audit_pad_table_clearance import require_pad_table_clearance


@pytest.mark.parametrize('clearance', [-.013, 0, .0019, float('nan')])
def test_reject_table_intersection(clearance):
    with pytest.raises(ValueError):
        require_pad_table_clearance({'states': [{'pads': {'left': {'min_z_above_table_m': clearance}}}]})


def test_pass_does_not_claim_whole_hand_safety():
    result = require_pad_table_clearance({'states': [{'pads': {'left': {'min_z_above_table_m': .003}}}]})
    assert not result['whole_hand_collision_checked']
    assert not result['contact_feasibility_proven']


def test_nan_after_finite_value_must_not_be_ignored():
    with pytest.raises(ValueError):
        require_pad_table_clearance({'states': [{'pads': {
            'left': {'min_z_above_table_m': .01}, 'right': {'min_z_above_table_m': float('nan')}}}]})
