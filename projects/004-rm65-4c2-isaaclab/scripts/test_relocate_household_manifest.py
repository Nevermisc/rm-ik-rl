import hashlib
import json
from pathlib import Path

import pytest

from openpi_extension.household_assets import LEGACY_OBJECT_IDS
from relocate_household_manifest import relocate


@pytest.fixture
def cache(tmp_path):
    cases = []
    root = tmp_path/'restored'
    for key in LEGACY_OBJECT_IDS:
        folder = root/key
        folder.mkdir(parents=True)
        (folder/'model.usd').write_bytes(b'unit fixture')
        (folder/'color.png').write_bytes(b'texture fixture')
        cases.append(dict(object_id=key, status='pass', package_path='/old/unavailable/model.usd',
            package_sha256=hashlib.sha256(b'unit fixture').hexdigest(),
            copied_textures=[dict(relative_path='color.png', sha256=hashlib.sha256(b'texture fixture').hexdigest())],
            stage_meters_per_unit=1., stage_up_axis='Z', rigid_prims=['/Root'], collider_prims=['/Root/Mesh'],
            physics_modifications={'collision_approximation':'convexDecomposition'},
            bounds_min=[-.05,-.04,-.04], bounds_max=[.05,.04,.04]))
    manifest = tmp_path/'source.json'
    manifest.write_text(json.dumps({'status':'pass','cases':cases}))
    return manifest, root, tmp_path/'new.json'


def test_relocation(cache):
    manifest, root, output = cache
    original = manifest.read_bytes()
    data = relocate(*cache)
    assert len(data['cases']) == 4
    assert Path(data['cases'][0]['package_path']).is_file()
    assert manifest.read_bytes() == original


def test_corruption_rejected_without_output(cache):
    manifest, root, output = cache
    (root/'ycb_mug'/'color.png').write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='checksum'):
        relocate(*cache)
    assert not output.exists()


def test_no_overwrite(cache):
    relocate(*cache)
    original = cache[2].read_bytes()
    with pytest.raises(FileExistsError):
        relocate(*cache)
    assert cache[2].read_bytes() == original


def test_partial_cache_rejected(cache):
    data = json.loads(cache[0].read_text())
    data['cases'].pop()
    cache[0].write_text(json.dumps(data))
    with pytest.raises(ValueError, match='complete'):
        relocate(*cache)
    assert not cache[2].exists()
