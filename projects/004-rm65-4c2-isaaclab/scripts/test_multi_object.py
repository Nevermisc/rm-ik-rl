import unittest
from dataclasses import replace
from openpi_extension.multi_object import CATALOG
from openpi_extension.multi_object import write_development_report
from pathlib import Path
from tempfile import TemporaryDirectory
import json


class CatalogTests(unittest.TestCase):
    def test_development_shape_coverage(self):
        self.assertEqual({s.shape for s in CATALOG.values() if s.split == 'development'}, {'box','sphere','cylinder'})

    def test_reserved_instance_not_development(self):
        self.assertEqual(CATALOG['round_reserved'].split, 'reserved')
        self.assertNotEqual(CATALOG['round_reserved'].size_m, CATALOG['round_small'].size_m)

    def test_invalid_dimensions(self):
        for size in [(0,.1,.1), (.1,float('nan'),.1), (.1,.1)]:
            with self.assertRaises(ValueError):
                replace(CATALOG['block_reference'], size_m=size)

    def test_invalid_mass(self):
        with self.assertRaises(ValueError):
            replace(CATALOG['round_small'], mass_kg=-1)

    def test_shape_contract(self):
        with self.assertRaises(ValueError):
            replace(CATALOG['round_small'], size_m=(.05,.06,.05))

    def test_no_household_claim(self):
        for spec in CATALOG.values():
            self.assertFalse(spec.metadata()['household_object_validated'])

    def test_legacy_report_unchanged(self):
        with TemporaryDirectory() as root:
            path = Path(root)/'result.json'
            report = {'status':'pass', 'expert_episode':{'training_ready':True}}
            write_development_report(path, report)
            self.assertEqual(json.loads(path.read_text()), report)
            self.assertTrue(report['expert_episode']['training_ready'])

    def test_probe_not_training_or_acceptance(self):
        with TemporaryDirectory() as root:
            path = Path(root)/'result.json'
            report = {'status':'pass', 'expert_episode':{'training_ready':True}}
            write_development_report(path, report, CATALOG['round_small'])
            self.assertFalse(report['formal_acceptance_passed'])
            self.assertFalse(report['expert_episode']['training_ready'])


if __name__ == '__main__':
    unittest.main()
