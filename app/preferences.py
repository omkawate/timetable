"""Room preference optimization at fixed session times; no teacher/time changes."""
from collections import defaultdict
from ortools.sat.python import cp_model
from .resources import eligible_rooms,booking_key,preference_cost,unreserved_project
from .classrooms import require_classroom_runs


def assign_rooms(config,entries,locked=(),seconds=5):
    if not any(t.preferred_lab_ids for t in config.teachers) and not any(r.preferred_years for r in config.rooms):return entries
    model=cp_model.CpModel();offerings={o.id:o for o in config.offerings};by_booking={};busy=defaultdict(list);candidates=[];costs=[]
    fixed={(e['offering_id'],e['kind'],e['day'],e['slot']):e['room_id'] for e in locked}
    periods=config.settings.periods()
    for i,e in enumerate(entries):
        o=offerings[e['offering_id']]
        if unreserved_project(o,e['kind']):continue
        key=(booking_key(config,o,e['kind']),e['day'],e['slot'])
        rooms=eligible_rooms(config,o,e['kind']);fixed_room=fixed.get((o.id,e['kind'],e['day'],e['slot']))
        if fixed_room:rooms=[r for r in rooms if r.id==fixed_room]
        if key not in by_booking:
            choices=[]
            for room in rooms:
                v=model.NewBoolVar('room');choices.append((v,room.id));model.AddHint(v,room.id==e['room_id'])
                for p in range(e['slot'],e['slot']+e['duration']):busy[room.id,e['day'],p].append(v)
                cost=preference_cost(config,o,e['kind'],room.id,periods[e['slot']][0],periods[e['slot']+e['duration']-1][1]);costs.append(cost*v)
            model.AddExactlyOne([v for v,_ in choices]);by_booking[key]=choices
        for v,room_id in by_booking[key]:candidates.append((v,{**e,'room_id':room_id,'index':i}))
    for choices in busy.values():model.Add(sum(choices)<=1)
    enabled=model.NewBoolVar('continuity');model.Add(enabled==1)
    require_classroom_runs(model,config,candidates,{g.id for g in config.groups}-{e['group_id'] for e in locked},enabled)
    model.Minimize(sum(costs));solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=seconds;solver.parameters.num_search_workers=4
    if solver.Solve(model) not in (cp_model.OPTIMAL,cp_model.FEASIBLE):return entries
    result=[dict(e) for e in entries]
    for v,e in candidates:
        if solver.BooleanValue(v):result[e['index']]['room_id']=e['room_id']
    return result


def report(config,entries):
    offerings={o.id:o for o in config.offerings};periods=config.settings.periods();missed=[];seen=set()
    for e in entries:
        o=offerings[e['offering_id']];key=(booking_key(config,o,e['kind']),e['day'],e['slot'])
        if key in seen:continue
        seen.add(key)
        cost=preference_cost(config,o,e['kind'],e['room_id'],periods[e['slot']][0],periods[e['slot']+e['duration']-1][1])
        if cost:missed.append({'offering_id':o.id,'kind':e['kind'],'day':config.settings.days[e['day']],'time':periods[e['slot']][0],'room_id':e['room_id'],'penalty':cost})
    return {'unmet_preferences':missed,'note':'Required choices are mandatory. Preferred choices may be missed to keep a complete clash-free timetable; see the listed sessions.'}
