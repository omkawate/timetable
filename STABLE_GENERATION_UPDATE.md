# Repeat-generation stability update

Generation now runs as a background job. Refreshing the browser reconnects to the same search. Repeated submissions with matching settings follow that job instead of starting another search. Other tabs can follow the active job too.

The checked “Reuse a matching successful timetable (fast, revalidated)” option reuses a matching successful arrangement and independently validates it before saving a new draft. Existing saved, approved and locked versions are not overwritten. This works even when “preserve other divisions” is unchecked. Changes to academic data invalidate exact-plan reuse. Uncheck reuse to request a fresh search; changed data and fresh searches may require the full search limit.

The server must remain running during a search. Restarting it stops unfinished jobs; saved timetables remain in Version history. Run using the supplied single-worker run.py launcher.

## Upgrade without losing your current data

1. Stop the old app and back up its entire `data` folder.
2. Extract the new ZIP to a separate folder.
3. Copy your CURRENT `data` folder into the new project, replacing the packaged folder. This preserves your latest subjects, professors, batches, IKS Auto classroom selections and saved timetables.
4. Start the app normally and hard-refresh the browser (Ctrl+F5).

No academic data or scheduling constraints were changed by this update. Two-hour practicals, one-hour lectures, separate batches, configured room eligibility and existing continuity rules remain in force.

## Validation

- 11 automated tests passed, including duplicate-job handling, stale revision rejection and recovery after worker failure.
- Three matching full-department generations completed in 0.84, 0.95 and 0.82 seconds on the test environment, with identical placements and independent validation. These are measured reuse times, not a guarantee for fresh searches.
- A changed faculty record invalidated the cached arrangement.
- Browser test verified refresh recovery, exactly one saved result and no JavaScript errors.
- Tests used disposable copies; the packaged source database was not modified.
