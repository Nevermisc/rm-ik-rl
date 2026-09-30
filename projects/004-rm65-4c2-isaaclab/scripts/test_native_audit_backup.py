import pytest
from backup_native_audit_batch import preserve


def setup(tmp_path):
    project=tmp_path/'project'; folder=project/'outputs/native_unit'; folder.mkdir(parents=True)
    (folder/'evidence.txt').write_text('simulation only')
    return project,tmp_path/'archive',tmp_path/'report.json'


def test_valid_and_no_overwrite(tmp_path):
    project,staging,report=setup(tmp_path)
    result=preserve(project,staging,'rm65_native_20260930_099',['outputs/native_unit'],[],report)
    assert result['status']=='pass' and result['file_count']==1
    assert not result['independent_copy_verified']
    with pytest.raises(FileExistsError): preserve(project,staging,'rm65_native_20260930_099',['outputs/native_unit'],[],report)


@pytest.mark.parametrize('path',['../outside','outputs/checkpoint','generated/old_assets','/etc'])
def test_reject_scope_escape(tmp_path,path):
    project,staging,report=setup(tmp_path)
    with pytest.raises(ValueError): preserve(project,staging,'rm65_native_20260930_098',[path],[],report)
