# UniSched

**Campus, in sync.** A working university timetable planner for **Datta Meghe College of Engineering, Airoli, Navi Mumbai**.

UniSched includes a responsive website, a FastAPI backend, a SQLite database, a Google OR-Tools CP-SAT scheduler, and downloadable PDF and Excel timetables. The website has no JavaScript build step or external CDN dependency. Local timetable advice works offline; an optional OpenAI explanation mode can use a server-side API key.

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

## Update an existing installation

1. Stop the old server with **Ctrl+C** and keep a backup of its `data` folder.
2. Extract the updated ZIP into a **new folder**. Copy the old `data` folder into it while both servers are stopped. This preserves academic data and saved timetable history.
3. Run `start_windows.bat` from the new folder. Do not copy `.venv` between folders; the launcher creates it.
4. Open http://127.0.0.1:8000 and press **Ctrl+F5** to load the updated website.
5. Existing data is preserved. To try the fuller IT curriculum, open **Import data → Preview IT reference data → Replace academic data**. Download the full JSON backup before replacing your editable data. Old timetable snapshots remain available.

A fresh database starts with the new IT presentation dataset. Older databases receive compatible defaults in memory: an existing-data department, original calendar, automatic capacity defaults, and the original weekly limits. Reading the database does not rewrite historical snapshots.

## Use the website

- **Department selector:** focus management screens and generation on IT or another department. Add departments through **Departments**.
- **Subjects & courses:** choose the academic year (First, Second, Third, Final), odd/even semester, department, course type, default contact hours, and elective set. Default contact hours prefill new assignments; assignment session counts are the actual scheduling requirements.
- **Academic setup:** manage assignments, teachers, subjects, divisions, rooms, departments, lab batches, and elective sets. Lab batches belong to a division; their total strength cannot exceed the division's strength. Linked records must be reassigned before deletion.
- **Faculty workload:** edit daily period limits, weekly hour limits, arrival/departure times, email, short code, and lab/project eligibility. A teacher's load includes assignments across all departments.
- **Generate by division:** choose the department and semester, then **Generate Division A**, **B**, **C**, or **Generate all selected divisions**. The buttons reflect the actual divisions you created.
- **Timetables:** select a saved version, academic year, division, or professor. Professor grids show only that person's classes; other teaching cells remain blank. Multi-period labs/projects are labelled as starting or continuing. Parallel practical batches are labelled separately.
- **Exports:** current view and all divisions as PDF/Excel; all professors as Excel. Every exported timetable displays the college name and uses the saved version's calendar.
- **College timings:** configure hours, working days, period length, breaks, blocked college activities, and lecture/lab/project durations. Preview periods before saving.
- **Analytics & conflicts:** inspect actual conflicts, student gaps, daily spans, teaching loads, and room utilization from a saved generation. Failed runs display problems and suggested changes.
- **Version history / Performance:** reopen snapshots and inspect measured runtimes, success rate, recent API latency, uptime, and peak process memory.

### Generating one division safely

By default, generation preserves sessions outside your selected divisions from the latest successful plan with the **same data revision**. For example, generate A, then B: A stays fixed while B is scheduled around its faculty, room, and elective reservations. The result lists scheduled and remaining divisions.

Preserving earlier choices can make a later division impossible even when a completely new joint plan would work. In that case, select all affected divisions and generate them together. Uncheck **Preserve other divisions** to start an independent plan; it does not claim coordination with other saved versions. Changing academic data starts a new revision, so incompatible historical schedules are never silently used as a base.

## Manual timetable editing and approval

Every successful generation starts as an unlocked **Draft**. In Timetables:

- **Edit timetable manually** opens the current division/professor's sessions. **Edit entire plan** opens all scheduled divisions, for coordinated moves across divisions.
- Change day, starting period, or eligible room. To swap lectures, exchange placements in both rows before saving. A two-period laboratory moves as one whole session.
- **Validate & save new Draft** checks every affected and unaffected session together. Faculty/room/student collisions, daily and weekly caps, elective separation, lecture spread, missing teaching days, student gaps, room eligibility, and breaks remain enforced. An invalid edit stays in the form with an explanation and does not create a version.
- A valid edit creates a **new Draft version**, preserving original timetable content. Manual versions are independently audited; they do not claim solver-optimal balancing or count as solver performance runs.
- **Approve timetable** audits the plan again and marks that version Approved. Approved timetables are read-only until **Mark Draft** is chosen.
- **Lock timetable** prevents editing and status changes for that saved version. **Unlock timetable** restores its previous draft/approved status. A lock is for the whole saved version; it is not a per-lecture pin. Generating another plan creates another draft and never modifies the locked snapshot.
- Status appears in Version history and PDF/Excel exports. Stale browser windows cannot overwrite newer workflow choices.

Approval is a local coordinator workflow marker, not authenticated HOD authorization. Historical snapshots have Draft/unlocked defaults until their status is explicitly changed. Partial plans can be approved; the timetable scope still clearly lists remaining divisions.

## Practical batches

The updated IT demo supplies **three batches for every division**: A1/A2/A3, B1/B2/B3, and C1/C2/C3 in each of semesters 3, 5, and 7. Each practical assignment specifies its batch, teacher, and lab. Parallel lab sessions appear together with their batch labels. Full-division batch PDFs use A3 landscape; individual-batch PDFs use A4. Use **Practical batch** in the timetable toolbar to view or export one batch alongside its whole-division lectures.

For a new division, Academic setup → Divisions offers **Create A1 / A2 / A3** (or the division's matching labels), splitting student strength evenly. Add separate lab assignments with a teacher and eligible room for each batch. **Add batch** supports additional custom batches; the total batch headcount cannot exceed the division's strength. Merely creating batch names does not invent teaching requirements.

## Presentation dataset

The folder `sample_data` includes the same complete IT dataset in three formats:

- [`it_presentation.csv`](sample_data/it_presentation.csv): one editable file for semesters 3, 5, and 7, divisions A/B/C.
- [`it_presentation.xlsx`](sample_data/it_presentation.xlsx): separate worksheets for academic entities and settings.
- [`it_presentation.json`](sample_data/it_presentation.json): full backup with stable identifiers.

It contains **27 illustrative subjects, 33 teachers, 9 divisions, 27 practical batches, and 108 assignments**. The resources are **7 shared classrooms and 6 shared laboratories**, fewer classrooms than divisions. Each division has three 20-student batches: A1/A2/A3, B1/B2/B3, or C1/C2/C3. **Each batch has exactly one two-hour lab per week. All three labs run simultaneously in one common weekly block**, with distinct assigned teachers and laboratories. For example, Semester 3 Division A runs Data Structures for A1, DBMS for A2, and OOP for A3 in that block. Lectures and mini projects belong to the whole division.

Each student attends **26 lecture hours + one 2-hour lab + one 4-hour mini project = 32 hours/week**. Projects are explicit optional assignments: change their hours/sessions or remove the assignment to omit them. Faculty limits are 20 hours/week, with five daily periods for theory faculty and six for practical/project faculty. Classrooms have 70 seats; four laboratories have 20 seats and two have 60 seats so they can also host whole-division projects. Each division has 60 students. The solver shares these rooms across all nine divisions without relaxing capacity or collision rules.

The calendar starts at **09:00**, with recess **13:00–13:45**, and permits teaching until **17:45**. The verified complete solution has **270 sessions / 324 faculty contact hours**, no internal student gaps, no audited conflicts, and a maximum of seven teaching periods per student day. Most days finish at 15:45–16:45; a shorter day is possible. The solver determines exact placements. Room-period utilization is **62.3%** across the thirteen rooms (324 / 520). The all-batches view totals 36 faculty contact hours per division; an individual batch's student timetable totals 32 hours.

This is presentation data, **not an official DMCE curriculum or faculty directory**. No filler sessions are invented. The original 22-hour/week dataset remains at [`unisched_semesters_3_5_7.csv`](sample_data/unisched_semesters_3_5_7.csv), and its 171-session / 198-hour generation remains regression-tested.

See [the presentation walkthrough](docs/PRESENTATION.md) and [the screenshot feature comparison](docs/FEATURE_COMPARISON.md).

## Mini projects and simultaneous batch labs

- Open **Academic setup → Assignments → Add mini project**. Choose a division, subject name/code, supervisor, sessions per week, hours per session, and a suitable lab or Auto. An existing project subject code can be reused for another division in its semester. The selected laboratory must seat the whole division.
- Use **Edit assignment** to change project hours/sessions or the supervisor. Remove a project-only assignment to omit the project. Hours must fit whole teaching periods and one unbroken window; a four-hour project fits 09:00–13:00 or 13:45–17:45, never across recess. Leaving hours blank uses the default project duration in College timings.
- Create batches under **Lab batches**, then add one lab assignment per batch. Each batch needs a different teacher and an available lab at the common time. Batches attend labs only; all students attend division-wide lectures and mini projects.
- When manually moving a practical block, move **all its batch rows** to the same new day/start before saving. Use **Edit entire plan** from a professor view to access the other batch rows. The backend checks synchronization alongside the existing no-gap, teacher, room, and count rules.
- Existing installations keep their academic data and original scheduling policy. To use the new example, back up data and import **Preview IT reference data → Replace academic data**. For your own older dataset, update its assignments, then enable **One simultaneous weekly lab block for all batches** in College timings. Existing saved timetables and exports retain their original rules; regeneration creates a new Draft.

## Classroom continuity and clearer timetables

The generation dialog offers **Flexible**, **Prefer 2 consecutive lecture periods in one room**, or **Prefer 3**. College timings sets the default; the IT demo defaults to 2. Each saved version retains its chosen setting. Changing it selects a new compatible base or starts a fresh plan rather than mixing different settings.

The scheduler first solves session times and mandatory constraints, then optimizes lecture rooms while keeping every day/time/teacher fixed. It minimizes early classroom changes, then total changes. Labs, mini projects, recess, and free periods reset a lecture run. This is a preference: fixed rooms, preserved divisions, capacity and eligibility always apply. The result reports actual changes, early changes, and whether the best room allocation was proven for those fixed session times. The verified nine-division example achieved zero consecutive-lecture classroom changes.

In **All batches**, each practical now has a separate, naturally sized card with a bold batch label, teacher, subject, and room. Rows grow to fit all cards. PDF uses larger type and separated coloured cards; Excel uses wrapped text, taller rows, and repeating print headings. The standard all-batches division PDF fits one A3 landscape page; unusually dense or custom calendars can continue onto another page with repeated column headings. Single-batch/professor PDF views remain available.

## Timetable assistant: local checks and optional OpenAI

Open **Timetable assistant**, select one saved timetable or **All saved timetables (latest 100)**, and enter a question. For a replacement-room check, select the particular session. Local mode checks the full saved plan: room type, seats, department/year eligibility, fixed-room restrictions, overlapping bookings, and a complete audit after each proposed replacement. It explains why rooms work or are ruled out, and shows any impact on classroom continuity. All saved versions are treated separately, not as simultaneous bookings.

Advice never modifies schedules. Apply a chosen room through **Edit timetable manually** on an unlocked Draft; validation runs again. Local mode supports summaries, conflicts, teaching loads, and room alternatives. It does not pretend to be an online language model.

To enable optional conversational explanations, set an OpenAI API key **on the computer running UniSched**, then start the server. In Windows Command Prompt, from the project folder:

```bat
set "UNISCHED_OPENAI_API_KEY=your-api-key"
set "UNISCHED_OPENAI_MODEL=gpt-4.1-mini"
start_windows.bat
```

On macOS/Linux:

```bash
export UNISCHED_OPENAI_API_KEY='your-api-key'
export UNISCHED_OPENAI_MODEL='gpt-4.1-mini'
.venv/bin/python run.py
```

Choose **OpenAI explanation + local checks** in the assistant. The model name is configurable; use one enabled for your OpenAI API account. API use may incur charges. The key stays on the server and is never stored in SQLite or returned to the browser. This mode sends the question and selected plans' audited facts and, for a single selected plan, its session list, including faculty and room names, to the OpenAI Responses API with `store: false`. It provides wording and explanations; verified local checks remain expandable underneath. If the key/service is unavailable, the assistant displays the local answer with a clear explanation. Large selections may need one timetable selected for online mode. The adapter is covered by mocked API tests; no live paid request is required to run the project or its tests.

## Scheduling rules

The solver uses **Google OR-Tools CP-SAT**. Mandatory session choices and resource occupancy constraints enforce:

| Rule | Behavior |
| --- | --- |
| Student continuity | Every active student/batch day begins at the first available period and has no internal holes, except configured breaks or blocked periods. Loads covering at least the number of working days attend every available working day. Days can finish early. |
| Teacher availability | Coming/leaving time, daily teaching-period cap, weekly teaching-hour cap, and lab/project eligibility. |
| Resource collisions | A teacher or room cannot be double-booked across departments or divisions in the same plan. |
| Room selection | Fixed classroom/lab or automatic allocation among rooms matching capacity, department, and academic year. Empty room year eligibility means all years; no department means shared college room. |
| Sessions | Exact lecture, lab, and project counts. Multi-period sessions stay consecutive in real time and never cross breaks, blocks, or the end of the day. |
| Batches | With the new default policy, batches cover the whole division and each has exactly one weekly lab. All batches share the same day, starting period, and duration, using distinct teachers and rooms. Batch lectures/projects are rejected. Whole-division lectures/projects occupy every batch. Historical versions retain their original policy. |
| Electives | Separate slots across the same department and semester, including its divisions. Elective sets organize related courses; they do **not** make alternatives run simultaneously. |
| Lecture distribution | Enabled by default: each subject with 3–4 weekly lectures uses different days. The daily limit is ceil(weekly lectures / working days). A fresh solver seed varies placements while keeping all constraints; this is not an unconstrained random shuffle. Existing snapshots keep their original policy. |
| Balance | Minimize the largest student daily teaching load; report whether optimality was proven. Optional second-stage room optimization preserves all session times and hard constraints. No requirements are silently relaxed. |

Preflight checks explain excess workload, insufficient room capacity/eligibility, missing assignments, unavailable lab windows, and other obvious problems. CP-SAT checks the combination. When proven infeasible, a diagnostic search identifies a sufficient conflicting set where possible; it need not be minimal. Suggestions are **not applied automatically**. A search timeout is reported as **Search limit**, never proof of impossibility.

Analytics independently reconstructs occupancy, exact session counts, session duration, faculty caps, eligible rooms, and student continuity. Health is 100 minus five per audited violation (minimum zero). Student quality is teaching periods divided by teaching periods plus internal gaps. Room utilization uses all rooms in the saved configuration, so partial-generation utilization will be lower. Batch session hours are contact-session hours summed over batches, not the weekly hours of one individual student.

## Import and backup formats

Imports accept UTF-8 CSV, `.xlsx`, or JSON up to 1 MB. They preview the configuration and basic issues before an explicit replacement. JSON and Excel preserve unassigned records and identifiers; use them for full backups. Excel imports require the named worksheets from the supplied template and literal cell values rather than formulas.

The extended CSV uses the original thirteen assignment columns plus department, strength, faculty daily limit/contact details/eligibility, project count and hours per session, batch, elective set, course type, and default hours. Its first row includes room pools, department metadata, and calendar settings as JSON. Those cells preserve shared-room eligibility; retain them when editing the file in Excel. **CSV exports represent assigned records** and recreate assignment/student/subject identifiers on import; use full JSON/Excel to preserve every record.

The original 13-column CSV is still supported:

```csv
semester,division,teacher_name,teacher_hours_per_week,teacher_arrival,teacher_departure,subject_name,subject_code,elective,classroom,lab_room,lectures_per_week,labs_per_week
3,A,Prof. Rahul Patil,18,09:00,17:45,Data Structures,CSC302,false,201,Lab 3-2,3,1
```

Use 24-hour times and whole-number counts. Repeat details consistently. CSV text starting with spreadsheet formula prefixes receives a leading apostrophe on export. Limits: 100 teachers, 120 subjects, 100 rooms, 30 divisions, 240 assignments, 30 departments, 120 batches, 80 elective sets. Larger or tighter plans may need the 60/120-second search options.

## Project layout

```text
app/
  main.py         FastAPI routes, generation scope, diagnostics metrics
  domain.py       Academic records and reference validation
  calendar.py     Validated calendar and period calculations
  scheduler.py    CP-SAT constraints, balancing, infeasibility explanations
  resources.py    Student units, session requirements, room eligibility
  analytics.py    Independent saved-timetable audit and measured statistics
  exchange.py     CSV, Excel, JSON import and backup
  demo.py         Reproducible IT presentation data
  storage.py      SQLite revisions, immutable snapshots, workflow states
  editing.py      Manual placement validation and draft version creation
  exports.py      College-branded PDF and Excel timetables
static/
  index.html      Original website shell with additional navigation
  app.js          Shared UI, API helpers, dialogs, original workspace
  workspace.js    Department, scoped generation, management and analysis screens
  editing.js      Manual editor, Draft / Approved / Lock controls
  style.css       Responsive purple design
sample_data/      Original CSV plus IT presentation CSV/Excel/JSON
tests/            API, scheduler, upgrade, export and browser regressions
docs/             Feature comparison and demonstration walkthrough
data/             SQLite files created automatically, excluded from Git/ZIP
run.py            Server entrypoint
start_windows.bat Windows dependency setup and startup
requirements.lock Tested exact runtime dependencies for Python 3.11/3.12
```

SQLite stores versioned configuration JSON and immutable generation snapshots. Writes are transactional; revision checks prevent stale windows from silently overwriting changes. Generation uses a single server worker with a lock. The history/performance lists cover the latest 100 saved runs; older records remain stored and accessible by ID. Runtime API latency covers the latest 500 completed requests, including long generation requests.

## Verification

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m playwright install chromium
.venv/bin/python tests/browser_smoke.py
```

On Windows, replace `.venv/bin/python` with `.venv\Scripts\python.exe`. Browser tests automatically use a system `chromium` if available, or `CHROMIUM_PATH`. Tests create disposable SQLite databases and leave the user's data untouched. Screenshots and test exports go in ignored `artifacts/`.

## Further additions

Useful next steps are coordinator/faculty login with role-based approval, individual teacher leave dates, specialist room equipment, manually pinned individual sessions, substitutions, and calendar subscriptions. The current version is intended for a local coordinator. OpenAI explanations are optional; automatic email messaging is not included. Authentication and HTTPS would be needed before public deployment.

## Reusable cloud workflow

Use `/workspace/timetable`. Install `requirements-dev.txt`, run `run.py`, check `/api/health`, and run `pytest`. No frontend build, external database service, or secrets are required. Server processes must be restarted after restoring an environment snapshot. Keep real SQLite data out of source archives.
