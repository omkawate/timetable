# UniSched

**Campus, in sync.** A working university timetable planner for **Datta Meghe College of Engineering, Airoli, Navi Mumbai**.

UniSched includes a responsive website, a FastAPI backend, a SQLite database, a Google OR-Tools CP-SAT scheduler, and downloadable PDF and Excel timetables. The website has no JavaScript build step or external CDN dependency.

## Run the project

Requires **64-bit Python 3.11 or 3.12**, with `venv` and `pip`.

### Windows

Extract the ZIP, open the folder containing `run.py`, and double-click **`start_windows.bat`**. It selects an installed Python 3.12 or 3.11, creates or checks `.venv`, installs dependencies, and starts the server. Keep the window open while using UniSched.

Alternatively, run these commands in **Command Prompt** from that folder:

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.lock
.venv\Scripts\python.exe run.py
```

If Python 3.12 is not installed, use `py -3.11 -m venv .venv` for the first command. Check that the second command reports Python 3.11 or 3.12. An existing supported `.venv` can be reused. Windows uses `.venv\Scripts\python.exe`; `.venv/bin/python` is the macOS/Linux path.

### macOS / Linux

From the project folder, with Python 3.11 or 3.12 selected:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python run.py
```

The website is served at `http://127.0.0.1:8000`. The API documentation is at `/docs`, and `/api/health` checks the server and database. Add `--reload` to the `run.py` command while developing. On subsequent launches, you can run only the final `run.py` command.

The first launch initializes `data/unisched.db` and imports the included sample dataset. Later launches reuse existing data. No separate database server, credentials, Node.js, or frontend build is needed. Set `UNISCHED_DB` to use a different SQLite database path.

### Fix an older Windows download

If installation reports `No matching distribution found for numpy==2.5.4`, use the updated `requirements.lock` from this repository. The older file pinned NumPy/Pandas versions that required Python 3.12. The corrected file supports both Python 3.11 and 3.12 and includes Windows dependencies.

You can update only that file from your existing project folder without replacing saved data:

```bat
curl.exe -fL https://raw.githubusercontent.com/omkawate/timetable/main/requirements.lock -o requirements.lock
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.lock
.venv\Scripts\python.exe run.py
```

If the file download fails, use **Code → Download ZIP** on GitHub and copy `requirements.lock` from the new ZIP into your existing project folder. Keep your `data` folder.

## Use the website

1. **Academic setup:** review or add teachers, subjects, rooms/labs, divisions, and teaching assignments. Edit or delete records using the row controls. References are validated: a teacher or room used by an assignment cannot be deleted until that assignment is updated.
2. **Import data:** upload a CSV, examine its validation report, and choose **Replace academic data**. You can first back up the current configuration with **Export data CSV**. Importing replaces the editable configuration and preserves all saved timetable snapshots.
3. **Generate timetable:** name the timetable and choose a 20-, 60-, or 120-second search limit. All years/divisions are solved together so shared teachers and rooms cannot clash.
4. **Timetables:** switch between division and professor views. A professor view shows only that teacher’s sessions, with the year, division, and room; all other teaching cells are blank.
5. **Export:** download the current view as PDF or Excel, all divisions as a PDF/Excel file, or all professors as an Excel workbook. Every timetable includes the college name. Each Excel worksheet and PDF page corresponds to one selected division/professor.
6. Select an older generation to view its immutable snapshot. An alert appears if the editable academic data has changed since that generation.

## Scheduling rules and assumptions

| Requirement | Implemented behavior |
| --- | --- |
| Teaching week | Monday–Friday |
| Teaching periods | 09:00–10:00, 10:00–11:00, 11:00–12:00, 12:00–13:00, 13:45–14:45, 14:45–15:45, 15:45–16:45, 16:45–17:45 |
| Recess | 13:00–13:45, excluded from teaching hours |
| No gaps | Each division’s active day starts at 09:00 and contains consecutive periods, except recess. A division with at least five weekly hours attends all five weekdays. Days can finish early. No filler classes are invented. |
| Teacher hours | Weekly **maximum teaching hours**, counted across every year and division. A one-hour lecture counts as one; a two-hour lab counts as two. |
| Availability | The teacher’s coming/leaving time applies on every weekday. An entire lecture/lab must fit within it. Partial hours do not form a teaching period. |
| Lectures | One hour each; the exact requested weekly count is placed. |
| Labs | Two consecutive hours per lab session; a lab cannot cross recess or the end of the day. Lab count means **sessions**, not hours. |
| Electives | Every elective session has a distinct slot within its semester, including across divisions and including elective labs. Electives in different semesters can overlap if no teacher or room clashes. |
| Rooms | Each division has a home lecture classroom; each lab assignment chooses its lab. A physical room name is unique. Shared rooms are supported but cannot be double-booked. |
| Subject assignments | One teacher per subject per division, used for both lectures and labs. The subject and division must have matching semesters. |
| Years | Semester 3 = Second Year; 5 = Third Year; 7 = Final Year. Divisions such as A/B/C are editable. |
| Professor view | Gaps are intentionally blank; the no-gap rule applies to **divisions**, not professors. |

This version treats each elective as a subject attended by its whole division. Student-specific elective baskets, split lab batches, day-specific teacher availability, room seat/equipment capacities, holidays, and separate lecture/lab instructors are future extensions. The sample is an illustrative Computer Engineering dataset; it is not an official DMCE syllabus or faculty roster.

## How generation and explanations work

The scheduler creates Boolean choices for each eligible lecture/lab start time. It enforces exact weekly counts, non-overlapping teachers/divisions/rooms, teacher availability, separate elective periods, and continuous division days. It minimizes the largest daily teaching load across divisions to balance the week.

Before searching, workload checks catch obvious impossibilities such as an overloaded teacher, insufficient full teaching periods, an unavailable two-hour lab window, or an overbooked room. The report gives the concrete shortage and suggests a change.

For a conflict between otherwise valid requirements, CP-SAT proves infeasibility and an assumption-based diagnostic search identifies a sufficient conflicting set when it can do so within the remaining time. The set is not guaranteed minimal. The report lists the involved assignments/rules and suggested changes. Suggestions are **not automatically applied**; you decide which academic requirements to change. If the solver finds no complete timetable before the deadline, the UI reports **Search limit**, not “impossible.”

Successful generations report which constraints were satisfied, the placement totals, the elapsed time, and whether the best daily balance was proven. All required sessions remain mandatory even when balancing stops before reaching the best possible balance.

For the supplied dataset, the generator schedules **9 divisions, 18 teachers, 171 sessions, and 198 teaching hours**. Each division has 22 teaching hours/week, and the optimal maximum daily load is 5 hours.

## CSV format

The complete file is [`sample_data/unisched_semesters_3_5_7.csv`](sample_data/unisched_semesters_3_5_7.csv). It contains all three semesters and divisions A, B, C in **one file**, with 54 teaching-assignment rows.

Use these exact headers in this order:

```csv
semester,division,teacher_name,teacher_hours_per_week,teacher_arrival,teacher_departure,subject_name,subject_code,elective,classroom,lab_room,lectures_per_week,labs_per_week
```

Example:

```csv
3,A,Prof. Rahul Patil,18,09:00,17:45,Data Structures,CSC302,false,201,Lab 3-2,3,1
```

Save as UTF-8 CSV, up to 1 MB. Use 24-hour times and whole-number counts. Elective accepts `true`/`false`, `yes`/`no`, or `1`/`0`. Leave `lab_room` blank when no lab is needed. Repeated teacher names, subject codes, room names, and semester/division pairs must have consistent details. Conflicting duplicates, duplicate division/subject assignments, malformed rows, invalid references, and unsupported semesters are rejected before saving. Names are matched case-insensitively; use one consistent spelling.

Configuration limits are 100 teachers, 120 subjects, 100 rooms, 30 divisions, and 240 assignments. Large constrained datasets may need longer search time. The CSV exporter neutralizes spreadsheet formula prefixes in text fields; such unusually prefixed names receive a leading apostrophe on CSV export.

## Project layout

```text
app/
  main.py         HTTP API, uploads, downloads, and static website
  domain.py       Typed academic data, validation, and CSV conversion
  scheduler.py    CP-SAT model, workload checks, and conflict explanations
  storage.py      SQLite configuration revisions and generation snapshots
  exports.py      College-branded PDF and Excel timetables
static/
  index.html      Website shell
  app.js          Dashboard, forms, import, schedule views, and exports
  style.css       Responsive desktop/mobile styles
sample_data/
  unisched_semesters_3_5_7.csv
tests/
  test_scheduler.py  Independent constraint verification and failure cases
  test_api.py        Persistence, imports, exports, and API behavior
  browser_smoke.py   Real Chromium desktop/mobile user workflows
data/               SQLite database, created automatically and gitignored
run.py
start_windows.bat    Windows setup and startup helper
requirements.txt    Direct runtime dependencies
requirements.lock   Tested runtime dependencies with exact versions
```

SQLite stores the validated academic configuration as a versioned JSON document in the `configuration` table, and immutable configuration/result snapshots in `generations`. Writes are transactional. Revision checks prevent one browser window silently overwriting changes from another. This keeps CSV replacement atomic and preserves historical timetables. The API uses one server worker and serializes timetable generation; it is designed for a single-coordinator installation.

## Tests

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

The tests independently reconstruct every occupied teacher, room, division, and elective period, verify exact lecture/lab counts and continuous days, test impossible configurations and time limits, parse exported PDFs/Excel workbooks, and check immutable snapshots and invalid imports. Tests use temporary databases.

For real browser testing, install Chromium or a Playwright browser:

```bash
.venv/bin/python -m playwright install chromium
.venv/bin/python tests/browser_smoke.py
```

The browser script automatically uses a system `chromium` if present; alternatively set `CHROMIUM_PATH` to your executable. It starts its own temporary server/database, tests CRUD, CSV import, generation, professor filtering, downloads, conflict explanations, and mobile navigation, and saves screenshots under ignored `artifacts/`. It does not alter your normal academic data.

## Deployment and useful next additions

This is a functional single-coordinator application. It defaults to loopback access. Before exposing it publicly, add authenticated administrator/faculty accounts, HTTPS, access control, and backups. SQLite data can be backed up safely with SQLite’s online backup API; avoid copying only the `.db` file while the WAL-mode server is writing. There is no deployment or public hosting included.

Suggested additions, in priority order:

1. **Login and approval:** coordinator editing, faculty read-only views, and head-of-department approval before publication.
2. **Academic calendar:** configurable weekdays/period lengths, holidays, and teacher leave or per-day availability.
3. **Lab batches and elective baskets:** schedule student groups independently and allow separate lab instructors.
4. **Manual pinning:** lock approved sessions, then regenerate the rest while checking collisions.
5. **Room capacity/equipment:** match class size, computers, projectors, and specialist laboratories.
6. **Substitutions and notifications:** find available replacement faculty, compare timetable versions, and optionally notify affected users.
7. **Institution-wide planning:** departments, even semesters, calendar feeds, attendance integration, and role-aware exports.

## Reusable cloud workflow

Use the existing checkout at `/workspace/timetable`; cloud tasks already run in an isolated environment. Do not create a Git worktree unless specifically requested. Dependencies and SQLite files can persist in a filesystem snapshot, but server processes must be restarted. Install from `requirements.lock`, run `run.py`, check `/api/health`, and use `pytest` for validation. No secrets or remote services are required at runtime.
