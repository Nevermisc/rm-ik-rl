from copy import deepcopy
import math
import pytest
from native_active_motion import arm_phase_endpoints


def fixture():
    q=[0,0,0,0,math.pi/2,0]; lifted=q.copy(); lifted[4]-=.15
    moved=lifted.copy(); moved[0]=.23
    return dict(active_motion=True,arm_joint_targets_rad=q,physics_dt_s=1/120,
        phases=[['close',.82,480],['active_lift',.82,240],['active_transport',.82,240],['reopen',0,480]],
        arm_phase_targets_rad={'active_lift':lifted,'active_transport':moved}),{f'joint_{i}':[-3,3] for i in range(1,7)}


def test_targets_continue_through_opening_without_reset():
    p,limits=fixture(); before=deepcopy(p); targets=arm_phase_endpoints(p,limits)
    assert targets['reopen'][0]==targets['reopen'][1]==p['arm_phase_targets_rad']['active_transport']
    assert targets['active_transport'][0]==p['arm_phase_targets_rad']['active_lift']
    assert p==before


@pytest.mark.parametrize('defect',['speed','limit','nonfinite','short','undeclared','inactive'])
def test_refuse_invalid_motion_contract(defect):
    p,limits=fixture()
    if defect=='speed': p['phases'][1][2]=1
    elif defect=='limit': limits['joint_5']=[0,1]
    elif defect=='nonfinite': p['arm_phase_targets_rad']['active_lift'][1]=float('nan')
    elif defect=='short': p['arm_phase_targets_rad']['active_lift'].pop()
    elif defect=='undeclared': p['arm_phase_targets_rad']['reopen']=[0]*6
    else: p['active_motion']=False
    with pytest.raises(ValueError): arm_phase_endpoints(p,limits)
