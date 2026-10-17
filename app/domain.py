"""Validated academic data and a single, documented CSV interchange format."""
import csv
import io
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

COLLEGE = 'Datta Meghe College of Engineering, Airoli, Navi Mumbai'
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
PERIODS = [('09:00', '10:00'), ('10:00', '11:00'), ('11:00', '12:00'),
           ('12:00', '13:00'), ('13:45', '14:45'), ('14:45', '15:45'),
           ('15:45', '16:45'), ('16:45', '17:45')]
CSV_FIELDS = ['semester', 'division', 'teacher_name', 'teacher_hours_per_week',
              'teacher_arrival', 'teacher_departure', 'subject_name', 'subject_code',
              'elective', 'classroom', 'lab_room', 'lectures_per_week', 'labs_per_week']

def minutes(value):
    hour, minute = map(int, value.split(':'))
    return hour * 60 + minute

class Record(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    id: str = Field(min_length=1, max_length=80, pattern=r'^[a-zA-Z0-9_-]+$')

    @field_validator('*')
    @classmethod
    def printable_text(cls, value):
        if isinstance(value, str) and any(ord(char) < 32 for char in value):
            raise ValueError('Text fields cannot contain control characters or line breaks.')
        return value

class Teacher(Record):
    name: str = Field(min_length=1, max_length=100)
    max_hours: int = Field(ge=1, le=40, strict=True)
    arrival: str
    departure: str

    @field_validator('arrival', 'departure')
    @classmethod
    def valid_time(cls, value):
        if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', value):
            raise ValueError('Use a 24-hour time such as 09:00 or 17:45.')
        return value

    @model_validator(mode='after')
    def time_order(self):
        if not 540 <= minutes(self.arrival) < minutes(self.departure) <= 1065:
            raise ValueError('Arrival and departure must be ordered within 09:00–17:45.')
        return self

class Subject(Record):
    name: str = Field(min_length=1, max_length=120)
    code: str = Field(min_length=1, max_length=30)
    semester: int = Field(strict=True)
    elective: bool = False

    @field_validator('semester')
    @classmethod
    def semester_allowed(cls, value):
        if value not in (3, 5, 7):
            raise ValueError('Semester must be 3, 5, or 7.')
        return value

class Room(Record):
    name: str = Field(min_length=1, max_length=50)
    kind: str = Field(pattern=r'^(classroom|lab)$')

class Group(Record):
    semester: int = Field(strict=True)
    division: str = Field(min_length=1, max_length=12)
    room_id: str
    _semester = field_validator('semester')(Subject.semester_allowed.__func__)

class Offering(Record):
    group_id: str
    subject_id: str
    teacher_id: str
    lectures: int = Field(ge=0, le=40, strict=True)
    labs: int = Field(ge=0, le=20, strict=True)
    lab_room_id: str | None = None

    @model_validator(mode='after')
    def nonempty(self):
        if self.lectures + self.labs == 0:
            raise ValueError('An assignment needs at least one lecture or lab per week.')
        return self

class Configuration(BaseModel):
    model_config = ConfigDict(extra='forbid')
    teachers: list[Teacher] = Field(default_factory=list, max_length=100)
    subjects: list[Subject] = Field(default_factory=list, max_length=120)
    rooms: list[Room] = Field(default_factory=list, max_length=100)
    groups: list[Group] = Field(default_factory=list, max_length=30)
    offerings: list[Offering] = Field(default_factory=list, max_length=240)

    @model_validator(mode='after')
    def references(self):
        for field in ('teachers', 'subjects', 'rooms', 'groups', 'offerings'):
            items = getattr(self, field)
            if len({item.id for item in items}) != len(items):
                raise ValueError(f'Duplicate IDs in {field}.')
        for field, key in [('teachers', lambda x: x.name.casefold()),
                           ('subjects', lambda x: x.code.casefold()),
                           ('rooms', lambda x: x.name.casefold()),
                           ('groups', lambda x: (x.semester, x.division.casefold()))]:
            items = getattr(self, field)
            if len({key(item) for item in items}) != len(items):
                raise ValueError(f'Duplicate names, codes, or divisions in {field}.')
        teachers = {x.id: x for x in self.teachers}
        subjects = {x.id: x for x in self.subjects}
        rooms = {x.id: x for x in self.rooms}
        groups = {x.id: x for x in self.groups}
        pairs = set()
        for group in self.groups:
            if group.room_id not in rooms or rooms[group.room_id].kind != 'classroom':
                raise ValueError(f'Division {group.division} needs a valid classroom.')
        for item in self.offerings:
            if item.group_id not in groups or item.subject_id not in subjects or item.teacher_id not in teachers:
                raise ValueError(f'Assignment {item.id} references a missing division, subject, or teacher.')
            if groups[item.group_id].semester != subjects[item.subject_id].semester:
                raise ValueError(f'Assignment {item.id}: subject and division semesters must match.')
            if item.labs and (item.lab_room_id not in rooms or rooms[item.lab_room_id].kind != 'lab'):
                raise ValueError(f'Assignment {item.id} needs a valid laboratory.')
            if item.lab_room_id and (item.lab_room_id not in rooms or rooms[item.lab_room_id].kind != 'lab'):
                raise ValueError(f'Assignment {item.id} references an invalid laboratory.')
            pair = (item.group_id, item.subject_id)
            if pair in pairs:
                raise ValueError('Each division/subject pair must have exactly one teacher assignment.')
            pairs.add(pair)
        return self

def parse_csv(raw: bytes) -> Configuration:
    if len(raw) > 1_000_000:
        raise ValueError('CSV must be smaller than 1 MB.')
    try:
        content = raw.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValueError('Save the CSV with UTF-8 encoding.') from exc
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames != CSV_FIELDS:
        raise ValueError('CSV headers must match the template exactly: ' + ', '.join(CSV_FIELDS))
    maps = {key: {} for key in ('teachers', 'subjects', 'rooms', 'groups')}
    offerings = []

    def add(category, key, values):
        existing = maps[category].get(key)
        if existing:
            if {k: v for k, v in existing.items() if k != 'id'} != values:
                raise ValueError(f'Conflicting repeated {category} details for {key}.')
            return existing['id']
        identifier = category[0] + str(len(maps[category]) + 1)
        maps[category][key] = {'id': identifier, **values}
        return identifier

    for row_number, row in enumerate(reader, 2):
        try:
            if len(offerings) >= 240:
                raise ValueError('At most 240 teaching assignments are supported.')
            if None in row or any(v is None for v in row.values()):
                raise ValueError('Incorrect number of CSV columns.')
            row = {k: v.strip() for k, v in row.items()}
            if row['elective'].lower() not in ('true', 'false', 'yes', 'no', '1', '0'):
                raise ValueError('Elective must be true/false, yes/no, or 1/0.')
            semester = int(row['semester'])
            teacher = add('teachers', row['teacher_name'].casefold(), {
                'name': row['teacher_name'], 'max_hours': int(row['teacher_hours_per_week']),
                'arrival': row['teacher_arrival'], 'departure': row['teacher_departure']})
            subject = add('subjects', row['subject_code'].casefold(), {
                'name': row['subject_name'], 'code': row['subject_code'], 'semester': semester,
                'elective': row['elective'].lower() in ('true', 'yes', '1')})
            room = add('rooms', row['classroom'].casefold(), {'name': row['classroom'], 'kind': 'classroom'})
            lab = None
            if row['lab_room']:
                lab = add('rooms', row['lab_room'].casefold(), {'name': row['lab_room'], 'kind': 'lab'})
            group = add('groups', (semester, row['division'].casefold()), {
                'semester': semester, 'division': row['division'].upper(), 'room_id': room})
            offerings.append({'id': f'o{len(offerings)+1}', 'group_id': group, 'subject_id': subject,
                              'teacher_id': teacher, 'lectures': int(row['lectures_per_week']),
                              'labs': int(row['labs_per_week']), 'lab_room_id': lab})
        except (ValueError, KeyError) as exc:
            raise ValueError(f'CSV row {row_number}: {exc}') from exc
    if not offerings:
        raise ValueError('The CSV has no teaching assignments.')
    return Configuration(**{k: list(v.values()) for k, v in maps.items()}, offerings=offerings)

def configuration_csv(config: Configuration):
    maps = {key: {x.id: x for x in getattr(config, key)} for key in ('teachers', 'subjects', 'rooms', 'groups')}
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for item in config.offerings:
        teacher, subject, group = maps['teachers'][item.teacher_id], maps['subjects'][item.subject_id], maps['groups'][item.group_id]
        row = dict(zip(CSV_FIELDS, [group.semester, group.division, teacher.name, teacher.max_hours,
            teacher.arrival, teacher.departure, subject.name, subject.code, str(subject.elective).lower(),
            maps['rooms'][group.room_id].name, maps['rooms'][item.lab_room_id].name if item.lab_room_id else '',
            item.lectures, item.labs]))
        # Protect spreadsheet users from formula interpretation of arbitrary names.
        writer.writerow({k: "'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@', '\t', '\r')) else v for k, v in row.items()})
    return output.getvalue()
