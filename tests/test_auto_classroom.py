import json,sqlite3
from pathlib import Path
from app.domain import Configuration
from app.resources import eligible_rooms
from app.scheduler import generate,preflight
from app.analytics import analyze
from app.exchange import configuration_csv_v2,parse_extended_csv,configuration_excel,parse_upload

def source():
    with sqlite3.connect(Path(__file__).parent/'original_unisched.db') as db:
        return Configuration(**json.loads(db.execute('select body from configuration where id=1').fetchone()[0]))

def test_choice_and_roundtrip():
    c=source();ids={s.id for s in c.subjects if s.code=='2345511'}
    rows=[o for o in c.offerings if o.subject_id in ids and o.labs]
    assert len(rows)==9
    assert all({r.kind for r in eligible_rooms(c,o,'lab')}=={'lab'} for o in rows)
    for o in rows:o.lab_room_type='classroom'
    assert all({r.kind for r in eligible_rooms(c,o,'lab')}=={'classroom'} for o in rows)
    assert all(o.lab_room_type=='lab' for o in c.offerings if o.subject_id not in ids)
    for restored in [parse_extended_csv(configuration_csv_v2(c)),parse_upload(configuration_excel(c),'test.xlsx'),Configuration.model_validate_json(c.model_dump_json())]:
        assert sum(o.lab_room_type=='classroom' for o in restored.offerings)==9
    assert not any(i['code']=='ROOM_POOL_CAPACITY' for i in preflight(c))

def test_generated_classroom_practical_and_audit():
    c=source();o=next(o for o in c.offerings if o.labs and next(s for s in c.subjects if s.id==o.subject_id).code=='2345511')
    o.lab_room_type='classroom'
    c.offerings=[o];c.groups=[g for g in c.groups if g.id==o.group_id];c.batches=[b for b in c.batches if b.group_id==o.group_id]
    r=generate(c,10,random_seed=42)
    assert r['status']=='feasible',r
    assert len(r['entries'])==1
    e=r['entries'][0];assert e['duration']==2 and e['batch_id']==o.batch_id and e['teacher_id']==o.teacher_id
    assert next(room for room in c.rooms if room.id==e['room_id']).kind=='classroom'
    assert analyze({'config':c.model_dump(),'result':r})['hard_conflicts']==0
    e['room_id']=next(room.id for room in c.rooms if room.kind=='lab')
    assert any('ineligible room' in v for v in analyze({'config':c.model_dump(),'result':r})['violations'])
