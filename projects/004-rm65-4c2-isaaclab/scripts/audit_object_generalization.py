"""Read-only inventory of source assumptions, raw demonstrations and cached tasks.

No images, trajectories, checkpoints or source files are rewritten. The report
is evidence of automated coverage, not a claim of complete semantic review.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess


PATTERNS = {
    'block_or_cube': r'\b(block|cube|BLOCK_SIZE|BLOCK_MASS)\b',
    'gravity_switch': r'gravity|DisableGravity',
    'privileged_object_pose': r'root_pos_w|target_error_before|target_zone',
    'training_admission': r'training_eligible|training_ready|diagnostic_only',
}


def counts(values):
    return dict(sorted(Counter(json.dumps(v, sort_keys=True) for v in values).items()))


def audit_raw(root):
    manifests = sorted(root.glob('episode_*/metadata.json'))
    if (root / 'metadata.json').is_file():
        manifests = [root / 'metadata.json']
    episodes = []
    for path in manifests:
        manifest = json.loads(path.read_text())
        meta = manifest.get('metadata', {})
        report_path = path.parent / 'task_report.json'
        report = json.loads(report_path.read_text()) if report_path.exists() else {}
        episodes.append(dict(
            path=str(path), metadata_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            prompt=manifest.get('prompt'), frames=manifest.get('frame_count'),
            split=meta.get('collection_split'), object_probe=meta.get('object_probe'),
            reported_block_size=report.get('block_size_m'),
            task_success=meta.get('task_success'),
            unassisted_full_task_complete=meta.get('unassisted_full_task_complete'),
            training_eligible=meta.get('training_eligible'),
            evaluation_scope=meta.get('evaluation_scope'),
            report_training_ready=report.get('training_ready'),
            natural_source_gravity=report.get('natural_source_gravity'),
            moving_gripper_gravity_disabled=report.get('moving_gripper_gravity_disabled'),
            arm_gravity_disabled_through_transport=report.get('arm_gravity_disabled_through_transport'),
            physics_contract=meta.get('physics_contract'),
        ))
    fields = ['prompt', 'split', 'object_probe', 'reported_block_size', 'task_success',
              'unassisted_full_task_complete', 'training_eligible', 'evaluation_scope',
              'report_training_ready', 'natural_source_gravity',
              'moving_gripper_gravity_disabled', 'arm_gravity_disabled_through_transport']
    return dict(root=str(root), episode_count=len(episodes),
                total_frames=sum(e['frames'] or 0 for e in episodes),
                distributions={k: counts(e[k] for e in episodes) for k in fields},
                episodes=episodes)


def audit_sources(project):
    tracked = subprocess.check_output(
        ['git', 'ls-files', '--', 'scripts', 'openpi_extension', 'config'], cwd=project, text=True
    ).splitlines()
    files = []
    for name in tracked:
        path = project / name
        if path.suffix not in {'.py', '.sh', '.json', '.yaml', '.yml'}:
            continue
        content = path.read_text(encoding='utf-8')
        files.append(dict(path=name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                          lines=len(content.splitlines()),
                          pattern_counts={k: len(re.findall(v, content, re.I)) for k, v in PATTERNS.items()}))
    return dict(coverage='all tracked code/config text files in three pipeline directories; pattern scan only',
                tracked_file_count=len(files), files=files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--raw-root', type=Path, action='append', default=[])
    parser.add_argument('--lerobot-root', type=Path, action='append', default=[])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('use a fresh report path')
    cached = []
    for root in args.lerobot_root:
        info = json.loads((root / 'meta/info.json').read_text())
        tasks = [json.loads(s) for s in (root / 'meta/tasks.jsonl').read_text().splitlines() if s.strip()]
        cached.append(dict(root=str(root), episodes=info['total_episodes'], frames=info['total_frames'],
                           task_count=info['total_tasks'], tasks=tasks,
                           all_task_texts_mention_block=all(re.search(r'\bblock\b', t['task'], re.I) is not None for t in tasks),
                           prompt_text_is_not_geometry_evidence=True))
    report = dict(schema='rm65_object_generalization_audit_v1',
                  timestamp_utc=datetime.now(timezone.utc).isoformat(),
                  code_baseline=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=args.project, text=True).strip(),
                  source_scan=audit_sources(args.project), raw=[audit_raw(p) for p in args.raw_root],
                  lerobot=cached, data_modified=False, checkpoint_modified=False,
                  geometry_limit='Missing object metadata is unknown, not proof of household variety or of a cube.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(dict(output=str(args.output), source_files=report['source_scan']['tracked_file_count'],
                          raw_counts={r['root']: r['episode_count'] for r in report['raw']}, lerobot=cached), indent=2))


if __name__ == '__main__':
    main()
