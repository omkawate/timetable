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
            ('tutorial', offering.tutorials, int(offering.tutorial_hours*60/config.settings.period_minutes) if offering.tutorial_hours is not None else config.settings.lecture_slots),
            ('project', offering.projects, int(offering.project_hours*60/config.settings.period_minutes) if offering.project_hours is not None else config.settings.project_slots)]

def teaching_slots(config, offering):
    return sum(count*duration for _,count,duration in session_specs(config, offering))

def eligible_rooms(config, offering, kind):
    group = next(g for g in config.groups if g.id == offering.group_id)
    if unreserved_project(offering,kind): return []
    size = next(b.strength for b in config.batches if b.id == offering.batch_id) if offering.batch_id else group.strength
    classroom_mode=classroom_practical(config,offering,kind)
    if classroom_mode:
        members=booking_members(config,offering,kind)
        size=sum(next(b.strength for b in config.batches if b.id==o.batch_id) if o.batch_id else group.strength for o in members)
    fixed = offering.tutorial_room_id if kind == 'tutorial' else group.room_id if kind == 'lecture' else (offering.project_room_id or offering.lab_room_id) if kind == 'project' else offering.lab_room_id
    expected = next(r.kind for r in config.rooms if r.id==offering.project_room_id) if kind == 'project' and offering.project_room_id else 'classroom' if kind in ('lecture','tutorial') else 'lab'
    if classroom_mode: expected='classroom'
    return [room for room in config.rooms if room.kind == expected and (not fixed or room.id == fixed)
            and room.capacity >= size and room.department_id in (None, group.department_id)
            and (not room.eligible_years or (group.semester+1)//2 in room.eligible_years)]


def classroom_practical(config, offering, kind):
    subject=next(s for s in config.subjects if s.id==offering.subject_id)
    return kind=='lab' and not offering.lab_room_id and subject.code in config.settings.practical_classroom_codes


def booking_key(config, offering, kind):
    """Joint instruction is allowed only for the same division, subject and professor."""
    if offering.batch_id and classroom_practical(config,offering,kind):
        return ('joint',offering.group_id,offering.subject_id,offering.teacher_id,offering.labs)
    return ('single',offering.id,kind)


def booking_members(config, offering, kind):
    key=booking_key(config,offering,kind)
    if key[0]=='single': return [offering]
    return [o for o in config.offerings if booking_key(config,o,kind)==key]


def unreserved_project(offering, kind):
    return kind=='project' and offering.teacher_id is None
