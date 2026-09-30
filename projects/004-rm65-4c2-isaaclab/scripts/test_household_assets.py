import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from openpi_extension.household_assets import load_household, manifest_object_ids


class HouseholdTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.asset = self.root/'model.usd'
        self.asset.write_bytes(b'unit test asset; not a real USD')
        self.texture = self.root/'color.png'
        self.texture.write_bytes(b'unit test texture')
        self.case = dict(object_id='ycb_mug', status='pass', package_path=str(self.asset),
            package_sha256=hashlib.sha256(self.asset.read_bytes()).hexdigest(),
            copied_textures=[dict(relative_path='color.png', sha256=hashlib.sha256(self.texture.read_bytes()).hexdigest())],
            stage_meters_per_unit=1.0, stage_up_axis='Z', rigid_prims=['/Root'], collider_prims=['/Root/Mesh'],
            physics_modifications=dict(collision_approximation='convexDecomposition'),
            bounds_min=[-.05,-.04,-.04], bounds_max=[.05,.04,.04])
        self.manifest = self.root/'manifest.json'

    def tearDown(self):
        self.temp.cleanup()

    def load(self):
        self.manifest.write_text(json.dumps(dict(status='pass',cases=[self.case])))
        return load_household(self.manifest,'ycb_mug')

    def test_valid_metadata_not_grasp_claim(self):
        spec = self.load()
        self.assertEqual(spec.size_m,(.1,.08,.08))
        self.assertTrue(spec.metadata()['textured_household_asset'])
        self.assertFalse(spec.metadata()['household_object_validated'])

    def test_usd_tamper(self):
        self.asset.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'checksum'): self.load()

    def test_texture_tamper(self):
        self.texture.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'checksum'): self.load()

    def test_units(self):
        self.case['stage_meters_per_unit'] = .01
        with self.assertRaisesRegex(ValueError,'meters'): self.load()

    def test_missing_collision(self):
        self.case['collider_prims'] = []
        with self.assertRaisesRegex(ValueError,'collision'): self.load()

    def test_offset_origin(self):
        self.case['bounds_min'] = [0,0,0]
        with self.assertRaisesRegex(ValueError,'centered'): self.load()

    def test_texture_traversal(self):
        self.case['copied_textures'][0]['relative_path'] = '../escape.png'
        with self.assertRaisesRegex(ValueError,'outside'): self.load()

    def test_unknown_object(self):
        with self.assertRaisesRegex(ValueError,'unknown'): load_household(self.manifest,'not_present')

    def test_explicit_subset_manifest(self):
        self.manifest.write_text(json.dumps(dict(requested_object_ids=['ycb_mug'], cases=[self.case])))
        self.assertEqual(manifest_object_ids(self.manifest), ['ycb_mug'])

    def test_incomplete_declared_subset(self):
        self.manifest.write_text(json.dumps(dict(requested_object_ids=['ycb_mug', 'ycb_large_marker'], cases=[self.case])))
        with self.assertRaisesRegex(ValueError, 'complete'): manifest_object_ids(self.manifest)


if __name__ == '__main__': unittest.main()
