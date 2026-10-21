"""Single-process generation jobs: deduplicate submissions and resume after refresh.

Timetables themselves remain durable SQLite records. Running jobs belong to this
server process; after a restart clients are told to check saved version history.
"""
from threading import Lock, Thread
from uuid import uuid4
import time
import json
from fastapi import HTTPException

_lock=Lock()
_jobs={}
_active=None


def _public(job):
    return {k:job[k] for k in ('id','status','name','config_revision','time_limit','result_id','error')} | {
        'elapsed_seconds':round((job['finished'] or time.monotonic())-job['started'],1)}


def active():
    with _lock:return {'active':_public(_jobs[_active]) if _active else None}


def get(identifier):
    with _lock:
        if identifier not in _jobs:
            raise HTTPException(404,'This generation job is no longer available, possibly after a server restart. Check Version history for its saved timetable.')
        return _public(_jobs[identifier])


def submit(payload,runner):
    global _active
    signature=json.dumps(payload.model_dump(exclude={'name','time_limit'}),sort_keys=True)
    with _lock:
        if _active:
            job=_jobs[_active]
            if job['signature']==signature:return _public(job)
            raise HTTPException(409,'Another timetable is being generated. Wait for the active job before changing generation settings.')
        identifier=uuid4().hex
        job=dict(id=identifier,signature=signature,status='running',name=payload.name,
                 config_revision=payload.config_revision,time_limit=payload.time_limit,
                 result_id=None,error=None,started=time.monotonic(),finished=None)
        _jobs[identifier]=job;_active=identifier
        # Keep recent outcomes so refreshed pages can retrieve the completed record.
        for old in list(_jobs)[:-20]:del _jobs[old]
    def run():
        global _active
        try:
            record=runner(payload)
            with _lock:job.update(status='completed',result_id=record['id'])
        except Exception as exc:
            message=str(exc.detail) if isinstance(exc,HTTPException) else 'Generation failed. Your saved data is unchanged. '+str(exc)
            with _lock:job.update(status='failed',error=message)
        finally:
            with _lock:
                job['finished']=time.monotonic()
                if _active==identifier:_active=None
    Thread(target=run,name='unisched-generation',daemon=True).start()
    return get(identifier)
