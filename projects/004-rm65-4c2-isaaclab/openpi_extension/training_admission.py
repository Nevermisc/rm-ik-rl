"""Fail closed on explicit development/physics exclusions; preserve legacy reads.

Historical block episodes predate admission metadata. Accepting their old format
for reproduction does NOT certify them as household demonstrations.
"""


def check_training_admission(manifest: dict, report: dict | None = None) -> dict:
    meta = manifest.get('metadata', {})
    report = report or {}
    if meta.get('task_success') is not True:
        raise ValueError('episode is not marked successful')
    records = [('metadata', meta), ('report', report),
               ('report.expert_episode', report.get('expert_episode') or {})]
    reasons = []
    for name, record in records:
        for field in ('training_eligible', 'training_ready', 'unassisted_full_task_complete'):
            if field in record and record[field] is not True:
                reasons.append(f'{name}.{field} is not true')
        for field in ('diagnostic_only', 'evaluation_only'):
            if record.get(field):
                reasons.append(f'{name}.{field}')
        if 'development_only' in str(record.get('evaluation_scope', '')):
            reasons.append(f'{name}.evaluation_scope is development only')
        if record.get('training_blocker'):
            reasons.append(f'{name}.training_blocker')
    # New object probes need a separately reviewed collection/admission contract.
    # Do not promote them by flipping a success bit or copying them to episode_*.
    if meta.get('object_probe') is not None or report.get('object_probe') is not None:
        reasons.append('object probes are not an approved household collection')
    if reasons:
        raise ValueError('training admission rejected: ' + '; '.join(reasons))
    return dict(mode='legacy_reproduction', household_training_certified=False,
                explicit_exclusions_checked=True)
