"""Real external/wrist RGB witnesses for a native development bench, not a dataset."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import torch
from PIL import Image
import omni.usd
from isaaclab.sensors.camera import Camera, CameraCfg
import isaaclab.sim as sim_utils
from isaaclab.utils.math import quat_apply, quat_from_matrix, quat_mul

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpi_extension.camera_rig import load_camera_rig, camera_rotation


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class NativeCameraProbe:
    """Construct before sim.reset; capture after reset at explicitly named physics steps.

    At least eight valid renderer refreshes happen with physics frozen. Camera buffer counters are
    not presented as independent renderer frame IDs. No object pose enters camera
    positioning. Geometric inclusion/occlusion and RGB content need separate review.
    """

    def __init__(self, rig_path, output_dir, sim):
        self.rig = load_camera_rig(Path(rig_path))
        self.out = Path(output_dir)/'camera_probe'
        self.out.mkdir(exist_ok=False)
        self.sim = sim
        self.last_step = 0
        self.rows = []
        self.cameras = {}
        optics = self.rig['config']['optics']
        for name in ('external', 'wrist'):
            self.cameras[name] = Camera(CameraCfg(
                prim_path=f'/World/Native{str.title(name)}Camera', update_period=0., update_latest_camera_pose=True,
                width=optics['width'], height=optics['height'], data_types=['rgb'],
                spawn=sim_utils.PinholeCameraCfg(focal_length=optics[name+'_focal_length_mm'],
                    focus_distance=1., horizontal_aperture=optics['horizontal_aperture_mm'],
                    clipping_range=tuple(optics['clipping_range_m']))))

    def manifest(self):
        return dict(rig=self.rig, helper_sha256=_sha(__file__),
            image_source='IsaacLab Camera real RGB, no generated or substitute frames',
            camera_buffer_counter_semantics='IsaacLab frame increments when buffers are recomputed; not an independent render-frame timestamp',
            sample_schedule='preview and named phase endpoints only; irregular intervals; NOT a training episode',
            minimum_valid_consecutive_refreshes=8, maximum_render_refreshes_per_capture=30, renderer_accumulation_reset=True,
            extra_physics_steps_per_capture=0, training_allowed=False,
            no_object_pose_or_task_target_for_camera_aim=True,
            appearance_review_required=True, quantified_occlusion_validated=False)

    def capture(self, robot, phase, step, physics_dt):
        if type(step) is not int or step < self.last_step or any(r['phase']==phase for r in self.rows):
            raise ValueError('camera phase must be fresh and physics step monotonic')
        config = self.rig['config']; wrist = config['wrist']; optics = config['optics']
        device = robot.device
        parent_id = list(robot.data.body_names).index(wrist['parent_link'])
        parent_p = robot.data.body_pos_w[0,parent_id].clone()
        parent_q = robot.data.body_quat_w[0,parent_id].clone()
        offset = torch.tensor(wrist['offset_local_m'], device=device, dtype=parent_p.dtype)
        local_rot = torch.tensor(camera_rotation(wrist['forward_local'], wrist['up_local']), device=device, dtype=parent_p.dtype)
        local_q = quat_from_matrix(local_rot.unsqueeze(0))
        eye = parent_p + quat_apply(parent_q.unsqueeze(0), offset.unsqueeze(0))[0]
        rotation = quat_mul(parent_q.unsqueeze(0), local_q)
        self.cameras['wrist'].set_world_poses(eye.unsqueeze(0), rotation, convention='opengl')
        self.cameras['external'].set_world_poses_from_view(
            torch.tensor([config['external']['eye_world_m']],device=device),
            torch.tensor([config['external']['target_world_m']],device=device))
        before_q = robot.root_physx_view.get_dof_positions().clone()
        before_clock = float(self.sim.current_time)
        omni.usd.get_context().reset_renderer_accumulation()
        history = {name: [] for name in self.cameras}
        images = {}
        valid_streak=0
        for refresh in range(30):
            self.sim.render()
            both_valid=True
            for name, camera in self.cameras.items():
                camera.update((step-self.last_step)*physics_dt if refresh==0 else 0.,force_recompute=True)
                output=camera.data.output
                buffer=output.get('rgb')
                raw_shape=list(buffer.shape) if buffer is not None else None
                rgb=(buffer[0,...,:3].detach().cpu().numpy().copy()
                     if buffer is not None and buffer.ndim==4 and buffer.shape[0]==1 else None)
                if rgb is None or rgb.shape != (optics['height'],optics['width'],3) or rgb.dtype != np.uint8:
                    history[name].append(dict(refresh=refresh,ready=False,raw_shape=raw_shape,
                        dtype=str(buffer.dtype) if buffer is not None else None,
                        empty_or_malformed_cache_cleared_for_real_annotator_reallocation=True))
                    # Camera otherwise retains an empty first annotator allocation and
                    # cannot assign a later correctly sized buffer. Never fabricate pixels.
                    output.clear()
                    both_valid=False
                    continue
                history[name].append(dict(refresh=refresh, rgb_bytes_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),
                    sensor_buffer_update_count=int(camera.frame[0]), sensor_internal_time_s=float(camera._timestamp[0])))
                images[name] = rgb
            valid_streak=valid_streak+1 if both_valid else 0
            if valid_streak>=8:break
        if valid_streak<8:
            raise RuntimeError('real camera buffers did not provide eight valid consecutive refreshes within 30 ticks')
        after_q = robot.root_physx_view.get_dof_positions()
        q_change = float(torch.max(torch.abs(before_q-after_q)))
        after_clock = float(self.sim.current_time)
        if q_change != 0 or after_clock != before_clock:
            raise RuntimeError('physics advanced while taking render-only camera witnesses')
        row = dict(phase=phase,sim_step=step,physics_time_s=step*physics_dt,
            renderer_refreshes=refresh+1,valid_consecutive_refreshes=valid_streak,simulation_clock_before_s=before_clock,simulation_clock_after_s=after_clock,
            max_actual_joint_change_during_capture_rad=q_change,
            wrist_parent=dict(name=wrist['parent_link'],position_m=parent_p.cpu().tolist(),quat_wxyz=parent_q.cpu().tolist()),
            cameras={})
        for name,camera in self.cameras.items():
            rgb=images[name]
            if int(rgb.max())-int(rgb.min())<2:
                raise RuntimeError(f'{name} RGB is constant or blank')
            path=self.out/f'{phase}_{name}.png'
            if path.exists(): raise FileExistsError(path)
            Image.fromarray(rgb).save(path)
            decoded=np.asarray(Image.open(path).convert('RGB'))
            if not np.array_equal(decoded,rgb): raise RuntimeError('saved PNG differs from sensor RGB')
            data=camera.data
            expected_pos=eye if name=='wrist' else torch.tensor(config['external']['eye_world_m'],device=device,dtype=parent_p.dtype)
            pose_error=float(torch.max(torch.abs(data.pos_w[0]-expected_pos)))
            expected_rotation=rotation[0] if name=='wrist' else quat_from_matrix(torch.tensor(
                camera_rotation(np.array(config['external']['target_world_m'])-np.array(config['external']['eye_world_m']),[0,0,1]),
                device=device,dtype=parent_p.dtype).unsqueeze(0))[0]
            quaternion_error=float(torch.minimum(torch.max(torch.abs(data.quat_w_opengl[0]-expected_rotation)),
                                                  torch.max(torch.abs(data.quat_w_opengl[0]+expected_rotation))))
            if pose_error>1e-5 or quaternion_error>1e-5:
                raise RuntimeError('CameraData pose is stale or differs from declared fixed rig')
            row['cameras'][name]=dict(path=str(path),png_sha256=_sha(path),
                rgb_bytes_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),rgb_bytewise_png_roundtrip=True,
                dimensions_wh=[optics['width'],optics['height']],intrinsic_matrix=data.intrinsic_matrices[0].cpu().tolist(),
                camera_position_world_m=data.pos_w[0].cpu().tolist(),camera_quat_wxyz_opengl=data.quat_w_opengl[0].cpu().tolist(),
                camera_quat_wxyz_ros=data.quat_w_ros[0].cpu().tolist(),clipping_range_m=optics['clipping_range_m'],
                sensor_buffer_update_count=int(camera.frame[0]),sensor_internal_time_s=float(camera._timestamp[0]),
                fixed_rig_position_error_m=pose_error,fixed_rig_quaternion_component_error=quaternion_error,
                rgb_min=int(rgb.min()),rgb_max=int(rgb.max()),rgb_std=float(rgb.std()),refresh_history=history[name])
        self.last_step=step
        self.rows.append(row)
        with (self.out/f'{phase}.json').open('x') as stream:json.dump(row,stream,indent=2,allow_nan=False)
        return row

    def finish(self):
        report=dict(self.manifest(),captures=self.rows,capture_count=len(self.rows),
            basic_rgb_and_render_only_checks_pass=bool(self.rows),native_camera_visual_acceptance=False,
            policy_observation_timing_validated=False,training_allowed=False)
        with (self.out/'report.json').open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)
        return report
