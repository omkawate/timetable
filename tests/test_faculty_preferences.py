import copy,json,sqlite3
from pathlib import Path
from fastapi.testclient import TestClient
from app import main,storage
from app.domain import Configuration
from app.resources import faculty_workload,effective_limits,eligible_rooms
from app.scheduler import generate,preflight
from app.analytics import analyze
from app.preferences import assign_rooms
from app.exchange import configuration_csv_v2,parse_extended_csv,configuration_excel,parse_upload


def example():
    return Configuration(**{
        'teachers':[{'id':'t','name':'Faculty','max_hours':1,'arrival':'09:45','departure':'17:00','auto_workload':True,'preferred_lab_ids':['lab2'],'lab_preference_mode':'required','lecture_start':'10:00','lecture_end':'13:00','lecture_preference_mode':'required'}],
        'subjects':[{'id':'s','name':'Subject','code':'SUB','semester':3}],
        'rooms':[{'id':'r','name':'705','kind':'classroom','preferred_years':[2]},{'id':'r2','name':'709','kind':'classroom'}, {'id':'lab','name':'701','kind':'lab'},{'id':'lab2','name':'902','kind':'lab'}],
        'groups':[{'id':'g','semester':3,'division':'A','strength':60}],
        'batches':[{'id':'b','group_id':'g','name':'A1','strength':60}],
        'offerings':[{'id':'o','group_id':'g','subject_id':'s','teacher_id':'t','lectures':3,'labs':0},{'id':'pr','group_id':'g','subject_id':'s','teacher_id':'t','batch_id':'b','lectures':0,'labs':2}],
        'settings':{'start_at_opening':False,'classroom_run_length':2,'spread_lectures':True}})


def test_required_rooms_and_times_generation_audit_and_workload():
    c=example();assert faculty_workload(c)[0]['total']==7
    assert effective_limits(c).teachers[0].max_hours==7
    assert effective_limits(c).teachers[0].max_daily_slots==6
    assert not [x for x in preflight(c) if x['code']=='TEACHER_LOAD']
    r=generate(c,10,random_seed=42);assert r['status']=='feasible',r
    r['entries']=assign_rooms(c,r['entries'])
    assert not analyze({'config':c.model_dump(),'result':r})['hard_conflicts']
    for e in r['entries']:
        if e['kind']=='lab':assert e['room_id']=='lab2' and e['duration']==2
        else:assert c.settings.periods()[e['slot']][0]>='10:00' and c.settings.periods()[e['slot']+e['duration']-1][1]<='13:00';assert e['room_id']=='r'
    bad=copy.deepcopy(r);next(e for e in bad['entries'] if e['kind']=='lab')['room_id']='lab'
    assert analyze({'config':c.model_dump(),'result':bad})['hard_conflicts']
    bad=copy.deepcopy(r);next(e for e in bad['entries'] if e['kind']=='lecture')['slot']=0
    assert analyze({'config':c.model_dump(),'result':bad})['hard_conflicts']


def test_preferences_round_trip_and_real_capacity_not_hidden():
    c=example()
    for restored in [parse_extended_csv(configuration_csv_v2(c)),parse_upload(configuration_excel(c),'test.xlsx')]:
        assert restored.teachers[0].lecture_start=='10:00'
        # CSV reconstructs room identifiers, so compare the resolved names.
        assert {r.name for r in eligible_rooms(restored,restored.offerings[0],'lab')}=={'902'}
    c.teachers[0].arrival='16:45';c.teachers[0].departure='17:45'
    assert preflight(c)


def test_reset_revision_confirmation_and_backup(monkeypatch,tmp_path):
    monkeypatch.setenv('UNISCHED_DB',str(tmp_path/'db.sqlite'))
    storage.initialize();storage.save_config(example().model_dump(),0)
    with TestClient(main.app) as client:
        assert client.post('/api/reset-academic-data',json={'revision':1,'confirmation':'wrong'}).status_code==422
        assert client.post('/api/reset-academic-data',json={'revision':0,'confirmation':'DELETE ALL DATA'}).status_code==409
        response=client.post('/api/reset-academic-data',json={'revision':1,'confirmation':'DELETE ALL DATA'});assert response.status_code==200
        result=response.json();assert not result['configuration']['teachers'] and not result['configuration']['offerings']
        backup=json.loads((tmp_path/'backups'/result['backup']).read_text());assert backup['configuration']['teachers'][0]['name']=='Faculty'
        assert client.get('/api/config').json()['revision']==2


def test_soft_window_falls_back_and_required_year_is_enforced():
    from app.preferences import report
    c=example();c.teachers[0].lecture_start='09:00';c.teachers[0].lecture_end='10:00';c.teachers[0].lecture_preference_mode='preferred'
    r=generate(c,10,random_seed=42);assert r['status']=='feasible'
    assert report(c,r['entries'])['unmet_preferences']
    for room in c.rooms:
        if room.kind=='classroom':room.eligible_years=[4]
    assert any(p['code']=='ROOM_ELIGIBILITY' for p in preflight(c))


def test_shared_lectures_count_once_even_if_lab_assignment_is_first():
    c=example().model_dump();c['subjects'][0].update(semester=7,code='IS',elective=True);c['groups'][0]['semester']=7
    c['groups'].append({**c['groups'][0],'id':'g2','division':'B'})
    lecture=c['offerings'][0];practical=c['offerings'][1]
    c['offerings']=[practical,lecture,{**lecture,'id':'other','group_id':'g2'}]
    c['settings']['combined_elective_students']={'IS':60}
    row=faculty_workload(Configuration(**c))[0]
    assert row['lecture']==3 and row['lab']==4 and row['total']==7
