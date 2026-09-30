"""Explicit, ephemeral Object-only cooking override; never saves a USD layer."""
from copy import deepcopy

from derive_native_collision_precision import PARAMETERS, PREFIX, stage_contract

API_NAME = 'PhysxConvexDecompositionCollisionAPI'
OBJECT_MESH_PATH = '/World/Case0/Object/_40_large_marker'


def validate_request(enabled, protocol):
    """The CLI and hash-bound protocol must jointly request the exact six values."""
    requested = protocol.get('object_collision_precision_override', False)
    if type(requested) is not bool or enabled is not requested:
        raise ValueError('object collision precision CLI/protocol mismatch')
    configured = protocol.get('object_collision_precision_parameters')
    if enabled:
        if not isinstance(configured, dict) or set(configured) != set(PARAMETERS):
            raise ValueError('exact six object collision precision parameters required')
        if any(type(configured[k]) is not type(v) or configured[k] != v for k, v in PARAMETERS.items()):
            raise ValueError('object collision precision must match existing uniform native parameters')
    elif configured is not None:
        raise ValueError('object collision precision parameters require the explicit override')


def assert_only_object_precision_changed(before, after, mesh_path=OBJECT_MESH_PATH):
    """Exclude exactly six attributes and one API on exactly one Mesh, nothing else."""
    if mesh_path != OBJECT_MESH_PATH or mesh_path not in before or mesh_path not in after:
        raise ValueError('unexpected object precision target')
    a, b = deepcopy(before), deepcopy(after)
    if a[mesh_path]['type'] != 'Mesh' or b[mesh_path]['type'] != 'Mesh':
        raise ValueError('precision target must remain a Mesh')
    if API_NAME in a[mesh_path]['schemas'] or b[mesh_path]['schemas'].count(API_NAME) != 1:
        raise ValueError('expected one newly applied object cooking API')
    b[mesh_path]['schemas'].remove(API_NAME)
    for key in PARAMETERS:
        name = PREFIX + key
        if name not in b[mesh_path]['attributes']:
            raise ValueError('missing explicit precision attribute: ' + name)
        a[mesh_path]['attributes'].pop(name, None)
        b[mesh_path]['attributes'].pop(name)
    if a != b:
        raise ValueError('object cooking override changed an unrelated stage value, relationship, or schema')


def apply_scene_object_precision(stage):
    """Apply six source-independent cooking attributes before reset/physics, with audit."""
    from pxr import Usd, UsdGeom, UsdPhysics, PhysxSchema

    prim = stage.GetPrimAtPath(OBJECT_MESH_PATH)
    if not prim or not prim.IsA(UsdGeom.Mesh) or not prim.HasAPI(UsdPhysics.CollisionAPI):
        raise ValueError('expected original marker Collision Mesh')
    if UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get() != 'convexDecomposition':
        raise ValueError('existing object convex decomposition required')
    if prim.HasAPI(PhysxSchema.PhysxConvexDecompositionCollisionAPI):
        raise ValueError('expected 001 source without authored cooking API')
    before = stage_contract(stage, exclude_precision=False)
    original = {}
    for key in PARAMETERS:
        attribute = prim.GetAttribute(PREFIX + key)
        original[key] = dict(attribute_exists=bool(attribute),
            value=attribute.Get() if attribute else None,
            authored=bool(attribute and attribute.HasAuthoredValueOpinion()))
    if any(item['authored'] for item in original.values()):
        raise ValueError('unexpected authored original object cooking parameter')

    # A separate anonymous stage documents applied-schema fallbacks, not 001 engine defaults.
    reference = Usd.Stage.CreateInMemory()
    reference_mesh = UsdGeom.Mesh.Define(reference, '/Reference').GetPrim()
    reference_api = PhysxSchema.PhysxConvexDecompositionCollisionAPI.Apply(reference_mesh)
    defaults = {key:getattr(reference_api, 'Get' + key[0].upper() + key[1:] + 'Attr')().Get()
                for key in PARAMETERS}
    api = PhysxSchema.PhysxConvexDecompositionCollisionAPI.Apply(prim)
    for key, value in PARAMETERS.items():
        attribute = getattr(api, 'Create' + key[0].upper() + key[1:] + 'Attr')()
        if not attribute.Set(value) or not attribute.HasAuthoredValueOpinion():
            raise ValueError('could not author exact object cooking attribute: ' + key)
    actual = {key:getattr(api, 'Get' + key[0].upper() + key[1:] + 'Attr')().Get() for key in PARAMETERS}
    # USD float attributes round to float32; compare to the same schema's typed authored values.
    for key, expected in PARAMETERS.items():
        ref_attr = getattr(reference_api, 'Create' + key[0].upper() + key[1:] + 'Attr')()
        ref_attr.Set(expected)
        if actual[key] != ref_attr.Get():
            raise ValueError('authored object cooking value mismatch: ' + key)
    after = stage_contract(stage, exclude_precision=False)
    assert_only_object_precision_changed(before, after)
    return dict(mesh_path=OBJECT_MESH_PATH, added_api=API_NAME,
        requested_parameters=dict(PARAMETERS), actual_schema_typed_parameters=actual,
        original_attribute_state=original, original_api_applied=False,
        applied_schema_reference_defaults=defaults, original_unapplied_engine_defaults_verified=False,
        exact_six_attributes_and_one_api_only=True, unrelated_stage_contract_equal=True,
        source_usd_saved=False, physics_steps_during_override=0,
        meters_per_unit=UsdGeom.GetStageMetersPerUnit(stage),
        min_thickness_semantics='Distance in authoring-layer units; actual cooked geometry must be measured, not inferred from this setting.',
        dependent_mass_properties='Source COM/inertia unauthored; runtime automatic COM/inertia may change after recooking and are exported without overrides.')
