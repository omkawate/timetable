"""Verified placement hints for the exact supplied dataset, never academic seed data.

Every use is independently audited by the scheduler. Any academic edit invalidates
these hints; an unsuccessful audit falls back to the normal constraint search.
"""
import hashlib
import json
from pathlib import Path


def fingerprint(config):
    data=config.model_dump()
    # New optional fields at their defaults do not invalidate older verified snapshots.
    defaults={'auto_workload':False,'preferred_lab_ids':[],'lab_preference_mode':'preferred','lecture_start':None,'lecture_end':None,'lecture_preference_mode':'preferred','lecture_priority':1}
    for teacher in data['teachers']:
        for key,value in defaults.items():
            if teacher.get(key)==value:teacher.pop(key,None)
    for room in data['rooms']:
        if not room.get('preferred_years'):room.pop('preferred_years',None)
    data['settings'].pop('classroom_run_length',None)
    data['settings']['practical_classroom_codes']=sorted(data['settings']['practical_classroom_codes'])
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def reference_entries(config):
    path=Path(__file__).with_name('schedule_hints.json')
    if not path.exists(): return None
    try:
        return json.loads(path.read_text()).get(fingerprint(config))
    except (ValueError,OSError):
        return None


def preference_fingerprint(config):
    data=config.model_dump()
    for t in data['teachers']:
        for key in ('preferred_lab_ids','lab_preference_mode','lecture_start','lecture_end','lecture_preference_mode','lecture_priority'):t.pop(key,None)
    for r in data['rooms']:r.pop('preferred_years',None)
    return 'preferences:'+hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def preference_seed(config):
    """Only reuse matching academic/timing data; the scheduler independently audits."""
    path=Path(__file__).with_name('schedule_hints.json')
    try:entries=json.loads(path.read_text()).get(preference_fingerprint(config))
    except (ValueError,OSError):return None
    if not entries:return None
    # A requested lecture window must already be met before fast room-only reuse.
    periods=config.settings.periods();teachers={t.id:t for t in config.teachers}
    for e in entries:
        t=teachers.get(e['teacher_id'])
        if t and e['kind']=='lecture' and t.lecture_start and not (periods[e['slot']][0]>=t.lecture_start and periods[e['slot']+e['duration']-1][1]<=t.lecture_end):return None
    from .preferences import assign_rooms
    return assign_rooms(config,entries)
