import time
from threading import Event
from fastapi.testclient import TestClient
from app import main, generation_jobs

def wait_done(client,identifier):
    for _ in range(200):
        r=client.get('/api/generation-jobs/'+identifier).json()
        if r['status']!='running' and client.get('/api/generation-jobs/active').json()['active'] is None:return r
        time.sleep(.01)
    raise AssertionError('Job did not finish')

def test_duplicate_requests_and_recovery(monkeypatch,tmp_path):
    monkeypatch.setenv('UNISCHED_DB',str(tmp_path/'data.db'))
    entered=Event();release=Event();calls=[]
    def runner(payload):
        calls.append(payload);entered.set();assert release.wait(5)
        return {'id':123}
    monkeypatch.setattr(main,'generate_timetable',runner)
    with TestClient(main.app) as client:
        try:
            first=client.post('/api/generation-jobs',json={}).json();assert entered.wait(2)
            second=client.post('/api/generation-jobs',json={}).json()
            assert second['id']==first['id'] and len(calls)==1
            assert client.get('/api/generation-jobs/active').json()['active']['id']==first['id']
            assert client.post('/api/generation-jobs',json={'start_at_opening':True}).status_code==409
        finally:release.set()
        r=wait_done(client,first['id']);assert r['status']=='completed' and r['result_id']==123
        assert client.get('/api/generation-jobs/'+first['id']).json()['result_id']==123

def test_failure_releases_job_and_stale_input_rejected(monkeypatch,tmp_path):
    monkeypatch.setenv('UNISCHED_DB',str(tmp_path/'data.db'))
    def fail(payload):raise ValueError('test failure')
    monkeypatch.setattr(main,'generate_timetable',fail)
    with TestClient(main.app) as client:
        assert client.post('/api/generation-jobs',json={'config_revision':999}).status_code==409
        first=client.post('/api/generation-jobs',json={}).json()
        assert wait_done(client,first['id'])['status']=='failed'
        monkeypatch.setattr(main,'generate_timetable',lambda payload:{'id':124})
        second=client.post('/api/generation-jobs',json={}).json()
        assert wait_done(client,second['id'])['status']=='completed'
        assert client.get('/api/generation-jobs/missing-after-restart').status_code==404
