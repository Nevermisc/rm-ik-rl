"""Visible layout preview only: holds the robot, does not execute a task/policy."""
import argparse
import math
import sys
import time
from pathlib import Path
from isaaclab.app import AppLauncher

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--manifest', type=Path, required=True)
parser.add_argument('--usd', type=Path, required=True)
parser.add_argument('--source-x', type=float, default=-.37128649)
parser.add_argument('--seconds', type=float, default=900)
AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args()
if args.headless: parser.error('preview requires a visible window')
if not -.45 <= args.source_x <= -.20 or not 0 < args.seconds <= 3600:
    parser.error('preview bounds exceeded')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from openpi_extension.household_assets import load_household, household_spawn_config
spec=load_household(args.manifest,'ycb_banana')
launcher=AppLauncher(args)
import torch
import omni.ui as ui
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, ArticulationCfg, RigidObject, RigidObjectCfg
from isaaclab.actuators import ImplicitActuatorCfg

try:
    sim=sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=1/240,device=args.device))
    sim.set_camera_view(eye=(.8,-1.4,1.35),target=(-.15,-.1,.75))
    light=sim_utils.DomeLightCfg(intensity=700)
    light.func('/World/Light',light)
    def box(path,size,position,color):
        cfg=sim_utils.CuboidCfg(size=size,collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=color))
        cfg.func(path,cfg,translation=position)
    box('/World/Floor',(3,3,.04),(0,0,-.02),(.12,.15,.19))
    box('/World/RobotStand',(.14,.14,.65),(0,0,.325),(.25,.28,.32))
    box('/World/SourcePlatform',(.20,.20,.02),(args.source_x,0,.723),(.38,.42,.48))
    box('/World/TargetPlatform',(.20,.20,.02),
        (args.source_x*math.cos(.8),args.source_x*math.sin(.8),.723),(.15,.55,.35))
    robot=Articulation(ArticulationCfg(prim_path='/World/Robot',
        spawn=sim_utils.UsdFileCfg(usd_path=str(args.usd.resolve()),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=False),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(enabled_self_collisions=False)),
        init_state=ArticulationCfg.InitialStateCfg(pos=(0,0,.65),joint_pos={
            'joint_1':0.,'joint_2':-.55,'joint_3':1.05,'joint_4':0.,'joint_5':.65,'joint_6':0.,'tool_.*':0.}),
        actuators={'all':ImplicitActuatorCfg(joint_names_expr=['.*'],effort_limit_sim=1000,
                                            stiffness=5000,damping=300)}))
    obj=RigidObject(RigidObjectCfg(prim_path='/World/Banana',spawn=household_spawn_config(spec,sim_utils),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(args.source_x,0,.733+spec.size_m[2]/2))))
    panel=ui.Window('RM65 - LIVE LAYOUT PREVIEW (NOT A GRASP TEST)',width=550,height=140)
    with panel.frame:
        with ui.VStack():
            ui.Label('SIMULATION ONLY | pi0.5 is NOT running',height=28)
            ui.Label(f'Banana platform center: {abs(args.source_x)*100:.1f} cm from base axis',height=28)
            ui.Label('Robot is held stationary; reachability is being checked separately.',height=28)
            ui.Label('Close this window/app whenever you want to end the preview.',height=28)
    sim.reset()
    state=robot.data.default_joint_pos.clone()
    robot.write_joint_state_to_sim(state,torch.zeros_like(state))
    start=time.monotonic()
    step=0
    print('VISIBLE_LAYOUT_PREVIEW=RUNNING; stationary robot, not a grasp result',flush=True)
    while launcher.app.is_running() and time.monotonic()-start < args.seconds:
        robot.set_joint_position_target(state)
        robot.write_data_to_sim()
        obj.write_data_to_sim()
        sim.step(render=False)
        robot.update(sim.get_physics_dt())
        obj.update(sim.get_physics_dt())
        step+=1
        if step%8==0:
            sim.render()
            delay=step/240-(time.monotonic()-start)
            if delay>0: time.sleep(min(delay,.04))
finally:
    launcher.app.close(skip_cleanup=True)
