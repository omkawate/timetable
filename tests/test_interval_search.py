from test_auto_classroom import source
from app.interval_search import solve_intervals
from app.resources import eligible_rooms
from app.analytics import analyze

def test_interval_search_keeps_real_constraints():
    c=source();g=c.groups[0]
    c.groups=[g];c.batches=[b for b in c.batches if b.group_id==g.id]
    c.offerings=[o for o in c.offerings if o.group_id==g.id]
    c.settings.classroom_run_length=2;c.settings.balanced_days=True;c.settings.start_at_opening=False
    r=solve_intervals(c,15,aligned_labs=True)
    assert r['status']=='feasible',r
    a=analyze({'config':c.model_dump(),'result':r})
    assert a['hard_conflicts']==0,a['violations']
    assert a['internal_gaps']==0 and a['classroom_optimization']['early_changes']==0
    assert all(e['duration']==2 for e in r['entries'] if e['kind']=='lab')

def test_later_arrival_is_not_an_internal_gap():
    c=source();o=next(o for o in c.offerings if o.labs);g=next(g for g in c.groups if g.id==o.group_id)
    c.offerings=[o];c.groups=[g];c.batches=[b for b in c.batches if b.group_id==g.id]
    room=eligible_rooms(c,o,'lab')[0]
    e=dict(offering_id=o.id,group_id=g.id,subject_id=o.subject_id,teacher_id=o.teacher_id,
           batch_id=o.batch_id,kind='lab',duration=2,day=0,slot=2,room_id=room.id)
    c.settings.start_at_opening=False
    r={'status':'feasible','entries':[e]}
    a=analyze({'config':c.model_dump(),'result':r});assert a['hard_conflicts']==0,a['violations']
    c.settings.start_at_opening=True
    assert any('starts after' in v for v in analyze({'config':c.model_dump(),'result':r})['violations'])
