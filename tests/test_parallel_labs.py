"""Single weekly batch blocks, optional project hours, and safe manual edits."""
from collections import Counter
from copy import deepcopy
import csv
import io
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from app import storage
from app.analytics import analyze
from app.demo import presentation_config
from app.domain import Configuration
from app.editing import edit_result
from app.exchange import configuration_csv_v2, configuration_excel, parse_upload
from app.main import app
from app.scheduler import generate, preflight


@pytest.fixture
def config():
    data=presentation_config().model_dump()
    data['groups']=[g for g in data['groups'] if g['id']=='it3A']
    data['batches']=[b for b in data['batches'] if b['group_id']=='it3A']
    data['offerings']=[o for o in data['offerings'] if o['group_id']=='it3A']
    return Configuration(**data)


def solve(config):
    result=generate(config,20,random_seed=42)
    assert result['status']=='feasible',result
    record={'id':1,'name':'Parallel lab plan','config':config.model_dump(),'result':result}
    assert analyze(record)['hard_conflicts']==0
    return record


def test_one_parallel_block_and_whole_division_project(config):
    record=solve(config)
    entries=record['result']['entries']
    labs=[e for e in entries if e['kind']=='lab']
    assert Counter(e['batch_id'] for e in labs)==Counter(b.id for b in config.batches)
    assert len({(e['day'],e['slot'],e['duration']) for e in labs})==1
    assert len({e['teacher_id'] for e in labs})==len({e['room_id'] for e in labs})==3
    assert all(e['batch_id'] is None for e in entries if e['kind']!='lab')
    assert sum(e['duration'] for e in entries if not e['batch_id'] or e['batch_id']=='it3A1')==32
    lecture_days=Counter((e['subject_id'],e['day']) for e in entries if e['kind']=='lecture')
    assert max(lecture_days.values())==1


@pytest.mark.parametrize('problem',['missing','multiple','same_teacher','incomplete_batches','division_lab'])
def test_incomplete_or_conflicting_batch_assignments_explained(config,problem):
    data=config.model_dump();labs=[o for o in data['offerings'] if o['batch_id']]
    if problem=='missing': data['offerings'].remove(labs[0])
    if problem=='multiple': labs[0]['labs']=2
    if problem=='same_teacher': labs[1]['teacher_id']=labs[0]['teacher_id']
    if problem=='incomplete_batches': data['batches'][0]['strength']=19
    if problem=='division_lab': data['offerings'][0]['labs']=1
    result=generate(Configuration(**data),1)
    assert result['status']=='infeasible'
    assert 'BATCH_LAB_BLOCK' in {i['code'] for i in result['issues']}
    assert result['entries']==[]


def test_batch_teaching_is_labs_only(config):
    for field in ('lectures','projects'):
        data=config.model_dump();next(o for o in data['offerings'] if o['batch_id'])[field]=1
        with pytest.raises(ValueError,match='Batches attend labs only'):
            Configuration(**data)


@pytest.mark.parametrize('hours',[2,3,4])
def test_project_hours_reach_solver_and_all_import_formats(config,hours):
    data=config.model_dump();project=next(o for o in data['offerings'] if o['projects'])
    project['project_hours']=hours;c=Configuration(**data)
    record=solve(c)
    assert [e['duration'] for e in record['result']['entries'] if e['kind']=='project']==[hours]
    for suffix,raw in [('csv',configuration_csv_v2(c).encode()),('xlsx',configuration_excel(c)),('json',c.model_dump_json().encode())]:
        parsed=parse_upload(raw,'project.'+suffix)
        assert next(o for o in parsed.offerings if o.projects).project_hours==hours
        assert preflight(parsed)==[]


def test_project_can_be_omitted_and_invalid_hours_explained(config):
    data=config.model_dump();project=next(o for o in data['offerings'] if o['projects'])
    project['project_hours']=2.5
    with pytest.raises(ValueError,match='whole number of teaching periods'):
        Configuration(**data)
    project['project_hours']=5
    result=generate(Configuration(**data),1)
    assert result['status']=='infeasible'
    assert any('unbroken window' in i['problem'] for i in result['issues'])
    data['offerings'].remove(project)
    record=solve(Configuration(**data))
    assert not any(e['kind']=='project' for e in record['result']['entries'])


def test_manual_edits_enforce_common_block_and_keep_original(config):
    record=solve(config);original=deepcopy(record)
    i,e=next((i,e) for i,e in enumerate(record['result']['entries']) if e['kind']=='lab')
    changed,issues=edit_result(record,[SimpleNamespace(entry_index=i,day=(e['day']+1)%5,slot=e['slot'],room_id=e['room_id'])])
    assert changed is None and any('common weekly block' in issue for issue in issues)
    moves=[SimpleNamespace(entry_index=i,day=(e['day']+1)%5,slot=e['slot'],room_id=e['room_id']) for i,e in enumerate(record['result']['entries'])]
    changed,issues=edit_result(record,moves)
    assert issues==[] and changed['source']=='manual'
    assert record==original


def test_old_batch_snapshot_keeps_its_original_policy(config,tmp_path,monkeypatch):
    data=config.model_dump();data['settings']['synchronized_batch_labs']=False
    for o in data['offerings']:
        if o['batch_id']: o['labs']=2
    record=solve(Configuration(**data))
    record['config']['settings'].pop('synchronized_batch_labs')
    monkeypatch.setenv('UNISCHED_DB',str(tmp_path/'legacy.db'))
    with TestClient(app) as client:
        identifier=storage.save_generation('Old weekly pattern',1,record['config'],record['result'])
        old=client.get(f'/api/generations/{identifier}').json()
        assert old['config']['settings']['synchronized_batch_labs'] is False
        assert old['result']==record['result']
        assert client.patch(f'/api/generations/{identifier}/workflow',json={'revision':0,'action':'approve'}).status_code==200


def test_previous_csv_without_project_hours_still_imports(config):
    rows=list(csv.reader(io.StringIO(configuration_csv_v2(config))))
    output=io.StringIO();csv.writer(output).writerows([row[:-1] for row in rows])
    parsed=parse_upload(output.getvalue().encode(),'old.csv')
    assert next(o for o in parsed.offerings if o.projects).project_hours is None
    assert preflight(parsed)==[]


def test_existing_academic_data_keeps_legacy_batch_projects(config,tmp_path,monkeypatch):
    data=config.model_dump();data['settings']['synchronized_batch_labs']=False
    batch=next(o for o in data['offerings'] if o['batch_id']);batch.update(projects=1,project_hours=2)
    Configuration(**data)
    data['settings'].pop('synchronized_batch_labs')
    monkeypatch.setenv('UNISCHED_DB',str(tmp_path/'existing.db'))
    storage.initialize();storage.save_config(data,0)
    with storage.connect() as db: before=db.execute('SELECT body FROM configuration').fetchone()[0]
    restored=storage.get_config()
    assert restored['revision']==1
    assert restored['configuration']['settings']['synchronized_batch_labs'] is False
    assert next(o for o in restored['configuration']['offerings'] if o['id']==batch['id'])['projects']==1
    with storage.connect() as db: assert db.execute('SELECT body FROM configuration').fetchone()[0]==before
