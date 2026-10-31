"""Academic resource rules independent of the solver implementation."""
def elective_code(config, offering):
    subject = next(s for s in config.subjects if s.id == offering.subject_id)
    group = next(g for g in config.groups if g.id == offering.group_id)
    return subject.code if group.semester == 7 and group.division.upper() in ('A','B') and subject.code in config.settings.combined_elective_students else None


def group_options(config, group):
    return sorted({elective_code(config,o) for o in config.offerings if o.group_id == group.id and elective_code(config,o)})


def elective_entry(config, entry):
    return entry['kind']=='lecture' and bool(elective_code(config,next(o for o in config.offerings if o.id==entry['offering_id'])))


def student_units(config, group):
    batches = [b for b in config.batches if b.group_id == group.id]
    units = [b.id for b in batches]
    if sum(b.strength for b in batches) < group.strength or not units:
        units.append('division:'+group.id)
    options=group_options(config,group)
    return [u+"::"+code for u in units for code in options] if options else units

def affected_units(config, offering):
    group = next(g for g in config.groups if g.id == offering.group_id)
    units=student_units(config,group)
    if offering.batch_id: units=[u for u in units if u.split('::')[0]==offering.batch_id]
    code=elective_code(config,offering)
    return [u for u in units if u.endswith('::'+code)] if code else units

def session_specs(config, offering):
    return [('lecture', offering.lectures, config.settings.lecture_slots),
            ('lab', offering.labs, config.settings.lab_slots),
            ('tutorial', offering.tutorials, int(offering.tutorial_hours*60/config.settings.period_minutes) if offering.tutorial_hours is not None else config.settings.lecture_slots),
            ('project', offering.projects, int(offering.project_hours*60/config.settings.period_minutes) if offering.project_hours is not None else config.settings.project_slots)]

def teaching_slots(config, offering):
    return sum(count*duration for _,count,duration in session_specs(config, offering))

def eligible_rooms(config, offering, kind):
    group = next(g for g in config.groups if g.id == offering.group_id)
    if unreserved_project(offering,kind): return []
    size = next(b.strength for b in config.batches if b.id == offering.batch_id) if offering.batch_id else group.strength
    code=elective_code(config,offering) if kind=='lecture' else None
    if code: size=config.settings.combined_elective_students[code]
    fixed = offering.tutorial_room_id if kind == 'tutorial' else group.room_id if kind == 'lecture' else (offering.project_room_id or offering.lab_room_id) if kind == 'project' else offering.lab_room_id
    expected = next(r.kind for r in config.rooms if r.id==offering.project_room_id) if kind == 'project' and offering.project_room_id else 'classroom' if kind in ('lecture','tutorial') else offering.lab_room_type if kind == 'lab' else 'lab'
    teacher=next((t for t in config.teachers if t.id==offering.teacher_id),None)
    required=teacher.preferred_lab_ids if teacher and expected=='lab' and kind in ('lab','project') and teacher.lab_preference_mode=='required' else []
    return [room for room in config.rooms if room.kind == expected and (not required or room.id in required) and (not fixed or room.id == fixed)
            and room.capacity >= size and room.department_id in (None, group.department_id)
            and (not room.eligible_years or (group.semester+1)//2 in room.eligible_years)]


def booking_key(config, offering, kind):
    """Every lab batch reserves its own laboratory and teacher time."""
    code=elective_code(config,offering) if kind=='lecture' else None
    if code:
        group=next(g for g in config.groups if g.id==offering.group_id)
        return ('combined',group.department_id,group.semester,code,offering.teacher_id)
    return ('single',offering.id,kind)


def booking_members(config, offering, kind):
    key=booking_key(config,offering,kind)
    if key[0]=='single': return [offering]
    return [o for o in config.offerings if booking_key(config,o,kind)==key]


def unreserved_project(offering, kind):
    return kind=='project' and offering.teacher_id is None


def lecture_allowed(teacher,kind,start,end):
    return not (teacher and kind=='lecture' and teacher.lecture_start and teacher.lecture_preference_mode=='required') or (start>=teacher.lecture_start and end<=teacher.lecture_end)


def preference_cost(config,offering,kind,room_id,start,end):
    teacher=next((t for t in config.teachers if t.id==offering.teacher_id),None)
    room=next((r for r in config.rooms if r.id==room_id),None)
    group=next(g for g in config.groups if g.id==offering.group_id)
    cost=0
    if teacher:
        if kind=='lecture' and teacher.lecture_start and not (start>=teacher.lecture_start and end<=teacher.lecture_end):cost+=10*teacher.lecture_priority
        if kind in ('lab','project') and room and room.kind=='lab' and teacher.preferred_lab_ids and room_id not in teacher.preferred_lab_ids:cost+=10
    if room:
        year=(group.semester+1)//2
        favored={r.id for r in eligible_rooms(config,offering,kind) if year in r.preferred_years}
        if (favored and room.id not in favored) or (room.preferred_years and year not in room.preferred_years):cost+=1
    return cost


def faculty_workload(config):
    rows={t.id:dict(id=t.id,name=t.name,lecture=0,lab=0,tutorial=0,project=0) for t in config.teachers};seen=set()
    for o in config.offerings:
        if not o.teacher_id:continue
        for kind,count,duration in session_specs(config,o):
            if not count:continue
            key=booking_key(config,o,kind)
            if key in seen:continue
            seen.add(key);rows[o.teacher_id][kind]+=count*duration*config.settings.period_minutes/60
    for t in config.teachers:
        r=rows[t.id];r['total']=sum(r[k] for k in ('lecture','lab','tutorial','project'))
        available=sum(config.settings.period_minutes/60 for day in range(len(config.settings.days)) for p in config.settings.available(day) if config.settings.periods()[p][0]>=t.arrival and config.settings.periods()[p][1]<=t.departure)
        r.update(weekly_limit=t.max_hours,available_hours=available,auto_workload=t.auto_workload)
    return list(rows.values())


def effective_limits(config):
    import math
    config=config.model_copy(deep=True);loads={r['id']:r for r in faculty_workload(config)}
    for t in config.teachers:
        if t.auto_workload:
            t.max_hours=min(60,max(1,math.ceil(loads[t.id]['total'])))
            t.max_daily_slots=max(1,sum(a>=t.arrival and b<=t.departure for a,b in config.settings.periods()))
    return config
