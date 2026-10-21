"""Compact interval model for interchangeable rooms and complete fresh plans.

Each actual session has one interval instead of a Boolean for every possible
room/time. Student-day head/tail intervals enforce no internal gaps and the selected
opening-time or flexible-arrival policy. The normal search handles heterogeneous/locked room configurations.
"""
from collections import defaultdict
import math
from ortools.sat.python import cp_model
from .domain import minutes
from .resources import (session_specs,booking_key,booking_members,affected_units,
                        eligible_rooms,student_units,unreserved_project,elective_code)
from .classrooms import (instructional_room_pool,interchangeable_labs,
                         allocate_instruction_intervals,allocate_lab_intervals)


def solve_intervals(config,time_limit,random_seed=42,aligned_labs=False):
    s=config.settings;periods=s.periods();width=len(periods);days=len(s.days)
    if s.blocked:return None
    classrooms=instructional_room_pool(config,[])
    labs=interchangeable_labs(config,[])
    if not classrooms or not labs:return None
    class_ids={r.id for r in classrooms};lab_ids={r.id for r in labs}
    model=cp_model.CpModel();tasks=[];seen=set();by_teacher=defaultdict(list);by_student=defaultdict(list)
    by_room=defaultdict(list);by_elective=defaultdict(list);teachers={t.id:t for t in config.teachers}
    subjects={x.id:x for x in config.subjects};groups={x.id:x for x in config.groups}
    for o in config.offerings:
        for kind,count,duration in session_specs(config,o):
            key=booking_key(config,o,kind)
            if not count or key in seen:continue
            seen.add(key);members=booking_members(config,o,kind)
            units=set(u for member in members for u in affected_units(config,member))
            rooms=eligible_rooms(config,o,kind);ids={r.id for r in rooms}
            if unreserved_project(o,kind):room_key=None;room_id=None
            elif ids==lab_ids:room_key='labs';room_id=labs[0].id
            elif class_ids<=ids:room_key='classrooms';room_id=classrooms[0].id
            elif len(ids)==1 and not ids & (class_ids|lab_ids):room_id=rooms[0].id;room_key='fixed:'+room_id
            else:return None
            teacher=teachers.get(o.teacher_id)
            domain=[d*width+p for d in range(days) for p in range(width) if s.fits(d,p,duration) and (not aligned_labs or kind!='lab' or p%duration==0)
                and (not teacher or (minutes(periods[p][0])>=minutes(teacher.arrival)
                and minutes(periods[p+duration-1][1])<=minutes(teacher.departure)))]
            if not domain:return {'status':'infeasible','entries':[]}
            previous=None;series=[]
            for index in range(count):
                name=f'{o.id}_{kind}_{index}'
                start=model.NewIntVarFromDomain(cp_model.Domain.FromValues(domain),name)
                end=model.NewIntVar(0,days*width,name+'_end');model.Add(end==start+duration)
                interval=model.NewIntervalVar(start,duration,end,name+'_interval')
                day=model.NewIntVar(0,days-1,name+'_day');model.AddDivisionEquality(day,start,width)
                on=[]
                for d in range(days):
                    b=model.NewBoolVar(name+f'_on_{d}');model.Add(day==d).OnlyEnforceIf(b);model.Add(day!=d).OnlyEnforceIf(b.Not());on.append(b)
                if previous is not None:model.Add(start>previous)
                previous=start
                task=dict(start=start,end=end,interval=interval,day=day,on=on,duration=duration,kind=kind,
                          members=members,units=units,room_id=room_id,teacher_id=o.teacher_id)
                tasks.append(task);series.append(task)
                if teacher:by_teacher[teacher.id].append(task)
                for u in units:by_student[u].append(task)
                if room_key:by_room[room_key].append(task)
                if subjects[o.subject_id].elective and not elective_code(config,o):
                    group=groups[o.group_id];by_elective[group.department_id,group.semester].append(task)
            if s.spread_lectures and kind in ('lecture','tutorial'):
                for d in range(days):model.Add(sum(t['on'][d] for t in series)<=math.ceil(count/days))
    for key,items in by_room.items():
        capacity=len(labs) if key=='labs' else len(classrooms) if key=='classrooms' else 1
        model.AddCumulative([t['interval'] for t in items],[1]*len(items),capacity)
    for items in by_elective.values():model.AddNoOverlap([t['interval'] for t in items])
    for tid,items in by_teacher.items():
        model.AddNoOverlap([t['interval'] for t in items])
        for d in range(days):model.Add(sum(t['duration']*t['on'][d] for t in items)<=teachers[tid].max_daily_slots)
    # Concurrent A+B elective alternatives retain their existing synchronized policy.
    alternatives=defaultdict(dict)
    for t in tasks:
        o=t['members'][0];code=elective_code(config,o) if t['kind']=='lecture' else None
        if code:
            group=groups[o.group_id];alternatives[group.department_id,group.semester].setdefault(code,[]).append(t)
    for family in alternatives.values():
        series=list(family.values())
        for others in series[1:]:
            for a,b in zip(series[0],others):model.Add(a['start']==b['start'])
    daily_load={};day_offsets={}
    for unit,items in by_student.items():
        intervals=[t['interval'] for t in items]
        total=sum(t['duration'] for t in items)
        for d in range(days):
            load=model.NewIntVar(1 if total>=days else 0,width,f'{unit}_{d}_load')
            model.Add(load==sum(t['duration']*t['on'][d] for t in items));daily_load[unit,d]=load
            offset=model.NewIntVar(0,0 if s.start_at_opening else width,'student_arrival');day_offsets[unit,d]=offset
            model.Add(offset+load<=width)
            intervals.append(model.NewIntervalVar(d*width,offset,d*width+offset,'student_day_head'))
            tail_start=model.NewIntVar(d*width,(d+1)*width,'tail_start');model.Add(tail_start==d*width+offset+load)
            tail_size=model.NewIntVar(0,width,'tail_size');model.Add(tail_size==width-offset-load)
            intervals.append(model.NewIntervalVar(tail_start,tail_size,(d+1)*width,'student_day_tail'))
            if s.balanced_days:
                practicals=[t for t in items if t['kind']=='lab']
                daily_practical=sum(t['on'][d] for t in practicals)
                model.Add(daily_practical<=math.ceil(len(practicals)/days))
                if len(practicals)>=days:model.Add(daily_practical>=1)
        model.AddNoOverlap(intervals)
        if s.balanced_days:
            for t in items:
                if t['kind']!='tutorial':continue
                at_start=model.NewBoolVar('tutorial_at_day_start')
                for d in range(days):
                    model.Add(t['start']==d*width+day_offsets[unit,d]).OnlyEnforceIf([at_start,t['on'][d]])
                    model.Add(t['end']==d*width+day_offsets[unit,d]+daily_load[unit,d]).OnlyEnforceIf([at_start.Not(),t['on'][d]])
    if s.balanced_days:
        for g in config.groups:
            items=[t for t in tasks if any(o.group_id==g.id for o in t['members'])]
            for d in range(days):
                lecture_count=sum(t['on'][d] for t in items if t['kind']=='lecture')
                for t in items:
                    if t['kind']=='lab':model.Add(lecture_count>=1).OnlyEnforceIf(t['on'][d])
    # Channel finite start domains into a period grid. These redundant constraints
    # give SAT propagation precise room/teacher occupancy before interval bounds fix.
    grid=defaultdict(list)
    for t in tasks:
        proto=model.Proto().variables[t['start'].Index()]
        values=[v for i in range(0,len(proto.domain),2) for v in range(proto.domain[i],proto.domain[i+1]+1)]
        choices=[]
        for value in values:
            b=model.NewBoolVar('session_start_choice');choices.append(b)
            model.Add(t['start']==value).OnlyEnforceIf(b)
            for q in range(value,value+t['duration']):
                if t['teacher_id']:grid['teacher',t['teacher_id'],q].append(b)
                for u in t['units']:grid['student',u,q].append(b)
                room=t['room_id']
                if room:grid['room',room,q].append(b)
        model.AddExactlyOne(choices)
    for (kind,key,q),choices in grid.items():
        cap=len(labs) if kind=='room' and key==labs[0].id else len(classrooms) if kind=='room' and key==classrooms[0].id else 1
        model.Add(sum(choices)<=cap)
    # Days have identical availability in this supported (unblocked) calendar.
    # A global weekday permutation can always put the first division's loads in
    # descending order, removing equivalent day permutations without removing plans.
    first_units=student_units(config,config.groups[0])
    day_totals=[sum(daily_load[u,d] for u in first_units if (u,d) in daily_load) for d in range(days)]
    for a,b in zip(day_totals,day_totals[1:]):model.Add(a>=b)
    solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=max(.001,time_limit)
    solver.parameters.num_search_workers=4;solver.parameters.random_seed=random_seed
    solver.parameters.stop_after_first_solution=True
    status=solver.Solve(model)
    if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        return {'status':'infeasible' if status==cp_model.INFEASIBLE else 'timeout','entries':[]}
    entries=[]
    for t in tasks:
        start=solver.Value(t['start'])
        for o in t['members']:
            entries.append(dict(offering_id=o.id,group_id=o.group_id,subject_id=o.subject_id,teacher_id=o.teacher_id,
                batch_id=o.batch_id,kind=t['kind'],duration=t['duration'],day=start//width,slot=start%width,room_id=t['room_id']))
    entries=allocate_lab_intervals(entries,labs)
    entries=allocate_instruction_intervals(config,entries,classrooms)
    return {'status':'feasible','entries':entries,'peak':max(solver.Value(v) for v in daily_load.values())}
