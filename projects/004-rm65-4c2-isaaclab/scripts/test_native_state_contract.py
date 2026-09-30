"""Local synthetic identity fixtures; never training-admitted demonstrations."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from openpi_extension.native_state_contract import (
    MANIFEST_SCHEMA, MODEL_CONTRACT, PROFILE, REQUIRED_ARTIFACTS, SCHEMA,
    inspect_native_state_contract, validate_native_state_contract,
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')


def ref(path, **extra):
    return dict(path=path.name, sha256=sha(path), **extra)


def read(path):
    return json.loads(path.read_text())


def fixture(tmp_path):
    """These bytes stand in for identities only, not physical/source validation."""
    def blob(name, content=b'fixture bytes', **extra):
        path = tmp_path / name
        path.write_bytes(content)
        return ref(path, **extra)

    def manifest(kind, files, **extra):
        path = tmp_path / (kind + '.json')
        write_json(path, dict(schema=MANIFEST_SCHEMA, kind=kind, files=files, **extra))
        return ref(path)

    obj = dict(object_id='fixture_marker', family_id='fixture_elongated',
               geometry_kind='textured_household_mesh', additional_scale=[1, 1, 1],
               physics_assumptions=dict(mass_kg=.02, static_friction=.7, dynamic_friction=.5,
                    restitution=0., collision_approximation='convexDecomposition', mass_is_simulation_assumption=True))
    artifacts = {}
    artifacts['objects'] = manifest('objects', [
        blob('object.usd', role='mesh', object_id=obj['object_id']),
        blob('object.png', role='texture', object_id=obj['object_id']),
    ], objects=[obj])
    camera = dict(schema='rm65_fixed_camera_rig_v1', rig_id='fixture_rig', simulation_only=True,
        hardware_calibrated=False, external=dict(eye_world_m=[0., -1., 1.], target_world_m=[0., 0., .7]),
        wrist=dict(parent_link='link_6', offset_local_m=[0., .1, 0.], forward_local=[0., 0., 1.], up_local=[0., 1., 0.]),
        optics=dict(width=640, height=480, external_focal_length_mm=24., wrist_focal_length_mm=18.,
                    horizontal_aperture_mm=20.955, clipping_range_m=[.01, 10.]))
    timing = dict(schema='rm65_native_timing_v1', physics_dt_s=1 / 120, control_stride_steps=6,
        control_period_s=.05, control_hz=20., timestamp_source='physics_time', observation_boundary='post_physics_pre_next_action',
        action_hold='zero_order_hold', action_validity='observation_boundary_to_next_control_boundary',
        executed_actions_per_chunk=5, reobserve_after_executed_chunk=True,
        advance_physics_while_waiting_for_inference=False)
    stats = dict(norm_stats={key: dict(mean=[0.] * 7, std=[1.] * 7, q01=[-1.] * 7, q99=[1.] * 7)
                            for key in ('state', 'actions')})
    for name, value in (('camera', camera), ('timing', timing), ('norm', stats),
                        ('control', dict(schema='fixture_control_identity_only', simulation_only=True))):
        path = tmp_path / (name + '.json')
        write_json(path, value)
        artifacts[name] = ref(path)
    artifacts['code'] = manifest('code', [blob(role + '.py', content=role.encode(), role=role) for role in
        ('training_config', 'rm65_input_transform', 'openpi_model', 'openpi_transforms', 'openpi_tokenizer')])
    artifacts['base_weights'] = manifest('base_weights', [blob('base.params', role='weights')],
        family='pi05_base', profile='pi05_base', checkpoint_role='released_base')
    groups = [dict(group_id='physical_001', object_id=obj['object_id'], family_id=obj['family_id'], split='train')]
    artifacts['split'] = manifest('split', [blob('split_source.json', b'{"fixture": true}', role='group_source')], groups=groups)
    meta_path = tmp_path / 'episode_metadata.json'
    write_json(meta_path, dict(metadata=dict(source_kind='native_household_demonstration', native_gripper=True,
        diagnostic_only=False, evaluation_only=False, object_id=obj['object_id'], trajectory_group_id='physical_001')))
    artifacts['dataset'] = manifest('dataset', [ref(meta_path, role='episode_metadata'), blob('trajectory.npz', role='trajectory')],
        repo_id='local/native_fixture_not_training', profile=PROFILE, source_kind='native_household_demonstration',
        robot_geometry='native_source_mesh', diagnostic_only=False, evaluation_only=False,
        trajectory_group_ids=['physical_001'], object_ids=[obj['object_id']])
    contract = dict(schema=SCHEMA, status='draft', simulation_only=True, training_allowed=False,
        model=copy.deepcopy(MODEL_CONTRACT), repo_id='local/native_fixture_not_training', artifacts=artifacts,
        normalization=dict(repo_id='local/native_fixture_not_training', profile=PROFILE, method='quantile', fit_split='train',
            dataset_manifest_sha256=artifacts['dataset']['sha256'], split_manifest_sha256=artifacts['split']['sha256']))
    path = tmp_path / 'contract.json'
    write_json(path, contract)
    return path


def alter_artifact(path, name, mutate):
    contract = read(path)
    artifact_path = path.parent / contract['artifacts'][name]['path']
    document = read(artifact_path)
    mutate(document)
    write_json(artifact_path, document)
    contract['artifacts'][name]['sha256'] = sha(artifact_path)
    if name in ('dataset', 'split'):
        contract['normalization'][name + '_manifest_sha256'] = sha(artifact_path)
    write_json(path, contract)


def add_checkpoint(path):
    contract = read(path)
    root = path.parent
    (root / 'trained.params').write_bytes(b'new candidate fixture only')
    (root / 'checkpoint_norm.json').write_bytes((root / 'norm.json').read_bytes())
    checkpoint = dict(schema=MANIFEST_SCHEMA, kind='checkpoint', profile=PROFILE, repo_id=contract['repo_id'],
        model=copy.deepcopy(MODEL_CONTRACT), bindings={k: contract['artifacts'][k]['sha256'] for k in REQUIRED_ARTIFACTS},
        files=[ref(root / 'trained.params', role='weights'), ref(root / 'checkpoint_norm.json', role='norm_stats')])
    write_json(root / 'checkpoint.json', checkpoint)
    contract['artifacts']['checkpoint'] = ref(root / 'checkpoint.json')
    write_json(path, contract)


def assert_closed(result):
    json.dumps(result, allow_nan=False)
    assert result['status'] == 'blocked'
    for field in ('training_allowed', 'normalization_allowed', 'serving_allowed', 'execution_allowed', 'admission_implemented'):
        assert result[field] is False
    assert result['hardware_calibration_required'] is False
    assert result['control_mapping_semantics_validated'] is False
    assert 'native_data_and_unseen_split_admission_not_implemented' in result['admission_blockers']


@pytest.mark.parametrize('purpose', ['inspect', 'norm', 'train', 'serve'])
def test_complete_real_file_identities_do_not_open_any_operation(tmp_path, purpose):
    path = fixture(tmp_path)
    add_checkpoint(path)
    before = {p.name: sha(p) for p in tmp_path.iterdir()}
    result = validate_native_state_contract(path, purpose=purpose, expected_repo_id='local/native_fixture_not_training',
        norm_stats_path=tmp_path / 'norm.json', checkpoint_manifest_path=tmp_path / 'checkpoint.json')
    assert result['contract_readable'] and result['structure_valid'] and result['identities_verified']
    assert result['inspection_status'] == 'pass'
    assert not result['errors']
    assert result['declared_unseen_groups_present'] is False
    assert 'no_declared_unseen_groups' in result['admission_blockers']
    assert before == {p.name: sha(p) for p in tmp_path.iterdir()}
    assert_closed(result)


@pytest.mark.parametrize('name,value', [
    ('profile', 'pi05_rm65_lora'), ('discrete_state_input', False), ('max_token_len', 64),
    ('environment_state_dim', 32), ('environment_action_dim', 32), ('model_action_dim', 7),
    ('action_horizon', 50), ('initialization', 'rm65_v5'), ('pi05', 1),
    ('preprocessing_order', list(reversed(MODEL_CONTRACT['preprocessing_order']))),
])
def test_wrong_legacy_model_or_state_token_configuration_is_rejected(tmp_path, name, value):
    path = fixture(tmp_path)
    contract = read(path)
    contract['model'][name] = value
    write_json(path, contract)
    result = inspect_native_state_contract(path)
    assert not result['structure_valid'] and not result['checks']['fixed_model_profile']
    assert_closed(result)


@pytest.mark.parametrize('artifact,filename', [
    ('camera', 'camera.json'), ('timing', 'timing.json'), ('norm', 'norm.json'),
    ('objects', 'object.usd'), ('objects', 'object.png'), ('code', 'openpi_model.py'),
    ('base_weights', 'base.params'), ('dataset', 'trajectory.npz'), ('dataset', 'episode_metadata.json'),
    ('split', 'split_source.json'), ('control', 'control.json'),
])
def test_actual_bytes_are_hashed_not_just_digest_format(tmp_path, artifact, filename):
    path = fixture(tmp_path)
    (tmp_path / filename).write_bytes(b'tampered after reference was saved')
    result = inspect_native_state_contract(path)
    assert not result['identities_verified']
    assert any(e['code'].startswith(artifact + '.') for e in result['errors'])
    assert_closed(result)


@pytest.mark.parametrize('bad_ref', [None, [], {'path': 'missing.json', 'sha256': 'a' * 64},
    {'path': 'norm.json', 'sha256': 'wrong'}, {'path': '../outside.json', 'sha256': 'a' * 64},
    {'path': 'https://example.invalid/file', 'sha256': 'a' * 64}])
def test_bad_paths_and_hashes_return_blocked_report(tmp_path, bad_ref):
    path = fixture(tmp_path)
    contract = read(path)
    contract['artifacts']['norm'] = bad_ref
    write_json(path, contract)
    result = inspect_native_state_contract(path)
    assert not result['identities_verified']
    assert_closed(result)


@pytest.mark.parametrize('field', ['physics_dt_s', 'control_stride_steps', 'control_period_s', 'control_hz', 'timestamp_source',
    'observation_boundary', 'action_hold', 'action_validity', 'executed_actions_per_chunk',
    'reobserve_after_executed_chunk', 'advance_physics_while_waiting_for_inference'])
def test_missing_time_or_execution_semantic_is_rejected(tmp_path, field):
    path = fixture(tmp_path)
    alter_artifact(path, 'timing', lambda d: d.pop(field))
    result = inspect_native_state_contract(path)
    assert not result['checks']['timing.explicit_execution_semantics']
    assert_closed(result)


def test_timing_period_cannot_mislabel_native_stride_as_legacy_fps(tmp_path):
    path = fixture(tmp_path)
    alter_artifact(path, 'timing', lambda d: d.update(control_stride_steps=12))
    result = inspect_native_state_contract(path)
    assert not result['checks']['timing.explicit_execution_semantics']


@pytest.mark.parametrize('mutate', [
    lambda d: d['external'].update(target_world_m=d['external']['eye_world_m']),
    lambda d: d['wrist'].update(forward_local=[0., 0., 0.]),
    lambda d: d['wrist'].update(forward_local=d['wrist']['up_local']),
])
def test_degenerate_camera_geometry_is_not_a_readable_contract(tmp_path, mutate):
    path = fixture(tmp_path)
    alter_artifact(path, 'camera', mutate)
    result = inspect_native_state_contract(path)
    assert not result['checks']['camera.non_degenerate']


@pytest.mark.parametrize('repo_id', ['../old', 'local/../old', 'local', '', None])
def test_repo_identity_is_not_an_output_path_escape(tmp_path, repo_id):
    path = fixture(tmp_path)
    contract = read(path)
    contract['repo_id'] = repo_id
    write_json(path, contract)
    result = inspect_native_state_contract(path)
    assert not result['checks']['new_explicit_repo_id']
    assert_closed(result)


def test_absurd_timing_values_fail_without_overflow(tmp_path):
    path = fixture(tmp_path)
    alter_artifact(path, 'timing', lambda d: d.update(control_stride_steps=10 ** 400))
    result = inspect_native_state_contract(path)
    assert not result['checks']['timing.explicit_execution_semantics']
    assert_closed(result)


def test_period_frequency_product_overflow_returns_closed_report(tmp_path):
    path = fixture(tmp_path)
    alter_artifact(path, 'timing', lambda d: d.update(physics_dt_s=10 ** 200,
        control_stride_steps=1, control_period_s=10 ** 200, control_hz=10 ** 200))
    result = inspect_native_state_contract(path)
    assert result['inspection_status'] == 'fail'
    assert not result['checks']['timing.explicit_execution_semantics']
    assert_closed(result)


@pytest.mark.parametrize('role', [None, 'untyped_data'])
def test_dataset_needs_verified_file_with_explicit_trajectory_role(tmp_path, role):
    path = fixture(tmp_path)
    def mutate(document):
        if role is None:
            document['files'] = [f for f in document['files'] if f['role'] != 'trajectory']
        else:
            document['files'][1]['role'] = role
    alter_artifact(path, 'dataset', mutate)
    result = inspect_native_state_contract(path)
    assert result['inspection_status'] == 'fail'
    assert not result['identities_verified']
    assert not result['checks']['dataset.actual_trajectory_files_present']
    assert_closed(result)


def test_episode_group_must_belong_to_declared_dataset_not_only_train_split(tmp_path):
    path = fixture(tmp_path)
    alter_artifact(path, 'split', lambda d: d['groups'].append(dict(d['groups'][0], group_id='physical_002')))
    meta_path = tmp_path / 'episode_metadata.json'
    meta = read(meta_path)
    meta['metadata']['trajectory_group_id'] = 'physical_002'
    write_json(meta_path, meta)
    alter_artifact(path, 'dataset', lambda d: d['files'][0].update(sha256=sha(meta_path)))
    result = inspect_native_state_contract(path)
    assert result['identities_verified']
    assert result['inspection_status'] == 'fail'
    assert not result['checks']['dataset.episode_metadata[0].native_training_source_only']
    assert_closed(result)


@pytest.mark.parametrize('field,value', [('diagnostic_only', True), ('evaluation_only', True),
    ('source_kind', 'legacy_reproduction'), ('source_kind', 'native_contact_diagnostic'), ('robot_geometry', 'wide_pads')])
def test_dataset_declared_diagnostic_legacy_or_evaluation_source_rejected(tmp_path, field, value):
    path = fixture(tmp_path)
    alter_artifact(path, 'dataset', lambda d: d.update({field: value}))
    result = inspect_native_state_contract(path)
    assert not result['checks']['dataset.native_training_source_only']


@pytest.mark.parametrize('field,value', [('diagnostic_only', True), ('evaluation_only', True),
    ('native_gripper', False), ('object_probe', {'object_id': 'fixture_marker'}), ('source_kind', 'legacy_reproduction'),
    ('training_ready', False), ('training_eligible', False), ('unassisted_full_task_complete', False),
    ('training_blocker', 'native qualification missing'), ('evaluation_scope', 'household_development_only')])
def test_hash_valid_actual_episode_cannot_hide_excluded_source_behind_clean_manifest(tmp_path, field, value):
    path = fixture(tmp_path)
    meta_path = tmp_path / 'episode_metadata.json'
    meta = read(meta_path)
    meta['metadata'][field] = value
    write_json(meta_path, meta)
    alter_artifact(path, 'dataset', lambda d: d['files'][0].update(sha256=sha(meta_path)))
    result = inspect_native_state_contract(path)
    assert result['identities_verified']
    assert not result['checks']['dataset.episode_metadata[0].native_training_source_only']
    assert_closed(result)


def test_old_150_cube_repo_is_not_a_native_identity(tmp_path):
    path = fixture(tmp_path)
    contract = read(path)
    contract['repo_id'] = 'local/rm65_sim_failure_correction_v5_train'
    write_json(path, contract)
    result = inspect_native_state_contract(path)
    assert not result['checks']['new_explicit_repo_id']


def test_diagnostic_block_is_rejected_even_with_valid_mesh_texture_hashes(tmp_path):
    path = fixture(tmp_path)
    alter_artifact(path, 'objects', lambda d: d['objects'][0].update(object_id='diagnostic_cube'))
    result = inspect_native_state_contract(path)
    assert not result['checks']['objects.objects[0].household_identity']


def test_requested_repo_and_norm_copy_are_bound_to_contract(tmp_path):
    path = fixture(tmp_path)
    (tmp_path / 'wrong_norm.json').write_bytes(b'wrong norm')
    result = inspect_native_state_contract(path, expected_repo_id='local/other', norm_stats_path=tmp_path / 'wrong_norm.json')
    assert not result['checks']['requested_repo_id_matches']
    assert not result['checks']['requested_norm.sha256_matches']


def test_norm_identity_and_dimensions_must_match_seven_dimensional_train_profile(tmp_path):
    path = fixture(tmp_path)
    contract = read(path)
    contract['normalization']['repo_id'] = 'local/other'
    write_json(path, contract)
    alter_artifact(path, 'norm', lambda d: d['norm_stats']['state'].update(q01=[-1.] * 32))
    result = inspect_native_state_contract(path)
    assert not result['checks']['norm.identity_bound_to_train_data']
    assert not result['checks']['norm.seven_dimensional_quantile_statistics']


@pytest.mark.parametrize('field,value', [('profile', 'pi05_rm65_lora'), ('repo_id', 'local/old')])
def test_legacy_checkpoint_mixing_rejected(tmp_path, field, value):
    path = fixture(tmp_path)
    add_checkpoint(path)
    alter_artifact(path, 'checkpoint', lambda d: d.update({field: value}))
    result = inspect_native_state_contract(path, purpose='serve')
    assert not result['checks']['checkpoint.native_profile_and_repo']


def test_checkpoint_norm_copy_must_match_actual_current_norm(tmp_path):
    path = fixture(tmp_path)
    add_checkpoint(path)
    copied = tmp_path / 'checkpoint_norm.json'
    copied.write_text('{"wrong": true}')
    alter_artifact(path, 'checkpoint', lambda d: d['files'][1].update(sha256=sha(copied)))
    result = inspect_native_state_contract(path, purpose='serve')
    assert not result['checks']['checkpoint.norm_copy_matches']
    assert not result['identities_verified']


def test_serve_needs_checkpoint_identity_before_any_operation(tmp_path):
    result = inspect_native_state_contract(fixture(tmp_path), purpose='serve')
    assert not result['checks']['checkpoint.required_for_serve']
    assert_closed(result)


def test_base_initialization_cannot_use_incremental_checkpoint(tmp_path):
    path = fixture(tmp_path)
    alter_artifact(path, 'base_weights', lambda d: d.update(family='pi05_rm65_lora', checkpoint_role='fine_tuned'))
    result = inspect_native_state_contract(path)
    assert not result['checks']['base.explicit_pi05_base_only']


def test_duplicate_trajectory_and_family_cross_split_rejected(tmp_path):
    path = fixture(tmp_path)
    alter_artifact(path, 'split', lambda d: d['groups'].append(dict(d['groups'][0], split='unseen')))
    result = inspect_native_state_contract(path)
    assert not result['checks']['split.groups[1].unique_group']
    assert not result['checks']['split.groups[1].family_disjoint']
    assert_closed(result)


def test_development_groups_cannot_enter_training_dataset(tmp_path):
    path = fixture(tmp_path)
    alter_artifact(path, 'split', lambda d: d['groups'][0].update(split='dev'))
    result = inspect_native_state_contract(path)
    assert not result['checks']['dataset.train_groups_match_split']


def test_training_flag_cannot_open_gate_even_when_all_bytes_match(tmp_path):
    path = fixture(tmp_path)
    contract = read(path)
    contract['training_allowed'] = True
    write_json(path, contract)
    result = inspect_native_state_contract(path, purpose='train')
    assert not result['checks']['draft_and_explicitly_closed']
    assert_closed(result)


@pytest.mark.parametrize('text', ['[]', '{}', '{"schema":1,"schema":2}', '{"model":NaN}', '{"x":1e999}', 'not json'])
def test_unreadable_or_incomplete_contract_fails_without_throwing(tmp_path, text):
    path = tmp_path / 'broken.json'
    path.write_text(text)
    result = inspect_native_state_contract(path)
    assert result['inspection_status'] == 'fail'
    assert_closed(result)


@pytest.mark.parametrize('name,field,value', [
    ('split', 'groups', 1), ('split', 'groups', ['wrong']), ('objects', 'objects', 'wrong'),
    ('objects', 'files', None), ('code', 'files', [None]), ('base_weights', 'files', []),
])
def test_malformed_manifest_structures_never_escape_fail_closed(tmp_path, name, field, value):
    path = fixture(tmp_path)
    alter_artifact(path, name, lambda d: d.update({field: value}))
    result = inspect_native_state_contract(path)
    assert result['inspection_status'] == 'fail'
    assert_closed(result)


def test_relative_symlink_escape_rejected(tmp_path):
    path = fixture(tmp_path)
    outside = tmp_path.parent / (tmp_path.name + '_outside.json')
    outside.write_bytes((tmp_path / 'norm.json').read_bytes())
    link = tmp_path / 'escaping.json'
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip('symlinks unavailable')
    contract = read(path)
    contract['artifacts']['norm'] = dict(path=link.name, sha256=sha(outside))
    write_json(path, contract)
    result = inspect_native_state_contract(path)
    assert not result['checks']['norm.file_readable']
    assert_closed(result)
