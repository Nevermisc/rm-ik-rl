"""Validate finite scripted arm targets; never sends a robot command."""
import math


def arm_phase_endpoints(protocol, source_limits):
    active=protocol.get('active_motion',False)
    mapping=protocol.get('arm_phase_targets_rad',{})
    if type(active) is not bool or not isinstance(mapping,dict):
        raise ValueError('explicit active mode and target mapping required')
    if (active and set(mapping)!={'active_lift','active_transport'}) or (not active and mapping):
        raise ValueError('only the two declared active arm phases may change targets')
    previous=protocol['arm_joint_targets_rad']
    dt=protocol['physics_dt_s']
    if not isinstance(dt,(int,float)) or isinstance(dt,bool) or not math.isfinite(dt) or dt<=0:
        raise ValueError('finite positive dt required')
    result={}
    for phase,_,count in protocol['phases']:
        target=mapping.get(phase,previous)
        if not isinstance(target,(list,tuple)) or len(target)!=6:
            raise ValueError('six arm targets required')
        if type(count) is not int or count<=0 or phase in result:
            raise ValueError('unique phases with positive step counts required')
        for index,q in enumerate(target,1):
            low,high=source_limits[f'joint_{index}']
            if isinstance(q,bool) or not isinstance(q,(int,float)) or not math.isfinite(q) or not low<=q<=high:
                raise ValueError('finite target within source joint limits required')
            # Peak derivative of 3 f^2 - 2 f^3 is 1.5 per unit interval.
            if 1.5*abs(q-previous[index-1])/(count*dt)>.5:
                raise ValueError('smooth arm command exceeds unchanged 0.5 rad/s cap')
        result[phase]=(list(previous),list(target))
        previous=target
    if not set(mapping)<=set(result):
        raise ValueError('declared arm motion phase missing from protocol')
    return result
