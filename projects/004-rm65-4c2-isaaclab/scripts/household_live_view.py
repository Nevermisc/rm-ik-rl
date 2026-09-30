"""Visible development telemetry; UI refresh is distinct from physics progress."""
import json
import os
import time
from pathlib import Path


class HouseholdLiveView:
    def __init__(self, path, run_name, pi05_used=False):
        import omni.ui as ui
        settings_window = ui.Workspace.get_window('Simulation Settings')
        if settings_window is not None:
            settings_window.visible = False
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.started = time.monotonic()
        self.last_write = 0.0
        self.frames = 0
        self.pi05_used = bool(pi05_used)
        self.stage = 'PREFLIGHT - checking reachable path; no motion yet'
        self.panel = ui.Window('RM65 LIVE | SIMULATION ONLY | pi0.5 ' + ('ON' if self.pi05_used else 'OFF'), width=690, height=102,
                               position_x=580, position_y=580)
        with self.panel.frame:
            with ui.VStack():
                ui.Label(run_name, height=24)
                self.stage_label = ui.Label(self.stage, height=24)
                self.clock_label = ui.Label('Waiting for first GUI refresh', height=24)

    def refresh(self, physics_steps=0, stage=None):
        if stage is not None:
            self.stage = stage
        self.frames += 1
        now = time.monotonic()
        stamp = time.strftime('%H:%M:%S')
        self.stage_label.text = self.stage
        self.clock_label.text = f'Live refresh {stamp} | UI frames {self.frames} | physics steps {physics_steps}'
        if now - self.last_write >= 2:
            payload = dict(pid=os.getpid(), wall_time_unix=time.time(), local_clock=stamp,
                           elapsed_s=now-self.started, ui_refresh_count=self.frames,
                           physics_steps=physics_steps, stage=self.stage,
                           simulation_only=True, pi05_used=self.pi05_used)
            temporary = self.path.with_suffix('.tmp')
            temporary.write_text(json.dumps(payload, indent=2), encoding='utf-8')
            temporary.replace(self.path)
            self.last_write = now
