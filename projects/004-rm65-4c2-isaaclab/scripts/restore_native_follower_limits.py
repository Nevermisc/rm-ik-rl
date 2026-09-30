"""Restore only imported mimic-follower limits from the hashed source URDF."""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import shutil
import sys
import traceback
import xml.etree.ElementTree as ET
from build_native_gripper_candidate import sha256
from derive_native_collision_precision import stage_contract


def follower_limits(root):
    result={}
    for joint in root.findall('joint'):
        mimic=joint.find('mimic')
        if mimic is None: continue
        if joint.get('type')!='revolute' or mimic.get('joint')!='tool_gripper_joint':
            raise ValueError('unexpected mimic definition')
        bounds=[float(joint.find('limit').get(k)) for k in ('lower','upper')]
        if not all(math.isfinite(x) for x in bounds) or bounds[0]>=bounds[1]:
            raise ValueError('invalid source bounds')
        if not bounds[0]<=0 or not bounds[1]>=.865:
            raise ValueError('source follower must cover master sweep')
        result[joint.get('name')]=bounds
    if len(result)!=5: raise ValueError('five unique source followers required')
    return result


def main():
    from isaaclab.app import AppLauncher
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--destination',type=Path,required=True)
    AppLauncher.add_app_launcher_args(parser)
    args=parser.parse_args(); src=args.source.resolve(); dst=args.destination.resolve()
    if dst.exists(): parser.error('fresh destination required')
    audit=json.loads((src/'import_audit.json').read_text())
    sa=json.loads((src/'source_audit.json').read_text())
    if audit['status']!='pass' or sha256(src/'native.urdf')!=sa['urdf_sha256']:
        parser.error('source audit/hash failed')
    for name,expected in {**audit['composed_layer_sha256'],**sa['mesh_sha256']}.items():
        if sha256(name)!=expected: parser.error('source file changed')
    limits=follower_limits(ET.parse(src/'native.urdf').getroot())
    launcher=AppLauncher(args)
    try:
        from pxr import Usd,UsdPhysics
        dst.mkdir(parents=True,exist_ok=False)
        for name in ('native.usd','native.urdf'): shutil.copy2(src/name,dst/name)
        shutil.copytree(src/'configuration',dst/'configuration')
        sa['urdf']=str(dst/'native.urdf')
        with (dst/'source_audit.json').open('x') as stream: json.dump(sa,stream,indent=2)
        stage=Usd.Stage.Open(str(dst/'native.usd')); before=stage_contract(stage,False); changes=[]
        for name,bounds in limits.items():
            matches=[p for p in stage.Traverse() if p.GetName()==name and p.IsA(UsdPhysics.RevoluteJoint)]
            if len(matches)!=1: raise ValueError('ambiguous follower USD joint')
            prim=matches[0]; joint=UsdPhysics.RevoluteJoint(prim)
            old=[joint.GetLowerLimitAttr().Get(),joint.GetUpperLimitAttr().Get()]
            joint.CreateLowerLimitAttr().Set(math.degrees(bounds[0]))
            joint.CreateUpperLimitAttr().Set(math.degrees(bounds[1]))
            actual=[math.radians(joint.GetLowerLimitAttr().Get()),math.radians(joint.GetUpperLimitAttr().Get())]
            if max(abs(a-b) for a,b in zip(actual,bounds))>1e-7:
                raise ValueError('restored bounds differ from source')
            changes.append(dict(joint=name,path=str(prim.GetPath()),old_degrees=old,source_rad=bounds,actual_rad=actual))
        after=stage_contract(stage,False); normalized=copy.deepcopy(after)
        for row in changes:
            for key in ('physics:lowerLimit','physics:upperLimit'):
                normalized[row['path']]['attributes'][key]=before[row['path']]['attributes'][key]
        if before!=normalized: raise ValueError('unrelated joint/model change')
        stage.GetRootLayer().Save()
        if stage_contract(Usd.Stage.Open(str(dst/'native.usd')),False)!=after:
            raise ValueError('saved stage differs')
        inherited=audit.get('derivation',{})
        audit['usd']=str(dst/'native.usd')
        audit['composed_layer_sha256']={l.realPath:sha256(l.realPath) for l in stage.GetUsedLayers() if l.realPath}
        audit['derivation']=dict(source=str(src),source_import_audit_sha256=sha256(src/'import_audit.json'),
            change='five_follower_limits_restored_from_source_only',restored_limits=changes,
            source_follower_limit_equality=True,self_collision_filters_added=inherited.get('self_collision_filters_added',[]),
            inherited_derivation=inherited,unrelated_stage_contract_equal=True,physics_steps=0,
            hardware_transmission_validated=False)
        with (dst/'import_audit.json').open('x') as stream: json.dump(audit,stream,indent=2)
        print(json.dumps(changes,indent=2),flush=True)
    except BaseException:
        traceback.print_exc(); sys.stdout.flush(); sys.stderr.flush(); os._exit(1)
    else: launcher.app.close(skip_cleanup=True)


if __name__=='__main__': main()
