"""Simulation-only geometric probes, not validated household-object assets.

Keep imports independent of Isaac so catalog validation can run before GPU startup.
"""
from dataclasses import dataclass, asdict
import math
import json


@dataclass(frozen=True)
class ObjectSpec:
    object_id: str
    shape: str
    size_m: tuple[float, float, float]
    mass_kg: float
    color: tuple[float, float, float]
    split: str

    def __post_init__(self):
        if self.shape not in {"box", "sphere", "cylinder"}:
            raise ValueError("unsupported shape")
        if len(self.size_m) != 3 or any(not math.isfinite(v) or v <= 0 for v in self.size_m):
            raise ValueError("three positive finite dimensions required")
        if not math.isfinite(self.mass_kg) or self.mass_kg <= 0:
            raise ValueError("positive finite mass required")
        if len(self.color) != 3 or any(not math.isfinite(v) or not 0 <= v <= 1 for v in self.color):
            raise ValueError("invalid color")
        if self.split not in {"development", "reserved"}:
            raise ValueError("invalid split")
        x, y, z = self.size_m
        if self.shape == "sphere" and not x == y == z:
            raise ValueError("sphere diameters must match")
        if self.shape == "cylinder" and x != y:
            raise ValueError("cylinder diameters must match")

    def metadata(self):
        return dict(asdict(self), geometry_only=True, household_object_validated=False,
                    simulation_only=True, upright_center_height_m=self.size_m[2] / 2)


# Different physical grasp challenges. A sphere is not an apple; a slab is not
# a photorealistic phone; a cylinder is not a hollow mug with a handle.
CATALOG = {
    s.object_id: s for s in (
        ObjectSpec("block_reference", "box", (.06, .04, .025), .03, (.85,.1,.08), "development"),
        ObjectSpec("round_small", "sphere", (.05,.05,.05), .06, (.15,.65,.2), "development"),
        ObjectSpec("cylinder_upright", "cylinder", (.05,.05,.09), .10, (.2,.3,.8), "development"),
        ObjectSpec("thin_slab", "box", (.13,.065,.009), .16, (.1,.1,.12), "development"),
        ObjectSpec("box_wide", "box", (.08,.055,.035), .07, (.8,.6,.15), "development"),
        ObjectSpec("round_reserved", "sphere", (.065,.065,.065), .10, (.7,.2,.15), "reserved"),
    )
}


def spawn_config(spec, sim_utils):
    """Generate a dynamic collision-enabled primitive; no robot control."""
    common = dict(
        rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=False),
        mass_props=sim_utils.MassPropertiesCfg(mass=spec.mass_kg),
        collision_props=sim_utils.CollisionPropertiesCfg(),
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=spec.color),
        physics_material=sim_utils.RigidBodyMaterialCfg(
            static_friction=.7, dynamic_friction=.5, restitution=0.0),
    )
    if spec.shape == "box":
        return sim_utils.CuboidCfg(size=spec.size_m, **common)
    if spec.shape == "sphere":
        return sim_utils.SphereCfg(radius=spec.size_m[0]/2, **common)
    return sim_utils.CylinderCfg(radius=spec.size_m[0]/2, height=spec.size_m[2], axis="Z", **common)


def write_development_report(path, report, spec=None):
    """Preserve historical reports; explicitly segregate new geometry results."""
    if spec is not None:
        report['object_probe'] = spec.metadata()
        report['evaluation_scope'] = 'multi_object_development_only'
        report['formal_acceptance_passed'] = False
        report['training_ready'] = False
        report['multi_object_limitation'] = (
            'Historical block criteria and calibrated grasp geometry are diagnostic only. '
            'This run cannot establish household-object capability or enter training automatically.')
        if isinstance(report.get('expert_episode'), dict):
            report['expert_episode']['training_ready'] = False
            report['expert_episode']['training_blocker'] = 'multi_object_geometry_requires_review'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
