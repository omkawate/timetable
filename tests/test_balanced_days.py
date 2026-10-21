from types import SimpleNamespace as N
from app.balance import audit_balance

def config():
    return N(settings=N(balanced_days=True,days=['Mon','Tue','Wed','Thu','Fri'],combined_elective_students={}),
        subjects=[N(id='s',code='TEST')],groups=[N(id='g',strength=20,semester=3)],batches=[N(id='a1',group_id='g',strength=20)],
        offerings=[N(id='o',subject_id='s',group_id='g',batch_id='a1',labs=5)])

def entry(day,kind,slot,duration=1):
    return dict(group_id='g',offering_id='o',day=day,kind=kind,slot=slot,duration=duration)

def balanced():
    return [e for d in range(5) for e in [entry(d,'lecture',0),entry(d,'lab',1,2)]]

def test_balanced_lab_days():
    assert audit_balance(config(),balanced())==[]

def test_reject_lab_only_day():
    es=[e for e in balanced() if not(e['day']==0 and e['kind']=='lecture')]
    assert any('needs a lecture' in x for x in audit_balance(config(),es))

def test_reject_concentrated_practicals():
    es=balanced();es[1]['day']=1
    assert any('spread across' in x for x in audit_balance(config(),es))

def test_tutorial_edge():
    es=balanced()+[entry(0,'tutorial',3)]
    assert audit_balance(config(),es)==[]
    es.append(entry(0,'lecture',4))
    assert any('tutorial must' in x for x in audit_balance(config(),es))

def test_legacy_not_reinterpreted():
    c=config();c.settings.balanced_days=False
    assert audit_balance(c,[entry(0,'lab',0,2)])==[]
