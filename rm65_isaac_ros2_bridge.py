from isaacsim import SimulationApp

simulation_app = SimulationApp({"renderer": "RaytracedLighting", "headless": False})

import numpy as np
import omni.graph.core as og
import usdrt.Sdf

from isaacsim.core.api import SimulationContext
from isaacsim.core.utils import extensions, prims, rotations, stage, viewports
from pxr import Gf

RM65_STAGE_PATH = "/RM65"
RM65_ARTICULATION_PATH = "/RM65/root_joint/root_joint"
RM65_USD_PATH = "/home/iot22/robot-learning/rm-ik-rl/assets/RM65-B/RM65-B.usd"

# Enable ROS2 bridge extension.
extensions.enable_extension("isaacsim.ros2.bridge")
simulation_app.update()

simulation_context = SimulationContext(stage_units_in_meters=1.0)

viewports.set_camera_view(
    eye=np.array([1.2, 1.2, 0.8]),
    target=np.array([0.0, 0.0, 0.4]),
)

# Load RM65-B USD.
robot = prims.create_prim(
    RM65_STAGE_PATH,
    "Xform",
    position=np.array([0.0, 0.0, 0.0]),
    orientation=rotations.gf_rotation_to_np_array(Gf.Rotation(Gf.Vec3d(0, 0, 1), 0)),
    usd_path=RM65_USD_PATH,
)

simulation_app.update()

# Create ROS2 bridge action graph.
og.Controller.edit(
    {"graph_path": "/ActionGraph", "evaluator_name": "execution"},
    {
        og.Controller.Keys.CREATE_NODES: [
            ("OnImpulseEvent", "omni.graph.action.OnImpulseEvent"),
            ("ReadSimTime", "isaacsim.core.nodes.IsaacReadSimulationTime"),
            ("Context", "isaacsim.ros2.bridge.ROS2Context"),
            ("PublishJointState", "isaacsim.ros2.bridge.ROS2PublishJointState"),
            ("SubscribeJointState", "isaacsim.ros2.bridge.ROS2SubscribeJointState"),
            ("ArticulationController", "isaacsim.core.nodes.IsaacArticulationController"),
            ("PublishClock", "isaacsim.ros2.bridge.ROS2PublishClock"),
        ],
        og.Controller.Keys.CONNECT: [
            ("OnImpulseEvent.outputs:execOut", "PublishJointState.inputs:execIn"),
            ("OnImpulseEvent.outputs:execOut", "SubscribeJointState.inputs:execIn"),
            ("OnImpulseEvent.outputs:execOut", "PublishClock.inputs:execIn"),
            ("OnImpulseEvent.outputs:execOut", "ArticulationController.inputs:execIn"),

            ("Context.outputs:context", "PublishJointState.inputs:context"),
            ("Context.outputs:context", "SubscribeJointState.inputs:context"),
            ("Context.outputs:context", "PublishClock.inputs:context"),

            ("ReadSimTime.outputs:simulationTime", "PublishJointState.inputs:timeStamp"),
            ("ReadSimTime.outputs:simulationTime", "PublishClock.inputs:timeStamp"),

            ("SubscribeJointState.outputs:jointNames", "ArticulationController.inputs:jointNames"),
            ("SubscribeJointState.outputs:positionCommand", "ArticulationController.inputs:positionCommand"),
            ("SubscribeJointState.outputs:velocityCommand", "ArticulationController.inputs:velocityCommand"),
            ("SubscribeJointState.outputs:effortCommand", "ArticulationController.inputs:effortCommand"),
        ],
        og.Controller.Keys.SET_VALUES: [
            ("ArticulationController.inputs:robotPath", RM65_ARTICULATION_PATH),
            ("PublishJointState.inputs:topicName", "isaac_joint_states"),
            ("SubscribeJointState.inputs:topicName", "isaac_joint_commands"),
            ("PublishJointState.inputs:targetPrim", [usdrt.Sdf.Path(RM65_ARTICULATION_PATH)]),
        ],
    },
)

simulation_app.update()
simulation_context.initialize_physics()
simulation_context.play()

print("RM65 Isaac ROS2 bridge started.")
print("Publishing: /isaac_joint_states")
print("Subscribing: /isaac_joint_commands")

while simulation_app.is_running():
    simulation_context.step(render=True)
    og.Controller.set(
        og.Controller.attribute("/ActionGraph/OnImpulseEvent.state:enableImpulse"),
        True,
    )

simulation_context.stop()
simulation_app.close()
