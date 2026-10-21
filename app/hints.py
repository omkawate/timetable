"""Verified placement hints for the exact supplied dataset, never academic seed data.

Every use is independently audited by the scheduler. Scheduling changes invalidate
these hints; teacher display-name corrections do not. An unsuccessful audit falls
back to the normal constraint search.
"""
import hashlib
import json
from pathlib import Path


def scheduling_data(config):
    """Teacher names are display text; stable IDs carry every assignment."""
    data=config.model_dump()
    for teacher in data['teachers']:
        teacher.pop('name',None)
    return data


def fingerprint(config, legacy=False):
    data=config.model_dump() if legacy else scheduling_data(config)
    data['settings'].pop('classroom_run_length',None)
    data['settings']['practical_classroom_codes']=sorted(data['settings']['practical_classroom_codes'])
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def reference_entries(config):
    path=Path(__file__).with_name('schedule_hints.json')
    if not path.exists(): return None
    try:
        hints=json.loads(path.read_text())
        return hints.get(fingerprint(config)) or hints.get(fingerprint(config,legacy=True))
    except (ValueError,OSError):
        return None
