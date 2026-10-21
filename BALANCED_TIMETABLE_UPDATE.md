# Balanced timetable update

Built from your uploaded RAR and its database. No professor, subject, batch, room, assignment, workload, or weekly session count was changed. Practical duration remains two hours and lectures one hour. Batches are not combined. Labs remain in laboratories.

## New generation option

“Balance practical days and keep tutorials at day edges” is enabled by default. It spreads each batch’s practical sessions across the week, limits daily practical concentration, requires a lecture on every practical day, and places each tutorial at the start or end of the attending batch’s day. Existing no-gap and classroom-continuity checks remain active. Saved historical timetables are not rewritten. Manual edits of new balanced plans must also pass these checks. The default UI search limit is now 120 seconds.

## Validation and limits

Second Year A/B/C and Third Year A/B/C were independently generated and audited as separate scopes: zero hard conflicts, zero internal student gaps, two-hour labs, one-hour lectures, unchanged assignments. These two tests are NOT one combined department timetable and must not be treated as globally clash-free together.

Full-department generation still correctly reports 246 required lab-hours against 240 available lab-hours in six labs, Monday–Friday, 09:00–17:45 excluding recess. This update does not claim to solve that capacity shortage. The supplied manual reference puts some IKS batch sessions in classrooms; that classification was not applied because you asked to preserve your data. No one-hour-practical or paired-batch workaround is included.

## Run/update

Stop the old application and back it up. Extract this ZIP to a new folder and run start_windows.bat. It includes the unchanged database from your uploaded RAR. If you edited data after uploading, replace data/unisched.db with a backup from your stopped current application instead. Refresh the browser with Ctrl+F5. Generate a new timetable to use the balancing rules. Your previous timetable versions remain available.
