"""Academic resource rules independent of the solver implementation."""
def student_units(config, group):
    batches = [b for b in config.batches if b.group_id == group.id]
    units = [b.id for b in batches]
    if sum(b.strength for b in batches) < group.strength or not units:
        units.append('division:'+group.id)
    return units

def affected_units(config, offering):
    group = next(g for g in config.groups if g.id == offering.group_id)
    return [offering.batch_id] if offering.batch_id else student_units(config, group)

def session_specs(config, offering):
    return [('lecture', offering.lectures, config.settings.lecture_slots),
            ('lab', offering.labs, config.settings.lab_slots),
            ('project', offering.projects, project_duration(config, offering))]

def teaching_slots(config, offering):
    return sum(count*duration for _,count,duration in session_specs(config, offering))

def eligible_rooms(config, offering, kind):
    group = next(g for g in config.groups if g.id == offering.group_id)
    size = next(b.strength for b in config.batches if b.id == offering.batch_id) if offering.batch_id else group.strength
    fixed = group.room_id if kind == 'lecture' else offering.lab_room_id
    expected = 'classroom' if kind == 'lecture' else 'lab'
    return [room for room in config.rooms if room.kind == expected and (not fixed or room.id == fixed)
            and room.capacity >= size and room.department_id in (None, group.department_id)
            and (not room.eligible_years or (group.semester+1)//2 in room.eligible_years)]


def project_duration(config, offering):
    return (int(offering.project_hours*60/config.settings.period_minutes)
            if offering.project_hours is not None else config.settings.project_slots)


def batch_lab_problems(config, group_ids=None):
    """Check complete weekly practical assignments without blocking incremental CRUD."""
    if not config.settings.synchronized_batch_labs:
        return []
    problems = []
    for group in config.groups:
        if group_ids is not None and group.id not in group_ids:
            continue
        batches = [b for b in config.batches if b.group_id == group.id]
        if not batches:
            continue
        label = f'Semester {group.semester}, Division {group.division}'
        offerings = [o for o in config.offerings if o.group_id == group.id]
        if sum(b.strength for b in batches) != group.strength:
            problems.append(f'{label}: lab batches must cover all {group.strength} students.')
        if any(o.labs and not o.batch_id for o in offerings):
            problems.append(f'{label}: assign practicals to batches, not to the whole division.')
        for batch in batches:
            count = sum(o.labs for o in offerings if o.batch_id == batch.id)
            if count != 1:
                problems.append(f'{label}, {batch.name}: needs exactly one lab session per week; assigned {count}.')
        teachers = [o.teacher_id for o in offerings if o.batch_id and o.labs]
        if len(teachers) != len(set(teachers)):
            problems.append(f'{label}: parallel batch labs need different teachers.')
    return problems
