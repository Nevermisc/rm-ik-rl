"""Fetch a pinned RealMan reference to a fresh cache; compare, never replace assets."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from audit_robot_model_lineage import source_report, differences, sha

REPO = 'RealManRobot/rm_models'
COMMIT = 'b63dddb20b7620d14cfff32678de60bb3a201ebc'
ARM = 'RM65/urdf/RM65-B'
GRIP = 'thirdparty/Two-finger Electric Gripper.urdf'


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'RM65-read-only-model-audit'})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--local-arm', required=True, type=Path)
    parser.add_argument('--local-gripper', required=True, type=Path)
    args = parser.parse_args()
    if args.cache.exists() or args.output.exists():
        parser.error('fresh cache and output paths required')
    tree = json.loads(fetch(f'https://api.github.com/repos/{REPO}/git/trees/{COMMIT}?recursive=1'))
    if tree['sha'] != COMMIT or tree.get('truncated'):
        raise ValueError('unverified/incomplete official repository tree')
    entries = [e for e in tree['tree'] if e['type'] == 'blob' and (
        (e['path'].startswith((ARM + '/', GRIP + '/')) and e['path'].lower().endswith(('.urdf', '.stl')))
        or e['path'] == 'LICENSE')]
    args.cache.mkdir(parents=True, exist_ok=False)
    sources = []
    for entry in entries:
        name = entry['path']
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('invalid reference path')
        url = f'https://raw.githubusercontent.com/{REPO}/{COMMIT}/' + urllib.parse.quote(name)
        data = fetch(url)
        git_sha = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if git_sha != entry['sha'] or len(data) != entry['size']:
            raise ValueError('reference blob mismatch: ' + name)
        path = args.cache / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
        sources.append(dict(path=name, url=url, git_blob_sha1=git_sha, sha256=sha(path), bytes=len(data)))
    arm, arm_root = source_report(args.cache / ARM / 'urdf/RM65-B.urdf', args.cache / ARM / 'meshes')
    grip, _ = source_report(args.cache / GRIP / 'urdf/EG2-4C2.urdf', args.cache / GRIP / 'meshes')
    local_root = ET.parse(args.local_arm).getroot()
    arm_diffs = []
    for tag in ('link', 'joint'):
        for original in arm_root.findall(tag):
            delta = differences(original, local_root.find(f"{tag}[@name='{original.get('name')}']"))
            if delta:
                arm_diffs.append(dict(tag=tag, name=original.get('name'), differences=delta))
    local_grip_root = ET.parse(args.local_gripper).getroot()
    result = dict(schema='rm65_official_reference_audit_v1', physics_steps=0, source_assets_modified=False,
        repository=REPO, commit=COMMIT, downloads=sources,
        official_arm=arm, official_gripper=grip,
        local_arm_sha256=sha(args.local_arm), local_gripper_sha256=sha(args.local_gripper),
        arm_semantic_differences=arm_diffs,
        gripper_link_names_local=[l.get('name') for l in local_grip_root.findall('link')],
        gripper_link_names_official=[l['name'] for l in grip['links']],
        limitations=['Official gripper reference is not automatically the users exact hardware revision.',
                     'Different frames/part topology require explicit registration; do not compare COM components blindly.',
                     'Official repository provenance does not certify dynamics or hardware calibration.'])
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(dict(commit=COMMIT, downloads=len(sources), arm_changed=[r['name'] for r in arm_diffs],
        official_gripper_links=result['gripper_link_names_official'],
        official_gripper_com_outside=[dict(name=l['name'], outside_m=l['com_outside_visual_aabb_m'])
                                     for l in grip['links'] if max(l['com_outside_visual_aabb_m']) > 1e-6]), indent=2))


if __name__ == '__main__':
    main()
