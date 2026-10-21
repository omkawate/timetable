import json
import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient
from app import hints,main
from app.domain import Configuration


def configured():
    with sqlite3.connect(Path(__file__).parents[1]/'data/unisched.db') as db:
        c=Configuration(**json.loads(db.execute('select body from configuration').fetchone()[0]))
    for o in c.offerings:
        if o.id in {'o'+str(i) for i in range(136,145)}:o.lab_room_type='classroom'
    c.settings.start_at_opening=False;c.settings.balanced_days=True
    c.settings.prefer_parallel_batches=True;c.settings.classroom_run_length=2
    c.settings.practical_classroom_codes=[];c.settings.combined_elective_students={'IS':60,'STQA':60}
    return c


def test_display_name_does_not_invalidate_but_assignment_does():
    c=configured();before=c.model_dump();key=hints.fingerprint(c)
    assert hints.reference_entries(c)
    c.teachers[0].name='Corrected display name'
    assert hints.fingerprint(c)==key and hints.reference_entries(c)
    assert before['teachers'][0]['name']!='Corrected display name'
    c.offerings[0].teacher_id=next(t.id for t in c.teachers if t.id!=c.offerings[0].teacher_id)
    assert hints.fingerprint(c)!=key and hints.reference_entries(c) is None


def test_saved_plan_reuse_after_name_correction(monkeypatch,tmp_path):
    monkeypatch.setenv('UNISCHED_DB',str(tmp_path/'db.sqlite'))
    with TestClient(main.app) as client:
        c=configured();revision=client.get('/api/config').json()['revision']
        assert client.put('/api/config',json={'revision':revision,'configuration':c.model_dump()}).status_code==200
        first=client.post('/api/generations',json={'time_limit':5}).json()
        assert first['result']['status']=='feasible'
        current=client.get('/api/config').json();current['configuration']['teachers'][0]['name']='Corrected name'
        assert client.put('/api/config',json=current).status_code==200
        # Prove saved history is reused even without the bundled hint.
        monkeypatch.setattr(hints,'reference_entries',lambda _:None)
        second=client.post('/api/generations',json={'time_limit':5,'continue_latest':False}).json()
        assert second['result']['status']=='feasible'
        assert second['result']['scope']['seed_generation_id']==first['id']
        assert second['result']['summary']['reused_placements']
        assert second['result']['entries']==first['result']['entries']
        assert second['config']['teachers'][0]['name']=='Corrected name'
