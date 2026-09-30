"""Cache official USD meshes/textures; built-in MDL shaders remain an Isaac dependency."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--asset-dir', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.output.exists() or args.asset_dir.exists():
    parser.error('use new asset and report paths; existing assets are never overwritten')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpi_extension.household_assets import HOUSEHOLD_CATALOG
launcher = AppLauncher(args)
from pxr import Usd, UsdGeom, UsdPhysics, UsdShade, Sdf
import omni.client
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR

try:
    args.asset_dir.mkdir(parents=True)
    cases = []
    for spec in HOUSEHOLD_CATALOG.values():
        source = f'{ISAAC_NUCLEUS_DIR}/Props/YCB/Axis_Aligned/{spec.filename}'
        local = args.asset_dir / spec.object_id / 'model.usd'
        local.parent.mkdir()
        print('HOUSEHOLD_PREPARE=' + source, flush=True)
        item = dict(spec.metadata(), source_url=source, package_path=str(local.resolve()))
        try:
            if omni.client.copy(source, str(local)) != omni.client.Result.OK:
                raise RuntimeError('USD source copy failed')
            source_sha256 = hashlib.sha256(local.read_bytes()).hexdigest()
            stage = Usd.Stage.Open(str(local))
            copied_textures = []
            for prim in stage.Traverse():
                for attr in prim.GetAttributes():
                    if attr.GetTypeName() != Sdf.ValueTypeNames.Asset:
                        continue
                    value = attr.Get()
                    if not value or not value.path.lower().endswith(('.png', '.jpg', '.jpeg')):
                        continue
                    texture_source = urljoin(source, value.path)
                    texture = local.parent / 'textures' / Path(urlparse(texture_source).path).name
                    texture.parent.mkdir(exist_ok=True)
                    if not texture.exists() and omni.client.copy(texture_source, str(texture)) != omni.client.Result.OK:
                        raise RuntimeError('texture copy failed: ' + texture_source)
                    attr.Set(Sdf.AssetPath('textures/' + texture.name))
                    copied_textures.append(dict(source=texture_source, relative_path='textures/'+texture.name,
                        sha256=hashlib.sha256(texture.read_bytes()).hexdigest(), bytes=texture.stat().st_size))
            if not copied_textures:
                raise RuntimeError('no image textures found; not accepted as textured asset')
            stage.GetRootLayer().Save()
            root = stage.GetDefaultPrim()
            if not root.IsValid():
                raise RuntimeError('asset has no default prim')
            UsdPhysics.RigidBodyAPI.Apply(root).CreateRigidBodyEnabledAttr(True)
            UsdPhysics.MassAPI.Apply(root).CreateMassAttr(spec.simulation_mass_kg)
            material = UsdShade.Material.Define(stage, str(root.GetPath()) + '/ProbePhysicsMaterial')
            physics_material = UsdPhysics.MaterialAPI.Apply(material.GetPrim())
            physics_material.CreateStaticFrictionAttr(.7)
            physics_material.CreateDynamicFrictionAttr(.5)
            physics_material.CreateRestitutionAttr(0.0)
            for mesh in [p for p in stage.Traverse() if p.IsA(UsdGeom.Mesh)]:
                UsdPhysics.CollisionAPI.Apply(mesh).CreateCollisionEnabledAttr(True)
                UsdPhysics.MeshCollisionAPI.Apply(mesh).CreateApproximationAttr('convexDecomposition')
                UsdShade.MaterialBindingAPI.Apply(mesh).Bind(material, materialPurpose='physics')
            stage.GetRootLayer().Save()
            bbox = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_, UsdGeom.Tokens.render])
            bounds = bbox.ComputeWorldBound(root).ComputeAlignedRange()
            meshes = [p for p in stage.Traverse() if p.IsA(UsdGeom.Mesh)]
            texture_assets = []
            for prim in stage.Traverse():
                for attr in prim.GetAttributes():
                    if attr.GetTypeName() == Sdf.ValueTypeNames.Asset:
                        val = attr.Get()
                        if val:
                            texture_assets.append(dict(attribute=str(attr.GetPath()), authored=val.path,
                                                       resolved=val.resolvedPath))
            with local.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            item.update(status='pass', package_sha256=digest, package_bytes=local.stat().st_size,
                        source_sha256=source_sha256, copied_textures=copied_textures,
                        external_runtime_dependency='Isaac built-in OmniPBR.mdl',
                        physics_modifications=dict(mass_kg=spec.simulation_mass_kg, static_friction=.7,
                            dynamic_friction=.5, collision_approximation='convexDecomposition',
                            cavity_fidelity_validated=False),
                        stage_meters_per_unit=UsdGeom.GetStageMetersPerUnit(stage),
                        stage_up_axis=str(UsdGeom.GetStageUpAxis(stage)), default_prim=str(root.GetPath()),
                        bounds_min=list(bounds.GetMin()), bounds_max=list(bounds.GetMax()),
                        mesh_count=len(meshes), texture_assets=texture_assets,
                        rigid_prims=[str(p.GetPath()) for p in stage.Traverse() if p.HasAPI(UsdPhysics.RigidBodyAPI)],
                        collider_prims=[str(p.GetPath()) for p in stage.Traverse() if p.HasAPI(UsdPhysics.CollisionAPI)])
        except Exception as exc:
            item.update(status='fail', error=str(exc))
        cases.append(item)
        print(json.dumps(item), flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(dict(status='pass' if all(c['status']=='pass' for c in cases) else 'fail',
                       simulation_only=True, cases=cases), stream, indent=2)
finally:
    launcher.app.close(skip_cleanup=True)
