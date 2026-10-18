# Included academic data

## IT presentation dataset (new default)

`it_presentation.csv`, `.xlsx`, and `.json` contain the same complete illustrative curriculum for Second, Third, and Final Year (semesters 3, 5, and 7), each with divisions A/B/C.

- 33 teachers (24 theory and nine practical), available 09:00–17:45, with 20-hour weekly limits and daily caps of five/six periods.
- 27 subjects, nine per semester (including one optional mini project), including two separately scheduled electives per semester.
- Seven shared 70-seat classrooms and six shared laboratories (four with 20 seats and two with 60 seats for whole-division projects) for nine 60-student divisions. Classrooms use Auto allocation; each batch has an explicitly assigned lab.
- 27 batches: A1/A2/A3, B1/B2/B3, C1/C2/C3 for each semester. 108 assignments include 26 lectures per division, one two-hour lab per batch, and one four-hour division-wide mini project: 32 hours per student/week. The three batch labs always run simultaneously in one weekly block, each with its own teacher and room. Batches attend labs only.
- 270 sessions / 324 faculty contact hours across all divisions. Most days finish at 15:45–16:45, with a possible shorter day; the exact grid is computed by the solver.
- Each subject’s three/four weekly lectures are spread across distinct days.
- Default classroom preference: two consecutive lecture periods in the same room; change to three or Flexible in the generation dialog.
- Recess 13:00–13:45; five working days; the college day can extend to 17:45.

Open **Import data → Preview IT reference data → Replace academic data**, or choose one of these files directly. A new empty database seeds this dataset automatically. Existing databases retain their data until an explicit import.

Use Excel/JSON for full backups. The extended CSV has one row per assignment; its first row carries room pools, department metadata, and calendar JSON. Keep those cells when editing. The `project_hours_per_session` column controls project duration; `project_sessions_per_week` controls frequency. Blank project hours use the saved college default. The previous extended CSV without the hours column remains importable. CSV imports rebuild assignment/subject/division IDs and do not preserve unassigned records.

## Original lighter dataset

`unisched_semesters_3_5_7.csv` remains supported:

- 18 teachers and 18 subjects; weekly teacher limit 18 hours.
- Nine dedicated classrooms and six laboratories.
- 54 assignments, 22 hours/week per division, 171 sessions / 198 teaching hours overall.

Find it through **Import data → Original sample CSV**.

All names and curricula are illustrative, not an official DMCE faculty list or prescribed syllabus. Repeat teacher details consistently; loads apply across divisions and departments. No filler subjects are inserted by the solver.
