"""Source catalog for textured household-object development, no success claims."""
from dataclasses import dataclass, asdict
import hashlib
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class HouseholdSpec:
    object_id: str
    filename: str
    prompt_name: str
    simulation_mass_kg: float
    collision_limit: str

    def metadata(self):
        return dict(asdict(self), source_provider='NVIDIA Isaac 5.1 YCB assets',
                    source_collection='Props/YCB/Axis_Aligned',
                    asset_license='NVIDIA/underlying third-party asset terms; not project code license',
                    mass_is_simulation_assumption=True, split='development',
                    real_object_grasp_validated=False)


HOUSEHOLD_CATALOG = {s.object_id:s for s in (
    HouseholdSpec('ycb_mug', '025_mug.usd', 'mug', .12, 'Cup/handle cavities require collision inspection.'),
    HouseholdSpec('ycb_banana', '011_banana.usd', 'banana', .066, 'Irregular curved geometry; no deformability model.'),
    HouseholdSpec('ycb_soup_can', '005_tomato_soup_can.usd', 'soup can', .35, 'Rigid sealed can; contents not simulated.'),
    HouseholdSpec('ycb_pudding_box', '008_pudding_box.usd', 'pudding box', .19, 'Rigid box; crushing not simulated.'),
)}


@dataclass(frozen=True)
class HouseholdRuntime:
    object_id: str
    usd_path: str
    size_m: tuple[float, float, float]
    mass_kg: float
    asset_evidence: dict

    def metadata(self):
        return dict(HOUSEHOLD_CATALOG[self.object_id].metadata(),
                    geometry_only=False, textured_household_asset=True,
                    household_object_validated=False,
                    size_m=self.size_m, local_asset_sha256=self.asset_evidence['package_sha256'],
                    collision_approximation='convexDecomposition', cavity_fidelity_validated=False,
                    simulation_only=True)


def load_household(manifest, object_id):
    if object_id not in HOUSEHOLD_CATALOG:
        raise ValueError('unknown household object')
    data = json.loads(Path(manifest).read_text())
    if data.get('status') != 'pass':
        raise ValueError('asset manifest failed')
    matches = [c for c in data['cases'] if c['object_id'] == object_id]
    if len(matches) != 1:
        raise ValueError('missing or duplicate asset')
    item = matches[0]
    if item.get('status') != 'pass' or item['stage_meters_per_unit'] != 1.0 or item['stage_up_axis'] != 'Z':
        raise ValueError('asset must be verified, meters, Z-up')
    if not item.get('rigid_prims') or not item.get('collider_prims'):
        raise ValueError('asset lacks rigid body/collision')
    if item.get('physics_modifications', {}).get('collision_approximation') != 'convexDecomposition':
        raise ValueError('missing collision contract')
    path = Path(item['package_path']).resolve()
    if hashlib.sha256(path.read_bytes()).hexdigest() != item['package_sha256']:
        raise ValueError('asset checksum mismatch')
    if not item.get('copied_textures'):
        raise ValueError('asset has no texture provenance')
    for texture in item['copied_textures']:
        texture_path = (path.parent / texture['relative_path']).resolve()
        if not texture_path.is_relative_to(path.parent):
            raise ValueError('texture outside asset folder')
        if hashlib.sha256(texture_path.read_bytes()).hexdigest() != texture['sha256']:
            raise ValueError('texture checksum mismatch')
    lo, hi = item['bounds_min'], item['bounds_max']
    sizes = tuple(b-a for a,b in zip(lo,hi))
    if len(sizes) != 3 or any(not math.isfinite(s) or not .005 < s < .5 for s in sizes):
        raise ValueError('implausible size')
    if any(abs((a+b)/2) > .001 for a,b in zip(lo,hi)):
        raise ValueError('asset origin not centered; placement adapter needed')
    return HouseholdRuntime(object_id, str(path), sizes, HOUSEHOLD_CATALOG[object_id].simulation_mass_kg, item)


def household_spawn_config(spec, sim_utils):
    return sim_utils.UsdFileCfg(usd_path=spec.usd_path,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=False,
            solver_position_iteration_count=32, solver_velocity_iteration_count=4,
            max_depenetration_velocity=1.0))
