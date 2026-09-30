from copy import deepcopy

import pytest

from native_object_collision_precision import (API_NAME, OBJECT_MESH_PATH, PARAMETERS, PREFIX,
    assert_only_object_precision_changed, validate_request)


def stages():
    before = {OBJECT_MESH_PATH:dict(type='Mesh', attributes={'points':'unchanged', 'physics:mass':'0.02'},
                                  relationships={'material:binding:physics':['/Material']}, schemas=['PhysicsCollisionAPI']),
              '/World/Robot':dict(type='Xform',attributes={'gain':'1000'},relationships={},schemas=[])}
    after = deepcopy(before)
    after[OBJECT_MESH_PATH]['schemas'].append(API_NAME)
    after[OBJECT_MESH_PATH]['attributes'].update({PREFIX+k:str(v) for k,v in PARAMETERS.items()})
    return before, after


def test_explicit_joint_request():
    protocol = dict(object_collision_precision_override=True, object_collision_precision_parameters=dict(PARAMETERS))
    validate_request(True, protocol)
    validate_request(False, {})
    with pytest.raises(ValueError): validate_request(False, protocol)
    with pytest.raises(ValueError): validate_request(True, {})
    protocol['object_collision_precision_parameters']['hullVertexLimit'] = True
    with pytest.raises(ValueError): validate_request(True, protocol)


def test_exact_target_allowlist_preserves_inputs():
    before, after = stages()
    saved = deepcopy((before, after))
    assert_only_object_precision_changed(before, after)
    assert (before, after) == saved


@pytest.mark.parametrize('mutation', ['other_cook', 'unknown_cook', 'points', 'mass', 'material', 'robot_gain', 'schema', 'extra_prim', 'missing_parameter'])
def test_rejects_every_unrelated_change(mutation):
    before, after = stages()
    mesh = after[OBJECT_MESH_PATH]
    if mutation == 'other_cook': after['/World/Robot']['attributes'][PREFIX+'maxConvexHulls'] = '128'
    elif mutation == 'unknown_cook': mesh['attributes'][PREFIX+'unapproved'] = '1'
    elif mutation == 'points': mesh['attributes']['points'] = 'different'
    elif mutation == 'mass': mesh['attributes']['physics:mass'] = '0.01'
    elif mutation == 'material': mesh['relationships']['material:binding:physics'] = ['/Other']
    elif mutation == 'robot_gain': after['/World/Robot']['attributes']['gain'] = '2000'
    elif mutation == 'schema': mesh['schemas'].append('OtherAPI')
    elif mutation == 'extra_prim': after['/World/Extra'] = dict(type='Xform',attributes={},relationships={},schemas=[])
    elif mutation == 'missing_parameter': mesh['attributes'].pop(PREFIX+'minThickness')
    with pytest.raises(ValueError): assert_only_object_precision_changed(before, after)


def test_cpu_usd_apply_if_available():
    pytest.importorskip('pxr.PhysxSchema')
    from pxr import Usd, UsdGeom, UsdPhysics, PhysxSchema
    from native_object_collision_precision import apply_scene_object_precision
    stage = Usd.Stage.CreateInMemory()
    UsdGeom.SetStageMetersPerUnit(stage, 1.)
    mesh = UsdGeom.Mesh.Define(stage, OBJECT_MESH_PATH).GetPrim()
    UsdPhysics.CollisionAPI.Apply(mesh)
    UsdPhysics.MeshCollisionAPI.Apply(mesh).CreateApproximationAttr().Set('convexDecomposition')
    report = apply_scene_object_precision(stage)
    assert report['exact_six_attributes_and_one_api_only']
    assert report['original_unapplied_engine_defaults_verified'] is False
    assert report['applied_schema_reference_defaults']['maxConvexHulls'] == 32
    assert PhysxSchema.PhysxConvexDecompositionCollisionAPI(mesh).GetMaxConvexHullsAttr().Get() == 128
    with pytest.raises(ValueError): apply_scene_object_precision(stage)
