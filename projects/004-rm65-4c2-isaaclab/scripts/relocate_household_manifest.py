"""Relocate a restored asset cache without accepting altered meshes/textures."""
import argparse
import copy
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpi_extension.household_assets import HOUSEHOLD_CATALOG, load_household, manifest_object_ids


def relocate(source, asset_root, output):
    output = Path(output)
    if output.exists():
        raise FileExistsError('never overwrite a manifest')
    data = copy.deepcopy(json.loads(Path(source).read_text()))
    expected = set(manifest_object_ids(source))
    seen = set()
    for case in data['cases']:
        object_id = case['object_id']
        if object_id not in HOUSEHOLD_CATALOG or object_id in seen:
            raise ValueError('unknown or duplicate object')
        seen.add(object_id)
        case['package_path'] = str((Path(asset_root) / object_id / 'model.usd').resolve())
    if seen != expected:
        raise ValueError('a complete declared object cache is required')
    # Validate all bytes before publishing any final manifest.
    with tempfile.TemporaryDirectory(prefix='rm65-household-verify-') as temporary:
        candidate = Path(temporary) / 'candidate.json'
        candidate.write_text(json.dumps(data))
        for object_id in seen:
            load_household(candidate, object_id)
    data['relocated_from_manifest'] = str(Path(source).resolve())
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        json.dump(data, stream, indent=2)
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--asset-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    relocate(args.manifest, args.asset_root, args.output)
    print('HOUSEHOLD_CACHE_RELOCATION=PASS')
