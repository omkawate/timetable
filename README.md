# UniSched

University timetable planning for **Datta Meghe College of Engineering, Airoli, Navi Mumbai**. Website, FastAPI, SQLite, and OR-Tools CP-SAT. No frontend build is required.

## Run on Windows

Extract into a **new folder** and double-click `start_windows.bat`. Install 64-bit Python 3.11 or 3.12 first. Keep the terminal open, then visit `http://127.0.0.1:8000`. Press Ctrl+F5 after upgrading.

Manual commands from the folder containing `run.py`:

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.lock
.venv\Scripts\python.exe run.py
```

On Linux/macOS, use `python3.12 -m venv .venv`, then `.venv/bin/python -m pip install -r requirements.lock` and `.venv/bin/python run.py`. Python 3.11 also works.

## This update

- **Generate by division → Generate:** choose a 9:00 or 10:00 a.m. start. The saved timetable and exports use that choice. It does not rewrite the imported source calendar.
- **Classroom continuity:** default minimum two consecutive lecture periods before changing rooms; three is optional. Enforced separately in each uninterrupted morning/afternoon lecture block. Recess, tutorials, labs, projects, and free periods end a block. A short block may end without inventing extra lectures. If reservations make the rule impossible, generation reports it instead of relaxing it.
- **Tutorials:** dedicated sidebar section with subject, division, batch, teacher, sessions, duration, and classroom. The nine supplied tutorial assignments use **room 710**.
- **Practicals remain two hours**, Monday–Friday. Existing lecture counts are preserved exactly; new lecture assignments default to three per week.
- Manual editing, Draft/Approved/Lock, deletion of generated versions, AI chat, separate batch cards, professor/classroom/lab views, and PDF/Excel export remain available.

## Supplied official data

The only application seed file is [`sample_data/it_timetable_import_group_consistent.csv`](sample_data/it_timetable_import_group_consistent.csv). Its bytes are unchanged from the uploaded file. A fresh database imports it automatically. Previous illustrative seed files are removed.

It contains 191 assignments, 34 subjects, 24 named faculty, eight divisions, 24 batches, seven classrooms and six laboratories. Semesters 3 and 5 have A/B/C; semester 7 has A/B. Teacher–subject mappings, names, session counts and room capacities are retained. The source's `MECH` faculty department code is represented as a department named `MECH`; no faculty is invented. Subjects appearing as both theory and practical are represented as mixed courses. Tutorial rows are recognized as tutorials, retaining their batch and room 710.

### Approved scheduling arrangement

The default generation option allows **Entrepreneurship Development (2993511), Environmental Science (2993512), India Knowledge System (2345511), and Full Stack Java Mini-Project (2343611)** practicals to use the existing classrooms. Batches combine only within the same division, subject, professor and frequency, and only if the classroom fits their combined strength. Each batch keeps its two-hour session; professor names, subject mappings, lecture counts and source data remain unchanged. Technical practicals outside these four codes still use laboratories. This is an explicitly disclosed scheduling assumption authorized for this update, not a claim that every classroom has laboratory equipment.

The reference images show IKS classroom sessions, lecture room continuity, batch rotations, and independent Major Project blocks. They are structural references; the CSV remains the source of faculty assignments and counts. No teacher-guardian or remedial sessions were invented.

**Major Project I** is reserved student time without a teacher or room booking, as requested. Its supplied two sessions of four hours remain on the timetable. There are no missing-project-supervisor errors for these independent blocks.

If you turn off the approved classroom/combined-batch option, the original exclusive-lab interpretation requires 246 lab-room hours against 240 at 9:00 or 210 at 10:00, and some faculty loads exceed their daily caps. The software explains this rather than shortening practicals or changing faculty limits.

A verified placement hint for the exact supplied dataset avoids repeating an expensive search. It is a starting solution, **not extra academic data**. Every generation independently rechecks counts, capacities, faculty limits, combined sessions, gaps and classroom continuity. Academic edits invalidate its fingerprint and trigger a new search. Saved placements can also be reused after validation. All divisions are checked together for shared resources.

A start-time choice only selects the calendar for the new timetable. Teacher availability remains enforced; if it prevents that start, the result explains the conflict. Source CSV downloads are exact; current-data CSV/Excel/JSON exports include normalized tutorial fields. JSON and Excel preserve all identifiers and independent project records.

## Existing databases

For the requested replacement data, use a freshly extracted folder **without copying the old `data` folder**. Keep your original project as a backup. Existing databases are never silently overwritten on startup. If you choose to retain an old database, use **Import data → Preview supplied college data → Replace academic data** after downloading a backup. Historical timetable snapshots remain unchanged and can be deleted separately.

## AI chat

The floating purple **AI chat** button is on the starting page and the sidebar. Local checks work without a key. Select a timetable/session to ask about eligible replacement classrooms and conflicts. Optional OpenAI explanations require `UNISCHED_OPENAI_API_KEY` in the server environment; never put keys in website code. Local checks remain authoritative and suggested changes are not automatically applied.

## Development checks

The source repository includes regression fixtures under `tests`; they are never imported by the application and are excluded from the downloadable ZIP. In a Git checkout, install `requirements-dev.txt`, run `python -m pytest -q`, and run `python tests/browser_official.py` with Chromium installed. Tests use temporary databases.
