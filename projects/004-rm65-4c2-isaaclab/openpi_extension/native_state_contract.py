"""CPU-only identity inspection for the unadmitted native state_v1 pipeline.

No models, network clients or simulator are imported. All referenced bytes are
hashed locally, including each member of identity manifests. A matching identity
is not evidence of native physics, clean holdouts or valid training data: every
purpose remains blocked in this version, even for a complete contract.

Contract artifacts are file references {path, sha256}. Relative paths resolve
inside the referring JSON file's directory; absolute local paths are permitted.
objects/code/base_weights/dataset/split/checkpoint use an identity manifest with
schema=rm65_native_identity_manifest_v1, kind=<artifact name>, files=[references
with a role]. Camera is a fixed-camera-rig JSON, timing is a native-timing JSON,
and norm is an OpenPI norm_stats JSON. Tests provide a minimal complete fixture.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re


PROFILE = 'pi05_rm65_native_state_v1_lora'
SCHEMA = 'rm65_native_state_contract_v1'
MANIFEST_SCHEMA = 'rm65_native_identity_manifest_v1'
PREPROCESSING_ORDER = (
    'rm65_inputs_state7_actions7', 'delta_actions_six_arm_joints_gripper_absolute',
    'quantile_normalize_state7_actions7', 'tokenize_prompt_with_normalized_state7',
    'pad_state_and_actions_to32',
)
MODEL_CONTRACT = dict(
    profile=PROFILE, pi05=True, discrete_state_input=True, max_token_len=200,
    environment_state_dim=7, environment_action_dim=7, model_action_dim=32,
    action_horizon=10, initialization='pi05_base',
    preprocessing_order=list(PREPROCESSING_ORDER),
)
REQUIRED_ARTIFACTS = ('objects', 'camera', 'timing', 'control', 'norm', 'code', 'base_weights', 'dataset', 'split')
_SHA = re.compile(r'^[0-9a-f]{64}$')
_REPO = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$')
_PURPOSES = ('inspect', 'norm', 'train', 'serve')


def _finite(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _vector(value, size):
    return isinstance(value, list) and len(value) == size and all(_finite(v) for v in value)


def _unique_strings(value):
    return (isinstance(value, list) and bool(value) and all(_nonempty(v) for v in value)
            and len(value) == len(set(value)))


def _strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError('nonfinite JSON constant: ' + value)


def _json_float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError('nonfinite JSON float')
    return parsed


def _product_matches(left, right, expected):
    try:
        product = left * right
        return _finite(product) and math.isclose(product, expected, rel_tol=1e-9, abs_tol=1e-12)
    except OverflowError:
        return False


def _same_model(value):
    return isinstance(value, dict) and json.dumps(value, sort_keys=True) == json.dumps(MODEL_CONTRACT, sort_keys=True)


def _camera_nondegenerate(external, wrist):
    forward, up = wrist['forward_local'], wrist['up_local']
    cross = [forward[1] * up[2] - forward[2] * up[1], forward[2] * up[0] - forward[0] * up[2],
             forward[0] * up[1] - forward[1] * up[0]]
    distances = [math.dist(external['eye_world_m'], external['target_world_m']), math.hypot(*cross)]
    return all(_finite(d) and d > 1e-8 for d in distances)


def _json(path):
    with path.open('r', encoding='utf-8') as stream:
        value = json.load(stream, object_pairs_hook=_strict_pairs, parse_constant=_reject_constant, parse_float=_json_float)
    if not isinstance(value, dict):
        raise ValueError('JSON root must be an object')
    return value


def _sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _local_path(raw, parent):
    if not _nonempty(raw) or '\x00' in raw or '://' in raw or '..' in re.split(r'[\\/]', raw):
        raise ValueError('expected explicit local path without traversal or URL')
    path = Path(raw)
    if not path.is_absolute():
        resolved = (parent / path).resolve(strict=True)
        if not resolved.is_relative_to(parent.resolve()):
            raise ValueError('relative path or symlink escapes referring directory')
    else:
        resolved = path.resolve(strict=True)
    if not resolved.is_file():
        raise ValueError('expected an existing regular file')
    return resolved


def _legacy_identity(value):
    text = str(value).lower()
    return ('pi05_rm65_lora' in text or 'rm65_sim' in text
            or 'failure_correction_v' in text or 'policy_window_v' in text)


def inspect_native_state_contract(contract_path, *, purpose='inspect', expected_repo_id=None,
                                  norm_stats_path=None, checkpoint_manifest_path=None):
    """Inspect a saved contract without starting any operation or opening admission.

    Complete CPU fixtures can have inspection_status='pass', structure_valid=True
    and identities_verified=True. status is nevertheless 'blocked' for inspect,
    norm, train and serve. Callers must check execution_allowed, never inspection.
    Optional CLI-supplied identities are checked against the contract as well.
    This does not authenticate upstream claims or prove physical data validity.
    """
    result = dict(
        schema='rm65_native_state_contract_inspection_v1', status='blocked',
        purpose=purpose if isinstance(purpose, str) else None,
        inspection_status='fail', contract_readable=False, structure_valid=False,
        identities_verified=False, simulation_only=True, training_allowed=False,
        normalization_allowed=False, serving_allowed=False, execution_allowed=False,
        hardware_calibration_required=False, admission_implemented=False,
        control_mapping_semantics_validated=False,
        admission_blockers=['native_data_and_unseen_split_admission_not_implemented'],
        checks={}, errors=[], verified_files=[],
        limitations=[
            'Identity matching does not certify physics, native demonstrations, token coverage or unseen objects.',
            'Base-family and source-kind declarations are checked for consistency, not upstream authenticity.',
            'No training, normalization, serving, model loading or network operation is authorized by this result.',
            'Control file identity is verified; mapping semantics require the separate native_control_contract validator.',
        ],
    )
    errors, checks = result['errors'], result['checks']

    def check(name, passed, category='structure'):
        passed = bool(passed)
        checks[name] = passed
        if not passed:
            errors.append(dict(code=name, category=category))
        return passed

    def reference(ref, parent, label, *, parse=True):
        if not check(label + '.reference_schema', isinstance(ref, dict)
                     and _nonempty(ref.get('path')) and isinstance(ref.get('sha256'), str)
                     and bool(_SHA.fullmatch(ref['sha256'])), 'identity'):
            return None, None
        try:
            path = _local_path(ref['path'], parent)
            actual = _sha256(path)
        except (OSError, ValueError, RuntimeError):
            check(label + '.file_readable', False, 'identity')
            return None, None
        if not check(label + '.sha256_matches', actual == ref['sha256'], 'identity'):
            return None, path
        result['verified_files'].append(dict(role=label, path=str(path), sha256=actual))
        if not parse:
            return True, path
        try:
            return _json(path), path
        except (OSError, ValueError, UnicodeError, RecursionError):
            check(label + '.json_readable', False)
            return None, path

    def members(document, path, kind):
        if not check(kind + '.manifest_schema', isinstance(document, dict)
                     and document.get('schema') == MANIFEST_SCHEMA and document.get('kind') == kind):
            check(kind + '.members_verified', False, 'identity')
            return []
        files = document.get('files')
        if not check(kind + '.member_list', isinstance(files, list) and bool(files)):
            check(kind + '.members_verified', False, 'identity')
            return []
        verified = []
        seen = set()
        for i, item in enumerate(files):
            label = f'{kind}.files[{i}]'
            check(label + '.role', isinstance(item, dict) and _nonempty(item.get('role')))
            ok, member_path = reference(item, path.parent, label, parse=False)
            if ok:
                check(label + '.not_duplicate', member_path not in seen, 'identity')
                seen.add(member_path)
                verified.append((item, member_path))
        return verified

    check('purpose_supported', isinstance(purpose, str) and purpose in _PURPOSES)
    try:
        path = Path(contract_path).resolve(strict=True)
        contract = _json(path)
        result['contract_sha256'] = _sha256(path)
        result['contract_readable'] = True
    except (OSError, TypeError, ValueError, UnicodeError, RuntimeError, RecursionError):
        check('contract_readable', False, 'identity')
        return result
    check('contract_schema', contract.get('schema') == SCHEMA)
    check('draft_and_explicitly_closed', contract.get('status') == 'draft'
          and contract.get('simulation_only') is True and contract.get('training_allowed') is False)
    model = contract.get('model')
    # JSON booleans must not be accepted as integer dimensions (True == 1).
    check('fixed_model_profile', _same_model(model))
    repo_id = contract.get('repo_id')
    check('new_explicit_repo_id', _nonempty(repo_id) and bool(_REPO.fullmatch(repo_id)) and not _legacy_identity(repo_id))
    check('requested_repo_id_matches', expected_repo_id is None or expected_repo_id == repo_id)
    artifacts = contract.get('artifacts')
    if not check('artifact_fields_complete', isinstance(artifacts, dict)
                 and all(name in artifacts for name in REQUIRED_ARTIFACTS)):
        artifacts = artifacts if isinstance(artifacts, dict) else {}

    def artifact_sha(name):
        ref = artifacts.get(name)
        return ref.get('sha256') if isinstance(ref, dict) else None

    docs, paths, file_members = {}, {}, {}
    for name in (*REQUIRED_ARTIFACTS, *(('checkpoint',) if 'checkpoint' in artifacts else ())):
        docs[name], paths[name] = reference(artifacts.get(name), path.parent, name)
        if name in ('objects', 'code', 'base_weights', 'dataset', 'split', 'checkpoint') and docs[name] is not None:
            file_members[name] = members(docs[name], paths[name], name)

    objects = docs.get('objects') or {}
    records = objects.get('objects')
    valid_objects = isinstance(records, list) and bool(records) and all(isinstance(o, dict) for o in records)
    check('objects.declarations_present', valid_objects)
    object_families = {}
    if valid_objects:
        for i, obj in enumerate(records):
            label = f'objects.objects[{i}]'
            oid, family = obj.get('object_id'), obj.get('family_id')
            check(label + '.household_identity', _nonempty(oid) and _nonempty(family)
                  and obj.get('geometry_kind') == 'textured_household_mesh'
                  and not any(word in str(oid).lower() for word in ('block', 'cube', 'native_contact')))
            check(label + '.no_additional_scaling', _vector(obj.get('additional_scale'), 3)
                  and obj['additional_scale'] == [1, 1, 1])
            assumptions = obj.get('physics_assumptions')
            valid_assumptions = (isinstance(assumptions, dict)
                and _finite(assumptions.get('mass_kg')) and assumptions['mass_kg'] > 0
                and all(_finite(assumptions.get(k)) and assumptions[k] >= 0
                        for k in ('static_friction', 'dynamic_friction', 'restitution'))
                and assumptions['restitution'] <= 1
                and isinstance(assumptions.get('mass_is_simulation_assumption'), bool)
                and _nonempty(assumptions.get('collision_approximation')))
            check(label + '.physical_assumptions_explicit', valid_assumptions)
            if _nonempty(oid) and _nonempty(family):
                check(label + '.object_unique', oid not in object_families)
                object_families[oid] = family
            roles = {f['role'] for f, _ in file_members.get('objects', [])
                     if f.get('object_id') == oid and _nonempty(f.get('role'))}
            check(label + '.mesh_and_texture_bytes_verified', {'mesh', 'texture'} <= roles, 'identity')

    camera = docs.get('camera') or {}
    external, wrist, optics = (camera.get(k) for k in ('external', 'wrist', 'optics'))
    camera_valid = check('camera.fixed_geometry_explicit', camera.get('schema') == 'rm65_fixed_camera_rig_v1'
          and _nonempty(camera.get('rig_id')) and camera.get('simulation_only') is True
          and isinstance(camera.get('hardware_calibrated'), bool)
          and isinstance(external, dict) and _vector(external.get('eye_world_m'), 3)
          and _vector(external.get('target_world_m'), 3)
          and isinstance(wrist, dict) and wrist.get('parent_link') in ('link_6', 'tool_base_link')
          and all(_vector(wrist.get(k), 3) for k in ('offset_local_m', 'forward_local', 'up_local'))
          and isinstance(optics, dict) and all(type(optics.get(k)) is int and optics[k] > 0 for k in ('width', 'height'))
          and all(_finite(optics.get(k)) and optics[k] > 0 for k in
                  ('external_focal_length_mm', 'wrist_focal_length_mm', 'horizontal_aperture_mm'))
          and _vector(optics.get('clipping_range_m'), 2) and 0 < optics['clipping_range_m'][0] < optics['clipping_range_m'][1])
    check('camera.non_degenerate', camera_valid and _camera_nondegenerate(external, wrist))
    timing = docs.get('timing') or {}
    dt, stride, period = (timing.get(k) for k in ('physics_dt_s', 'control_stride_steps', 'control_period_s'))
    check('timing.explicit_execution_semantics', timing.get('schema') == 'rm65_native_timing_v1'
          and _finite(dt) and dt > 0 and type(stride) is int and stride > 0
          and _finite(period) and period > 0 and _product_matches(dt, stride, period)
          and _finite(timing.get('control_hz')) and timing['control_hz'] > 0
          and _product_matches(period, timing['control_hz'], 1.)
          and timing.get('timestamp_source') == 'physics_time'
          and timing.get('observation_boundary') == 'post_physics_pre_next_action'
          and timing.get('action_hold') == 'zero_order_hold'
          and timing.get('action_validity') == 'observation_boundary_to_next_control_boundary'
          and type(timing.get('executed_actions_per_chunk')) is int and 1 <= timing['executed_actions_per_chunk'] <= 10
          and timing.get('reobserve_after_executed_chunk') is True
          and isinstance(timing.get('advance_physics_while_waiting_for_inference'), bool))
    check('control.explicit_contract_identity', docs.get('control') is not None, 'identity')

    stats = (docs.get('norm') or {}).get('norm_stats')
    valid_stats = isinstance(stats, dict) and set(stats) == {'state', 'actions'}
    if valid_stats:
        valid_stats = all(isinstance(s, dict) and all(_vector(s.get(k), 7) for k in ('mean', 'std', 'q01', 'q99'))
                          and all(v >= 0 for v in s['std'])
                          and all(a <= b for a, b in zip(s['q01'], s['q99'])) for s in stats.values())
    check('norm.seven_dimensional_quantile_statistics', valid_stats)
    norm_identity = contract.get('normalization')
    check('norm.identity_bound_to_train_data', isinstance(norm_identity, dict)
          and norm_identity.get('repo_id') == repo_id and norm_identity.get('profile') == PROFILE
          and norm_identity.get('method') == 'quantile' and norm_identity.get('fit_split') == 'train'
          and norm_identity.get('dataset_manifest_sha256') == artifact_sha('dataset')
          and norm_identity.get('split_manifest_sha256') == artifact_sha('split'))

    code_roles = {f['role'] for f, _ in file_members.get('code', []) if _nonempty(f.get('role'))}
    check('code.required_sources_verified', {'training_config', 'rm65_input_transform', 'openpi_model',
          'openpi_transforms', 'openpi_tokenizer'} <= code_roles, 'identity')
    base = docs.get('base_weights') or {}
    check('base.explicit_pi05_base_only', base.get('family') == 'pi05_base'
          and base.get('profile') == 'pi05_base' and base.get('checkpoint_role') == 'released_base'
          and any(f.get('role') == 'weights' for f, _ in file_members.get('base_weights', []))
          and all(not _legacy_identity(p) for _, p in file_members.get('base_weights', [])))
    split = docs.get('split') or {}
    groups = split.get('groups')
    valid_groups = isinstance(groups, list) and bool(groups) and all(isinstance(g, dict) for g in groups)
    check('split.trajectory_groups_explicit', valid_groups)
    group_roles, family_roles, object_roles, group_objects = {}, {}, {}, {}
    if valid_groups:
        for i, group in enumerate(groups):
            gid, oid, family, role = (group.get(k) for k in ('group_id', 'object_id', 'family_id', 'split'))
            valid = (_nonempty(gid) and _nonempty(oid) and _nonempty(family)
                     and role in ('train', 'dev', 'unseen') and object_families.get(oid) == family)
            check(f'split.groups[{i}].identity', valid)
            if valid:
                check(f'split.groups[{i}].unique_group', gid not in group_roles)
                check(f'split.groups[{i}].family_disjoint', family not in family_roles or family_roles[family] == role)
                check(f'split.groups[{i}].object_disjoint', oid not in object_roles or object_roles[oid] == role)
                group_roles[gid], family_roles[family], object_roles[oid] = role, role, role
                group_objects[gid] = oid
    result['declared_unseen_groups_present'] = 'unseen' in group_roles.values()
    # Presence is only a declaration, never an assertion that the group was truly unseen.
    if not result['declared_unseen_groups_present']:
        result['admission_blockers'].append('no_declared_unseen_groups')

    dataset = docs.get('dataset') or {}
    check('dataset.native_training_source_only', dataset.get('repo_id') == repo_id
          and dataset.get('profile') == PROFILE and dataset.get('source_kind') == 'native_household_demonstration'
          and dataset.get('robot_geometry') == 'native_source_mesh'
          and dataset.get('diagnostic_only') is False and dataset.get('evaluation_only') is False)
    dataset_groups = dataset.get('trajectory_group_ids')
    check('dataset.train_groups_match_split', _unique_strings(dataset_groups)
          and all(group_roles.get(g) == 'train' for g in dataset_groups))
    check('dataset.object_ids_match_groups', _unique_strings(dataset.get('object_ids'))
          and _unique_strings(dataset_groups)
          and set(dataset['object_ids']) == {group_objects[g] for g in dataset_groups if g in group_objects})
    metadata_files = [(f, p) for f, p in file_members.get('dataset', []) if f.get('role') == 'episode_metadata']
    trajectory_files = [(f, p) for f, p in file_members.get('dataset', []) if f.get('role') == 'trajectory']
    check('dataset.actual_episode_metadata_present', bool(metadata_files), 'identity')
    check('dataset.actual_trajectory_files_present', bool(trajectory_files), 'identity')
    for i, (_, metadata_path) in enumerate(metadata_files):
        try:
            metadata = _json(metadata_path)
            metadata = metadata.get('metadata', metadata)
        except (OSError, ValueError, UnicodeError, RecursionError):
            metadata = None
        check(f'dataset.episode_metadata[{i}].native_training_source_only', isinstance(metadata, dict)
              and metadata.get('source_kind') == 'native_household_demonstration'
              and metadata.get('native_gripper') is True
              and metadata.get('diagnostic_only') is False and metadata.get('evaluation_only') is False
              and metadata.get('object_probe') is None
              and all(k not in metadata or metadata[k] is True
                      for k in ('training_ready', 'training_eligible', 'unassisted_full_task_complete'))
              and not metadata.get('training_blocker')
              and 'development' not in str(metadata.get('evaluation_scope', '')).lower()
              and _nonempty(metadata.get('trajectory_group_id'))
              and _unique_strings(dataset_groups) and metadata['trajectory_group_id'] in dataset_groups
              and group_roles.get(metadata['trajectory_group_id']) == 'train'
              and group_objects.get(metadata['trajectory_group_id']) == metadata.get('object_id'))

    if purpose == 'serve' or checkpoint_manifest_path is not None:
        check('checkpoint.required_for_serve', 'checkpoint' in artifacts)
    if 'checkpoint' in artifacts:
        checkpoint = docs.get('checkpoint') or {}
        check('checkpoint.native_profile_and_repo', checkpoint.get('profile') == PROFILE
              and checkpoint.get('repo_id') == repo_id and _same_model(checkpoint.get('model')))
        bindings = checkpoint.get('bindings')
        check('checkpoint.all_contract_identities_bound', isinstance(bindings, dict)
              and all(bindings.get(k) == artifact_sha(k) for k in REQUIRED_ARTIFACTS))
        copies = [f for f, _ in file_members.get('checkpoint', []) if f.get('role') == 'norm_stats']
        check('checkpoint.norm_copy_matches', len(copies) == 1
              and copies[0].get('sha256') == artifact_sha('norm'), 'identity')
        check('checkpoint.weights_verified', any(f.get('role') == 'weights'
              for f, _ in file_members.get('checkpoint', [])), 'identity')
        check('checkpoint.not_legacy_path', all(not _legacy_identity(p) for _, p in file_members.get('checkpoint', [])))
    for label, supplied, artifact in (('requested_norm', norm_stats_path, 'norm'),
                                      ('requested_checkpoint', checkpoint_manifest_path, 'checkpoint')):
        if supplied is not None:
            _, supplied_path = reference(dict(path=str(supplied), sha256=artifact_sha(artifact)), path.parent, label, parse=False)
            if artifact == 'checkpoint':
                check(label + '.path_matches', supplied_path is not None and supplied_path == paths.get(artifact), 'identity')
    result['structure_valid'] = not any(e['category'] == 'structure' for e in errors)
    result['identities_verified'] = (checks.get('artifact_fields_complete', False)
        and all(docs.get(k) is not None for k in REQUIRED_ARTIFACTS)
        and not any(e['category'] == 'identity' for e in errors))
    result['inspection_status'] = 'pass' if result['structure_valid'] and result['identities_verified'] else 'fail'
    return result


def validate_native_state_contract(contract_path, *, purpose, **kwargs):
    """Shared preflight entry point; execution_allowed remains False in this version."""
    return inspect_native_state_contract(contract_path, purpose=purpose, **kwargs)
