# Included academic data

## IT presentation dataset (new default)

`it_presentation.csv`, `.xlsx`, and `.json` contain the same complete illustrative curriculum for Second, Third, and Final Year (semesters 3, 5, and 7), each with divisions A/B/C.

- 24 teachers, available 09:00–17:45, with 20-hour weekly and five-period daily limits.
- 24 subjects, eight per semester, including two separately scheduled electives per semester.
- Only seven shared classrooms and two shared laboratories for nine divisions; 70 seats per room, 60 students per division. Auto allocation avoids dedicated classroom requirements.
- 72 assignments: 26 one-hour lectures plus three two-hour practicals per division, totaling 32 teaching hours/week.
- 261 sessions / 288 teaching hours across all divisions. Most days finish at 15:45–16:45, with a possible shorter day; the exact grid is computed by the solver.
- Recess 13:00–13:45; five working days; the college day can extend to 17:45.

Open **Import data → Preview IT reference data → Replace academic data**, or choose one of these files directly. A new empty database seeds this dataset automatically. Existing databases retain their data until an explicit import.

Use Excel/JSON for full backups. The extended CSV has one row per assignment; its first row carries room pools, department metadata, and calendar JSON. Keep those cells when editing. CSV imports rebuild assignment/subject/division IDs and do not preserve unassigned records.

## Original lighter dataset

`unisched_semesters_3_5_7.csv` remains supported:

- 18 teachers and 18 subjects; weekly teacher limit 18 hours.
- Nine dedicated classrooms and six laboratories.
- 54 assignments, 22 hours/week per division, 171 sessions / 198 teaching hours overall.

Find it through **Import data → Original sample CSV**.

All names and curricula are illustrative, not an official DMCE faculty list or prescribed syllabus. Repeat teacher details consistently; loads apply across divisions and departments. No filler subjects are inserted by the solver.
