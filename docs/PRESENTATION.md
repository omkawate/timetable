# UniSched presentation walkthrough

1. Start with `start_windows.bat`, then open http://127.0.0.1:8000.
2. For an existing database, export **Import data → Back up current data**, then **Preview IT reference data → Replace academic data**. A new database already contains this dataset.
3. Select **IT · Information Technology** in the header. In Academic setup, show 27 subjects, 33 teachers, nine divisions, 27 batches, and seven classrooms plus six laboratories. Divisions use Auto classroom allocation; classrooms have 70 seats, four labs have 20 seats, and two labs have 60 seats to accommodate whole-division projects. Each division has 60 students.
4. Open Generate by division. Leave All years / semesters selected, choose Generate all selected divisions, and use a 60-second limit. It must place 270 sessions / 324 faculty contact hours without collisions or student gaps. Runtime depends on the computer; use 120 seconds if the search reaches its limit.
5. Show a division timetable: 09:00 start, 13:00–13:45 recess, 32 teaching hours per student/week, mostly 15:45–16:45 finishes. Each subject’s three/four weekly lectures must appear on different days. Select a practical batch to see its 32-hour schedule; the all-batches view includes parallel sessions and therefore totals 36 contact hours per division. A shorter day is legitimate. Show the three distinct batch cards in All batches, then the solved-constraints report below the grid. The generation dialog offers 2/3-period classroom continuity; the demo defaults to 2 and reports actual room changes.
6. Open Analytics & conflicts: inspect actual student gaps, teacher caps, and room occupancy. The complete reference plan uses 62.3% of the available room-period capacity. Partial plans naturally have lower utilization.
7. Switch to By professor. Only that faculty member's lectures/labs appear. Export PDF and Excel; both include the college name.
8. Demonstrate separate generation by selecting Semester 3 and generating A, then B. If you already have a full plan, other divisions remain locked; to demonstrate starting from A only, uncheck Preserve other divisions for the first run. B's generation then preserves A automatically. The banner shows exactly which divisions remain unscheduled.
9. Add a department, then a subject with Second/Third/Final Year selection. Add a division and teaching assignments before generating that new department. A new subject alone does not create teaching assignments.
10. Demonstrate a real failure on a copy of the reference data: set one assigned teacher's weekly limit to 1 hour, then generate. UniSched explains the excess assigned hours and proposes reassigning/reducing requirements or changing the limit. Restore the limit to 20 and regenerate. No restriction is silently ignored.

## Manual edits and workflow

Open Edit entire plan. Exchange days/starting periods in two lecture rows, then Validate & save new Draft. If other divisions clash, the form explains the conflicts and leaves the old version intact. Whole-day exchanges across the complete plan are a useful demonstration when all faculty have the same daily availability. Show the earlier version in history, approve the new one, then lock it. The editing button becomes unavailable. Unlock it and Mark Draft to edit again.

## Lab-batch example

A 60-student division contains A1/A2/A3 with 20 students each. Assign lectures and mini projects to the whole division. Create **one lab assignment per batch, with one session per week** and distinct teachers. All three labs occupy the same two-hour weekly block in different laboratories. The Semester 3 example assigns Data Structures to A1, DBMS to A2, and OOP to A3. Batch strengths must cover the complete division. If the teachers cannot attend together or rooms are insufficient, generation explains the problem rather than separating the labs or leaving student gaps.

In manual editing, change the day/start in all three practical rows together. Moving one batch alone is rejected; the earlier version stays intact.

## Optional mini projects

Open **Academic setup → Assignments → Add mini project**, select the division and supervisor, enter a subject code, weekly session count, and hours per session. Choose Auto or a laboratory that seats the whole division. The reference data explicitly requests one four-hour session per division, but this is editable and removable. Project duration is independent for each assignment; it must fit complete periods and cannot cross the 13:00–13:45 recess. A five-hour unbroken session cannot fit the default calendar and produces a clear unavailable-window report. Show the project in the division, batch, and supervisor views and PDF/Excel exports.

## Backup and migration

Stop the server before copying a complete `data` folder. To update, keep the old installation as a backup, extract the new ZIP to a new folder, copy `data`, then run the new Windows launcher. Do not transfer `.venv`. Existing academic data retains its original batch policy; import the updated reference dataset, or update assignments and enable the simultaneous weekly lab block in College timings. Historical snapshots keep their original rules. For editable academic data only, use JSON/Excel export and import. Historical timetables remain in SQLite and are not included in academic-data exports.

## Classroom continuity and assistant demonstration

Select a 2- or 3-period classroom preference in Generate timetable. Show that consecutive lectures retain their classroom where feasible, while laboratories have their own rooms. The banner reports actual changes and unmet preferences. Room optimization never shifts session times, removes student-gap constraints, or moves preserved divisions.

Open Timetable assistant, select the generated plan and a lecture, and ask “Is there a replacement classroom for this session?” Show the eligible free rooms and the reasons other rooms are excluded. Select All saved timetables to compare plan audits; versions are alternatives and are not combined into one room calendar. Optional OpenAI mode uses the server API key described in README. No suggestion is applied automatically.
