"""Fresh, bounded diagnostic archive with per-member/source hashes. No deletion."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile
from audit_rm65_backup_tar import audit_archive


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(4*1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def preserve(project, staging, batch, directories, evidence, report_path):
    project=Path(project).resolve(); staging=Path(staging).resolve(); report_path=Path(report_path)
    if not re.fullmatch(r'rm65_native_[0-9]{8}_[0-9]{3}',batch): raise ValueError('explicit native batch id required')
    archive=staging/(batch+'.tar'); index=staging/(batch+'.index.json')
    if any(p.exists() for p in (archive,index,report_path)): raise FileExistsError('fresh archive/index/report required')
    records={}
    def add(path,name):
        if not path.is_file() or path.is_symlink(): raise ValueError('regular files only')
        key=batch+'/'+name
        if key in records: raise ValueError('duplicate archive entry')
        records[key]=dict(source=str(path.resolve()),bytes=path.stat().st_size,sha256=digest(path))
    for name in directories:
        relative=Path(name)
        if relative.is_absolute() or '..' in relative.parts or len(relative.parts)!=2:
            raise ValueError('single diagnostic directory required')
        top,leaf=relative.parts
        if not ((top=='generated' and leaf.startswith('native_surface_')) or
                (top=='outputs' and leaf.startswith(('native_','official_model_reference_')))):
            raise ValueError('only native diagnostic/official-reference directories allowed')
        root=(project/relative).resolve(strict=True)
        if not root.is_dir(): raise ValueError('directory missing')
        for p in sorted(root.rglob('*')):
            if p.is_symlink(): raise ValueError('nested symlink forbidden')
            if p.is_file(): add(p,relative.as_posix()+'/'+p.relative_to(root).as_posix())
    for name in evidence:
        relative=Path(name)
        if relative.is_absolute() or '..' in relative.parts or len(relative.parts)!=2 or relative.parts[0]!='results':
            raise ValueError('evidence must be a results file')
        add(project/relative,relative.as_posix())
    total=sum(r['bytes'] for r in records.values())
    if not records or total>500*1024*1024: raise ValueError('empty or exceeds diagnostic 500 MiB bound')
    staging.mkdir(parents=True,exist_ok=True)
    with index.open('x') as stream: json.dump(records,stream,indent=2)
    with archive.open('xb') as stream,tarfile.open(fileobj=stream,mode='w') as tar:
        for name,row in sorted(records.items()): tar.add(row['source'],arcname=name,recursive=False)
    safe=audit_archive(archive,required_prefix=batch,expected_file_count=len(records),expected_total_bytes=total)
    if safe['status']!='pass': raise ValueError('tar path/type/count gate failed')
    with tarfile.open(archive) as tar:
        for member in tar:
            h=hashlib.sha256()
            with tar.extractfile(member) as stream:
                for chunk in iter(lambda:stream.read(4*1024*1024),b''): h.update(chunk)
            row=records[member.name]
            if h.hexdigest()!=row['sha256'] or digest(row['source'])!=row['sha256']:
                raise ValueError('member mismatch or source changed during backup')
    report=dict(schema='native_audit_backup_v1',status='pass',archive_path=str(archive),
        archive_bytes=archive.stat().st_size,archive_sha256=digest(archive),source_index_path=str(index),
        source_index_sha256=digest(index),file_count=len(records),source_bytes=total,
        all_member_hashes_match_source=True,safe_archive_audit=safe,independent_copy_verified=False,
        extraction_restore_tested=False,raw_assets_committed_to_git=False,real_robot_command_sent=False)
    with report_path.open('x') as stream: json.dump(report,stream,indent=2)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,default=Path.cwd()); p.add_argument('--staging',type=Path,required=True)
    p.add_argument('--batch',required=True); p.add_argument('--directory',action='append',default=[])
    p.add_argument('--evidence',action='append',default=[]); p.add_argument('--report',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(preserve(args.project,args.staging,args.batch,args.directory,args.evidence,args.report),indent=2))
