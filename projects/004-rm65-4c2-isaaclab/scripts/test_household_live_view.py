import contextlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from household_live_view import HouseholdLiveView


class LiveViewTests(unittest.TestCase):
    def test_state_does_not_invent_policy_or_physics_progress(self):
        titles = []
        ui = types.ModuleType('omni.ui')
        def window(title, **kwargs):
            titles.append(title)
            return types.SimpleNamespace(frame=contextlib.nullcontext())
        ui.Window = window
        ui.Workspace = types.SimpleNamespace(get_window=lambda name: None)
        ui.VStack = contextlib.nullcontext
        ui.Label = lambda text, **kwargs: types.SimpleNamespace(text=text)
        omni = types.ModuleType('omni')
        omni.ui = ui
        with tempfile.TemporaryDirectory() as folder, patch.dict(sys.modules, {'omni': omni, 'omni.ui': ui}):
            for policy in (False, True):
                path = Path(folder)/f'{policy}.json'
                view = HouseholdLiveView(path, 'test', pi05_used=policy)
                view.refresh(7, 'PAUSED')
                view.last_write = 0
                view.refresh(7, 'PAUSED')
                data = json.loads(path.read_text())
                self.assertEqual(data['pi05_used'], policy)
                self.assertEqual(data['physics_steps'], 7)
                self.assertEqual(data['ui_refresh_count'], 2)
                self.assertEqual(data['stage'], 'PAUSED')
                self.assertTrue(titles[-1].endswith('ON' if policy else 'OFF'))


if __name__ == '__main__':
    unittest.main()
