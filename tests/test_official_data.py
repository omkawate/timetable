"""Supplied college data, tutorial reservations, and generation-only options."""
import csv
import io
from collections import Counter
import pytest
from fastapi.testclient import TestClient
from app.demo import presentation_config, OFFICIAL_CSV
from app.domain import Configuration, parse_csv
from app.exchange import configuration_csv_v2, configuration_excel, parse_upload
from app.scheduler import preflight
from app.main import app
from app.analytics import analyze
from app.exports import pdf, excel


def test_supplied_rows_preserve_faculty_subject_counts_and_tutorial_room():
    c=presentation_config();rows=list(csv.DictReader(io.StringIO(OFFICIAL_CSV.read_text(encoding='utf-8-sig'))))
    assert [len(getattr(c,k)) for k in ('teachers','subjects','groups','batches','rooms','offerings')]==[24,34,8,24,13,191]
    assert c.settings.lab_slots==2 and c.settings.days==['Monday','Tuesday','Wednesday','Thursday','Friday']
    teachers={t.id:t.name for t in c.teachers};subjects={s.id:s for s in c.subjects};rooms={r.id:r for r in c.rooms}
    for row,o in zip(rows,c.offerings):
        assert teachers.get(o.teacher_id,'')==row['teacher_name']
        assert subjects[o.subject_id].code==row['subject_code']
        assert o.labs==int(row['labs_per_week'])
        assert o.lectures+o.tutorials==int(row['lectures_per_week'])
        if o.tutorials: assert rooms[o.tutorial_room_id].name=='710'
    assert sum(o.tutorials for o in c.offerings)==9
    assert sum(o.labs for o in c.offerings)==123
    assert len([o for o in c.offerings if o.projects and o.teacher_id is None])==2
    for ext,body in [('csv',configuration_csv_v2(c).encode()),('xlsx',configuration_excel(c)),('json',c.model_dump_json().encode())]:
        restored=parse_upload(body,'data.'+ext)
        assert Counter((o.lectures,o.labs,o.tutorials,o.projects) for o in restored.offerings)==Counter((o.lectures,o.labs,o.tutorials,o.projects) for o in c.offerings)
        assert sum(o.teacher_id is None for o in restored.offerings)==2
        assert restored.settings==c.settings


@pytest.mark.parametrize('start,capacity',[('09:00',240),('10:00',210)])
def test_two_hour_capacity_is_reported_without_changing_requirements(start,capacity):
    c=presentation_config();c.settings.start=start
    issues=preflight(c)
    shortage=next(i for i in issues if i['code']=='ROOM_POOL_CAPACITY')
    assert '246 periods' in shortage['problem'] and f'{capacity} available' in shortage['problem']
    assert c.settings.lab_slots==2


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('UNISCHED_DB',str(tmp_path/'official.db'))
    with TestClient(app) as client: yield client


def test_fresh_install_preserves_source_and_explains_whole_college_shortage(client):
    before=client.get('/api/config').json()
    assert len(before['configuration']['offerings'])==191
    assert client.get('/api/sample.csv').content==OFFICIAL_CSV.read_bytes()
    assert client.get('/api/demo/csv').content==OFFICIAL_CSV.read_bytes()
    r=client.post('/api/generations',json={'start_time':'10:00','time_limit':5,'flexible_practicals':False}).json()
    assert r['result']['status']=='infeasible' and r['result']['entries']==[]
    assert any(i['code']=='ROOM_POOL_CAPACITY' for i in r['result']['issues'])
    assert r['config']['settings']['start']=='10:00' and r['config']['settings']['lab_slots']==2
    assert r['config']['settings']['classroom_run_length']==2
    assert client.get('/api/config').json()==before


@pytest.mark.parametrize('start',['09:00','10:00'])
def test_scoped_generation_keeps_two_hour_labs_tutorials_and_classroom_runs(client,start):
    before=client.get('/api/config').json()
    group=before['configuration']['groups'][0]['id']
    response=client.post('/api/generations',json={'start_time':start,'group_ids':[group],'time_limit':60})
    assert response.status_code==200,response.text
    record=response.json();r=record['result']
    assert r['status']=='feasible',r
    assert all(e['duration']==2 for e in r['entries'] if e['kind']=='lab')
    a=analyze(record)
    assert a['hard_conflicts']==a['internal_gaps']==0
    assert r['summary']['classroom_optimization']['early_changes']==0
    assert all(d['start']==start for d in a['student_days'])
    c=Configuration(**record['config']);room={r.id:r.name for r in c.rooms}
    tutorials=[e for e in r['entries'] if e['kind']=='tutorial']
    assert len(tutorials)==3 and all(room[e['room_id']]=='710' for e in tutorials)
    assert len(pdf(record))>1000 and len(excel(record))>1000
    assert client.get('/api/config').json()==before
    again=client.post('/api/generations',json={'start_time':start,'group_ids':[group],'time_limit':5}).json()
    assert again['result']['status']=='feasible' and again['result']['summary']['reused_placements']
