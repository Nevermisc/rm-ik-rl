import json
from summarize_household_session import summarize


def test_diagnostic_is_not_a_task_win(tmp_path):
    for suffix, status in [('trial','fail'),('free','diagnostic')]:
        folder=tmp_path/('rm65_household_dev_'+suffix)
        folder.mkdir()
        (folder/'task_report.json').write_text(json.dumps({'status':status,'pi05_used':False}))
    summary=summarize(tmp_path)
    assert summary['task_trial_count']==1
    assert summary['diagnostic_count']==1
    assert summary['task_pass_count']==0
    assert not summary['deployment_accepted']


def test_wrong_support_filter_is_not_validated(tmp_path):
    folder=tmp_path/'rm65_household_dev_support'
    folder.mkdir()
    (folder/'task_report.json').write_text(json.dumps({'status':'fail',
        'development_pad_calibration':{'source_support_contact_by_body':{'pad':{'peak_n':0.}}}}))
    summary=summarize(tmp_path)
    assert summary['cases'][0]['support_sensor_filter_validated'] is False
