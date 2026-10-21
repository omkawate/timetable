# Generation after a professor-name correction

The uploaded revision-57 database has no saved generation records. Its nine IKS practical offerings correctly use Auto classroom. Compared with the tested data, a professor's title was corrected from “Mra.” to “Mrs.”. The previous exact fingerprint included this display name, so it rejected the built-in verified placement hint and started a fresh search.

The matching logic now ignores only teacher display names. Teacher IDs, assignments, availability, workload, subjects, batches, rooms and scheduling constraints remain part of the match. Both built-in hints and saved timetable reuse still undergo independent validation. New snapshots show the current corrected name; old snapshots remain untouched.

Validation on a disposable copy of the uploaded database: three successful full-department generations in 1.38, 1.35 and 1.40 seconds, identical placements and zero detected hard conflicts. Configuration was unchanged. All 13 automated tests passed, including saved-plan reuse after a name correction and rejection after a teacher-assignment change.

## Install

Stop the existing app. Back up and copy your CURRENT entire `data` folder into this extracted project, replacing its packaged `data` folder. Start the app and press Ctrl+F5. Keep “Reuse a matching successful timetable” enabled. The supplied project database has not been replaced by this update.

Copying only a SQLite database while the app is running can omit recent records held in its WAL file. Stop the app before backing up; preserve the entire data folder. The uploaded file alone does not establish whether its missing generation history was deleted or omitted during copying.
