"""Simulation gravity contract, with pure validation and lazy USD inspection."""
import math

GRAVITY_M_S2 = (0.0, 0.0, -9.81)


def validate_strict_options(options):
    required = ('natural_source_gravity', 'enable_moving_gripper_gravity', 'unassisted_release')
    forbidden = ('disable_arm_gravity_during_approach', 'disable_arm_gravity_through_transport',
                 'collision_bypass_during_approach', 'initialize_at_grasp')
    errors = [f'{k} must be enabled' for k in required if getattr(options, k) is not True]
    errors += [f'{k} is diagnostic assistance' for k in forbidden if getattr(options, k)]
    if options.target_collision_enable_stage != 'initial':
        errors.append('target collision must be enabled from initial scene creation')
    if errors:
        raise ValueError('strict gravity contract: ' + '; '.join(errors))


def validate_runtime_snapshot(snapshot, required_body_paths, expected_mass):
    errors = []
    gravity = snapshot.get('gravity_m_s2', [])
    if len(gravity) != 3 or any(not math.isfinite(v) or abs(v-e) > 1e-5
                              for v, e in zip(gravity, GRAVITY_M_S2)):
        errors.append('scene gravity is not (0, 0, -9.81) m/s^2')
    bodies = snapshot.get('rigid_bodies', {})
    for path in required_body_paths:
        if path not in bodies:
            errors.append('missing required rigid body: ' + path)
    for path, body in bodies.items():
        if body.get('gravity_disabled') is not False:
            errors.append('gravity disabled or unverified: ' + path)
        if body.get('rigid_body_enabled') is not True or body.get('kinematic_enabled') is not False:
            errors.append('non-dynamic body: ' + path)
    colliders = snapshot.get('object_colliders', {})
    if not colliders or any(enabled is not True for enabled in colliders.values()):
        errors.append('object collision missing or disabled')
    masses = snapshot.get('object_runtime_masses_kg', [])
    if len(masses) != 1 or not math.isfinite(masses[0]) or not math.isclose(masses[0], expected_mass, rel_tol=1e-4):
        errors.append('runtime object mass does not match declared mass')
    if snapshot.get('stage_meters_per_unit') != 1.0 or snapshot.get('stage_up_axis') != 'Z':
        errors.append('scene must use meters and Z-up')
    return dict(status='pass' if not errors else 'fail', errors=errors,
                limitation='Checks scene/body settings and PhysX mass; not a friction, motor or free-fall calibration.')


def inspect_runtime(sim, stage, obj):
    from pxr import UsdGeom, UsdPhysics, PhysxSchema
    direction, magnitude = sim.get_physics_context().get_gravity()
    bodies, colliders = {}, {}
    for prim in stage.Traverse():
        path = str(prim.GetPath())
        in_robot = path == '/World/Robot' or path.startswith('/World/Robot/')
        in_object = path == '/World/Cube' or path.startswith('/World/Cube/')
        if (in_robot or in_object) and prim.HasAPI(UsdPhysics.RigidBodyAPI):
            rigid = UsdPhysics.RigidBodyAPI(prim)
            # Strict mode explicitly authors this attribute; missing evidence is not a pass.
            gravity = PhysxSchema.PhysxRigidBodyAPI(prim).GetDisableGravityAttr().Get()
            bodies[path] = dict(gravity_disabled=gravity,
                               rigid_body_enabled=rigid.GetRigidBodyEnabledAttr().Get(),
                               kinematic_enabled=rigid.GetKinematicEnabledAttr().Get())
        if in_object and prim.HasAPI(UsdPhysics.CollisionAPI):
            colliders[path] = UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get()
    return dict(gravity_m_s2=[float(v * magnitude) for v in direction], rigid_bodies=bodies,
                object_colliders=colliders,
                object_runtime_masses_kg=obj.root_physx_view.get_masses().detach().cpu().reshape(-1).tolist(),
                stage_meters_per_unit=UsdGeom.GetStageMetersPerUnit(stage),
                stage_up_axis=str(UsdGeom.GetStageUpAxis(stage)))
