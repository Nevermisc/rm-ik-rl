"""Create a fresh rigid-mimic diagnostic variant; never edit the source candidate."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import traceback
from build_native_gripper_candidate import sha256
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--destination', type=Path, required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
src, dst = args.source.resolve(), args.destination.resolve()
if dst.exists():
    parser.error('fresh destination required')
audit = json.loads((src/'import_audit.json').read_text())
if audit['status'] != 'pass':
    parser.error('source import audit must pass')
for name, expected in audit['composed_layer_sha256'].items():
    if sha256(name) != expected:
        parser.error('source USD changed since audit')
launcher = AppLauncher(args)
from pxr import Usd, UsdPhysics, PhysxSchema


def main():
    # Source is copied to a fresh, isolated directory; all source files stay immutable.
    dst.mkdir(parents=True,exist_ok=False)
    for filename in ('native.usd','native.urdf'):
        shutil.copy2(src/filename,dst/filename)
    shutil.copytree(src/'configuration',dst/'configuration')
    source_audit = json.loads((src/'source_audit.json').read_text())
    source_audit['urdf'] = str(dst/'native.urdf')
    with (dst/'source_audit.json').open('x') as stream:
        json.dump(source_audit,stream,indent=2)
    stage = Usd.Stage.Open(str(dst/'native.usd'))
    changes = []
    for record in audit['passive_mimic_followers']:
        prim = next(p for p in stage.Traverse() if p.IsA(UsdPhysics.Joint) and p.GetName()==record['name'])
        schemas = [str(s) for s in prim.GetAppliedSchemas() if str(s).startswith('PhysxMimicJointAPI:')]
        if len(schemas)!=1:
            raise RuntimeError('missing mimic relation')
        axis = schemas[0].split(':',1)[1]
        frequency = prim.GetAttribute('physxMimicJoint:'+axis+':naturalFrequency')
        damping = prim.GetAttribute('physxMimicJoint:'+axis+':dampingRatio')
        if not frequency or not damping:
            raise RuntimeError('expected authored compliance attributes')
        changes.append(dict(joint=record['name'],old_frequency=float(frequency.Get()),
                            old_damping=float(damping.Get()),new_frequency=0.,new_damping=0.))
        frequency.Set(0.)
        damping.Set(0.)
        record['mimic_attributes'] = {a.GetName():str(a.Get()) for a in prim.GetAttributes() if 'mimic' in a.GetName().lower()}
    stage.GetRootLayer().Save()
    audit['usd'] = str(dst/'native.usd')
    audit['composed_layer_sha256'] = {l.realPath:sha256(l.realPath) for l in stage.GetUsedLayers() if l.realPath}
    audit['derivation'] = dict(source=str(src),source_import_audit_sha256=sha256(src/'import_audit.json'),
        change='ideal_rigid_mimic_from_source_urdf',changes=changes,
        self_collision_filters_added=[],physics_steps=0,
        rationale='URDF mimic specifies a kinematic relationship, not the importer-added 25 Hz/0.005 compliant spring.',
        hardware_transmission_validated=False)
    with (dst/'import_audit.json').open('x') as stream:
        json.dump(audit,stream,indent=2)
    print(json.dumps(audit['derivation'],indent=2),flush=True)


try:
    main()
except BaseException:
    traceback.print_exc()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(1)
else:
    launcher.app.close(skip_cleanup=True)
