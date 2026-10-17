"""CP-SAT scheduling with hard constraints and honest infeasibility reporting."""
import math
import time
from collections import defaultdict
from ortools.sat.python import cp_model
from .domain import Configuration, DAYS, PERIODS, minutes

def issue(code, problem, suggestion):
    return {'code': code, 'problem': problem, 'suggestion': suggestion}

def preflight(config: Configuration):
    problems = []
    if not config.offerings or not config.groups:
        return [issue('EMPTY_DATA', 'There are no teaching assignments to schedule.',
                      'Import the sample CSV or add divisions, teachers, subjects, and assignments.')]
    teacher_hours, group_hours, room_hours, elective_hours = (defaultdict(int) for _ in range(4))
    groups = {g.id: g for g in config.groups}
    subjects = {s.id: s for s in config.subjects}
    for item in config.offerings:
        total = item.lectures + item.labs * 2
        teacher_hours[item.teacher_id] += total
        group_hours[item.group_id] += total
        room_hours[groups[item.group_id].room_id] += item.lectures
        if item.labs:
            room_hours[item.lab_room_id] += item.labs * 2
        if subjects[item.subject_id].elective:
            elective_hours[subjects[item.subject_id].semester] += total
    for teacher in config.teachers:
        hours = teacher_hours[teacher.id]
        available = sum(minutes(a) >= minutes(teacher.arrival) and minutes(b) <= minutes(teacher.departure)
                        for a, b in PERIODS) * len(DAYS)
        if hours > teacher.max_hours:
            problems.append(issue('TEACHER_LOAD', f'{teacher.name} has {hours} assigned hours, above the {teacher.max_hours}-hour weekly limit.',
                f'Reassign at least {hours-teacher.max_hours} hours to another teacher, reduce the requirements, or raise the limit if college policy permits.'))
        if hours > available:
            problems.append(issue('TEACHER_AVAILABILITY', f'{teacher.name} needs {hours} hours but {teacher.arrival}–{teacher.departure} provides only {available} complete teaching periods per week.',
                'Extend the teacher’s availability or reassign some subjects to another available teacher.'))
        if any(o.teacher_id == teacher.id and o.labs for o in config.offerings):
            valid_pair = any(minutes(PERIODS[p][0]) >= minutes(teacher.arrival) and
                             minutes(PERIODS[p+1][1]) <= minutes(teacher.departure) for p in (0,1,2,4,5,6))
            if not valid_pair:
                problems.append(issue('LAB_AVAILABILITY', f'{teacher.name} has no two-hour window for a laboratory.',
                                      'Provide two consecutive available periods on the same side of recess, or reassign the lab.'))
    for group in config.groups:
        hours = group_hours[group.id]
        label = f'Semester {group.semester}, Division {group.division}'
        if hours > 40:
            problems.append(issue('DIVISION_LOAD', f'{label} needs {hours} hours; the week contains 40 periods.',
                                  'Reduce lecture/lab requirements. Each lab uses two hours.'))
        if not hours:
            problems.append(issue('NO_ASSIGNMENTS', f'{label} has no teaching assignments.', 'Add at least one subject assignment or remove the unused division.'))
    for room in config.rooms:
        if room_hours[room.id] > 40:
            problems.append(issue('ROOM_CAPACITY', f'{room.name} needs {room_hours[room.id]} hours, exceeding its 40-period capacity.',
                                  'Assign some divisions or practicals to a different room.'))
    for semester, hours in elective_hours.items():
        if hours > 40:
            problems.append(issue('ELECTIVE_CAPACITY', f'Semester {semester} needs {hours} separate elective periods, but only 40 exist.',
                                  'Reduce elective contact hours or division count. Electives in a semester cannot run simultaneously.'))
    return problems

def generate(config: Configuration, time_limit=20):
    started = time.monotonic()
    problems = preflight(config)
    if problems:
        return {'status': 'infeasible', 'entries': [], 'issues': problems, 'solutions': [],
                'summary': {}, 'elapsed_seconds': round(time.monotonic()-started, 3)}
    model = cp_model.CpModel()
    teachers = {x.id: x for x in config.teachers}
    subjects = {x.id: x for x in config.subjects}
    groups = {x.id: x for x in config.groups}
    coverage = defaultdict(list)
    candidates = []
    assumptions = {}

    def assumption(name, diagnostic):
        literal = model.NewBoolVar(name)
        model.AddAssumption(literal)
        assumptions[literal.Index()] = diagnostic
        return literal

    for item in config.offerings:
        teacher, subject, group = teachers[item.teacher_id], subjects[item.subject_id], groups[item.group_id]
        label = f'{subject.code}, semester {group.semester} {group.division}, {teacher.name}'
        required = assumption('required_'+item.id, issue('ASSIGNMENT_CONFLICT',
            f'{label}: {item.lectures} lectures and {item.labs} two-hour labs are part of the conflicting requirements.',
            'Review this assignment alongside the other listed constraints; change its teacher, room, availability, or weekly counts.'))
        for kind, count, duration in [('lecture', item.lectures, 1), ('lab', item.labs, 2)]:
            if count == 0:
                continue
            choices = []
            room = group.room_id if kind == 'lecture' else item.lab_room_id
            for day in range(5):
                for slot in range(8):
                    if duration == 2 and slot not in (0, 1, 2, 4, 5, 6):
                        continue
                    if minutes(PERIODS[slot][0]) < minutes(teacher.arrival) or minutes(PERIODS[slot+duration-1][1]) > minutes(teacher.departure):
                        continue
                    var = model.NewBoolVar(f'{item.id}_{kind}_{day}_{slot}')
                    choices.append(var)
                    entry = {'offering_id': item.id, 'group_id': group.id, 'subject_id': subject.id,
                             'teacher_id': teacher.id, 'room_id': room, 'day': day, 'slot': slot,
                             'duration': duration, 'kind': kind}
                    candidates.append((var, entry))
                    for offset in range(duration):
                        for resource, key in [('group', group.id), ('teacher', teacher.id), ('room', room)]:
                            coverage[resource, key, day, slot+offset].append(var)
                        if subject.elective:
                            coverage['elective', group.semester, day, slot+offset].append(var)
            model.Add(sum(choices) == count).OnlyEnforceIf(required)

    for (resource, key, day, slot), variables in coverage.items():
        if resource != 'elective':
            model.Add(sum(variables) <= 1)
    for semester in {s.semester for s in config.subjects if s.elective}:
        separate = assumption(f'elective_{semester}', issue('SEPARATE_ELECTIVES',
            f'Semester {semester} requires a separate slot for every elective session across all its divisions.',
            'Reduce elective hours or adjust assignments/teacher availability to create more distinct elective slots.'))
        for day in range(5):
            for slot in range(8):
                model.Add(sum(coverage['elective', semester, day, slot]) <= 1).OnlyEnforceIf(separate)

    peak = model.NewIntVar(0, 8, 'largest_daily_load')
    for group in config.groups:
        no_gaps = assumption('no_gaps_'+group.id, issue('CONTIGUOUS_DAY',
            f'Semester {group.semester} {group.division} must start at 09:00 with no gaps except recess.',
            'Make teachers available in the morning, choose other rooms/teachers, or adjust weekly requirements.'))
        hours = sum(o.lectures+2*o.labs for o in config.offerings if o.group_id == group.id)
        for day in range(5):
            busy = []
            for slot in range(8):
                value = model.NewBoolVar(f'busy_{group.id}_{day}_{slot}')
                model.Add(value == sum(coverage['group', group.id, day, slot]))
                busy.append(value)
            for slot in range(7):
                model.Add(busy[slot] >= busy[slot+1]).OnlyEnforceIf(no_gaps)
            if hours >= 5:
                model.Add(busy[0] == 1).OnlyEnforceIf(no_gaps)
            model.Add(sum(busy) <= peak)
    model.Minimize(peak)
    # Fix assumption literals for the normal search so presolve and symmetry
    # reduction can work fully. Retain a separate model for conflict analysis.
    diagnostic_model = model.Clone()
    model.ClearAssumptions()
    for index in assumptions:
        model.Add(model.GetBoolVarFromProtoIndex(index) == 1)
    model.Add(peak >= max(math.ceil(sum(o.lectures+2*o.labs for o in config.offerings
                                     if o.group_id == g.id)/5) for g in config.groups))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 4
    solver.parameters.random_seed = 42
    result = solver.Solve(model)
    elapsed = round(time.monotonic()-started, 3)
    if result == cp_model.INFEASIBLE:
        diagnostic_model.ClearObjective()
        diagnostic_solver = cp_model.CpSolver()
        diagnostic_solver.parameters.max_time_in_seconds = max(0.1, time_limit - elapsed)
        diagnostic_solver.parameters.num_search_workers = 1
        diagnostic_result = diagnostic_solver.Solve(diagnostic_model)
        core = diagnostic_solver.SufficientAssumptionsForInfeasibility() if diagnostic_result == cp_model.INFEASIBLE else []
        elapsed = round(time.monotonic()-started, 3)
        diagnostics = [assumptions[i] for i in core if i in assumptions]
        return {'status': 'infeasible', 'entries': [], 'issues': diagnostics or [issue('CONSTRAINT_CONFLICT',
            'The combined teacher, classroom, lab, and slot requirements cannot be satisfied.',
            'Review shared teachers and rooms and their availability, then adjust assignments.')],
            'solutions': [], 'summary': {}, 'elapsed_seconds': elapsed,
            'explanation': 'Proven infeasible. The listed constraints form a sufficient conflict set, which may not be the smallest possible set. Suggestions require your changes; no constraints were relaxed.'}
    if result not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {'status': 'timeout', 'entries': [], 'issues': [issue('SEARCH_LIMIT',
            'The search time limit was reached without a complete timetable. This does not prove generation is impossible.',
            'Retry with a longer search limit, or reduce the number of shared teachers and rooms.')],
            'solutions': [], 'summary': {}, 'elapsed_seconds': elapsed}
    entries = [entry for var, entry in candidates if solver.BooleanValue(var)]
    entries.sort(key=lambda e: (e['group_id'], e['day'], e['slot']))
    return {'status': 'feasible', 'entries': entries, 'issues': [], 'elapsed_seconds': elapsed,
            'solutions': [
                'Placed every requested lecture and two-hour lab without overlapping a teacher, division, or room.',
                'Kept each division’s teaching periods consecutive from 09:00, with only the fixed 13:00–13:45 recess. Days may finish early.',
                'Reserved separate periods for all elective sessions within each semester, including across divisions.',
                'Respected teacher arrival/departure times and weekly teaching-hour limits. Labs never cross recess.',
                f'Balanced the week to a maximum of {solver.Value(peak)} teaching hours per division per day.'
            ], 'summary': {'sessions': len(entries), 'teaching_hours': sum(e['duration'] for e in entries),
                           'divisions': len(config.groups), 'teachers': len({e['teacher_id'] for e in entries}),
                           'max_daily_hours': solver.Value(peak), 'balance_optimal': result == cp_model.OPTIMAL,
                           'algorithm': 'Google OR-Tools CP-SAT'}}
