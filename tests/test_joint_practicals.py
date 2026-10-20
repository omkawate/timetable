import copy
import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.analytics import analyze
from app.demo import presentation_config
from app.hints import fingerprint,reference_entries
from app.resources import booking_key
from app.domain import Configuration
from app.exports import pdf,excel
from app.assistant import local_advice


def test_full_official_timetable_and_independent_project(tmp_path,monkeypatch):
    monkeypatch.setenv('UNISCHED_DB',str(tmp_path/'full.db'))
    with TestClient(app) as client:
        before=client.get('/api/config').json()
        record=client.post('/api/generations',json={'name':'All college divisions','time_limit':5}).json()
        result=record['result'];assert result['status']=='feasible',result
        assert len(result['scope']['scheduled_group_ids'])==8 and result['scope']['remaining_group_ids']==[]
        a=analyze(record);assert a['hard_conflicts']==a['internal_gaps']==0,a['violations']
        assert a['classroom_optimization']['classroom_changes']==0
        assert record['config']['teachers']==before['configuration']['teachers']
        assert record['config']['offerings']==before['configuration']['offerings']
        assert all(e['duration']==2 for e in result['entries'] if e['kind']=='lab')
        projects=[e for e in result['entries'] if e['kind']=='project']
        assert len(projects)==4 and all(e['duration']==4 and e['teacher_id'] is None and e['room_id'] is None for e in projects)
        assert len(pdf(record))>1000 and len(excel(record))>1000
        index=next(i for i,e in enumerate(result['entries']) if e['kind']=='project')
        assert 'independent project time' in local_advice([record],'Where is project?',index)[0]
        assert client.get('/api/config').json()==before
        c=Configuration(**record['config']);assert reference_entries(c)
        c.teachers[0].max_hours+=1;assert reference_entries(c) is None
        # Removing a batch or moving it away from a shared session is not silently accepted.
        broken=copy.deepcopy(record);c=Configuration(**record['config'])
        o=next(o for o in c.offerings if booking_key(c,o,'lab')[0]=='joint')
        e=next(e for e in broken['result']['entries'] if e['offering_id']==o.id and e['kind']=='lab');e['day']=(e['day']+1)%5
        assert analyze(broken)['hard_conflicts']>0
