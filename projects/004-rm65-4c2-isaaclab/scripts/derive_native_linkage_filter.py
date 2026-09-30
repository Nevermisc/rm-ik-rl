"""Fresh diagnostic variant with four source-supported internal hinge filters.

No external collider, geometry, mass, drive, gravity or contact-offset changes.
The reviewed list is not generated from contact-force peaks or task outcomes.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import traceback
from build_native_gripper_candidate import sha256

REVIEWED_HINGES = [
    ('tool_base_link', 'tool_l_2'), ('tool_base_link', 'tool_r_2'),
    ('tool_l_2', 'tool_l_3'), ('tool_r_2', 'tool_r_3'),
]


def validate_evidence(proof, urdf_hash):
    if proof['urdf_sha256'] != urdf_hash:
        raise ValueError('pivot proof/source mismatch')
    rows = {tuple(r['links']): r for r in proof['pairs']}
    for pair in REVIEWED_HINGES:
        row = rows.get(pair)
        if row is None or not row['plausible_kinematic_hinge'] or row['max_pivot_coincidence_error_m'] > 1e-6:
            raise ValueError('missing reviewed kinematic hinge evidence')
        for name in pair:
            profiles = row.get('source_cylinder_profiles', {}).get(name, [])
            if not any(p['angular_coverage_deg'] > 300 and p['interpretation'] == 'hole_candidate' for p in profiles):
                raise ValueError('missing source coaxial hole evidence')
    return [rows[p] for p in REVIEWED_HINGES]


def main():
    from isaaclab.app import AppLauncher
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--pivot-evidence', type=Path, required=True)
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    src, dst = args.source.resolve(), args.destination.resolve()
    if dst.exists():
        parser.error('fresh destination required')
    audit = json.loads((src/'import_audit.json').read_text())
    source_audit = json.loads((src/'source_audit.json').read_text())
    proof = json.loads(args.pivot_evidence.read_text())
    reviewed = validate_evidence(proof, sha256(src/'native.urdf'))
    if audit['status'] != 'pass':
        parser.error('source import audit must pass')
    for name, expected in audit['composed_layer_sha256'].items():
        if sha256(name) != expected:
            parser.error('source layer changed')
    for name, expected in source_audit['mesh_sha256'].items():
        if sha256(name) != expected:
            parser.error('source mesh changed')
    launcher = AppLauncher(args)
    try:
        from pxr import Usd, UsdPhysics
        dst.mkdir(parents=True, exist_ok=False)
        for filename in ('native.usd','native.urdf'):
            shutil.copy2(src/filename,dst/filename)
        shutil.copytree(src/'configuration',dst/'configuration')
        source_audit['urdf'] = str(dst/'native.urdf')
        with (dst/'source_audit.json').open('x') as stream:
            json.dump(source_audit, stream, indent=2)
        stage = Usd.Stage.Open(str(dst/'native.usd'))
        bodies = {p.GetName():p for p in stage.Traverse() if p.HasAPI(UsdPhysics.RigidBodyAPI)}
        if any(p.HasAPI(UsdPhysics.FilteredPairsAPI) for p in stage.Traverse()):
            raise ValueError('unexpected preexisting pair filters')
        for left, right in REVIEWED_HINGES:
            UsdPhysics.FilteredPairsAPI.Apply(bodies[left]).CreateFilteredPairsRel().AddTarget(bodies[right].GetPath())
        stage.GetRootLayer().Save()
        audit['usd'] = str(dst/'native.usd')
        audit['composed_layer_sha256'] = {l.realPath:sha256(l.realPath) for l in stage.GetUsedLayers() if l.realPath}
        audit['derivation'] = dict(source=str(src), source_import_audit_sha256=sha256(src/'import_audit.json'),
            change='four_source_supported_internal_linkage_pairs_only',
            self_collision_filters_added=[list(p) for p in REVIEWED_HINGES],
            evidence_sha256=sha256(args.pivot_evidence), evidence=reviewed,
            global_self_collision_unchanged=True, external_collisions_unchanged=True,
            geometry_mass_drives_unchanged=True, physics_steps=0,
            hardware_transmission_validated=False, source_follower_limit_equality=False,
            rationale='Coaxial source holes plus fixed pivot coincidence throughout 19 poses; '
                      'diagnostic internal linkage abstraction, not permission from task/contact success.')
        with (dst/'import_audit.json').open('x') as stream:
            json.dump(audit, stream, indent=2)
        print(json.dumps(audit['derivation'],indent=2),flush=True)
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    else:
        launcher.app.close(skip_cleanup=True)


if __name__ == '__main__':
    main()
