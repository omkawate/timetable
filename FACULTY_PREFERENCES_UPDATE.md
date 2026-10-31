# Faculty availability, room preferences and workload

Based on the supplied college-format ZIP and the supplied Faculties_2026-27 spreadsheet. The college-format website/PDF/Excel presentation is retained.

## Faculty timings applied

21 spreadsheet faculty matched existing records. Kalyani Dinde appears only in the spreadsheet; no new faculty or teaching assignment was invented. Five existing faculty not listed in the sheet retain 09:00–17:45. Names, subject mappings, batch identities and assignment counts are unchanged. See docs/FACULTY_TIMINGS_AND_WORKLOAD.md for the complete table and docs/Faculty-timing-source.xlsx for the source.

On the current hourly calendar, 09:45 arrival means the first possible lecture begins at 10:00. A 17:00 departure does not permit a 16:45–17:45 lecture or a 15:45–17:45 practical. Both ends of every session are checked. No teacher or room may be booked twice at the same time.

The nine IKS batch practicals use Auto classroom, restoring the setting requested earlier. All practicals remain two hours and lectures remain one hour. Batches are not combined.

## Preferences

- Faculty directory → Edit faculty → select laboratories. Choose **Required** to allow only those labs (for example, Kadam → 902). Choose **Preferred** to permit another eligible lab if needed. The preference applies to laboratory-based practicals/projects; authorised classroom practicals remain classroom-based.
- Faculty directory → Edit faculty → set the preferred lecture start and end. Example: Vidya Kubde → 10:00–13:00, Required. The entire lecture must fit this window and the faculty's actual working hours. A one-hour window such as 10:00–11:00 can be used when the requested weekly lecture count fits the working days.
- Priority 1–10 weights a **Preferred** lecture window; higher values give it more weight. Required windows are mandatory regardless of priority.
- Classrooms & Labs → Edit room → Preferred academic years. Other years can still use the room if needed. Existing Eligible academic years is the strict restriction and is checked for every allocation.
- Generation reports list sessions using alternatives to soft preferences. They are not presented as mandatory clashes. Required preferences are never silently relaxed.

## Workload

Automatic workload is enabled for the supplied faculty. It derives the weekly teaching limit from actual assigned sessions and sets the daily maximum to the usable teaching periods within arrival/departure. Existing manual limits remain available by unchecking automatic workload.

Three lectures × one hour = 3 faculty hours. Three separate batch practicals × two hours = 6 faculty hours. Tutorial and supervised project durations count as configured. Shared A+B elective lectures with the same teacher count once. Independent Major Project reservations have no faculty workload.

The Faculty Workload screen separates lecture, practical, tutorial and supervised-project hours. Analytics reports actual scheduled hours. Automatic limits remove artificial cap failures; actual availability, required rooms and clashes still cannot be bypassed.

## New semester: Delete all data

Academic setup includes **Delete all data**. Type `DELETE ALL DATA` to confirm. This clears current faculty, subjects, rooms, divisions, batches, electives and assignments. College timings are retained, with an empty General department placeholder for setup. Saved timetable history is retained unless its separate checkbox is selected. A full pre-reset backup is saved in `data/backups` before deletion. Clearing is blocked while generation is running.

## Installation

Stop the old application and back up its data folder. The included database contains the updated faculty timings and workload settings. Do not overwrite it with an older database if you want to use these updates. Start the new folder normally and press Ctrl+F5. Existing saved versions retain their historical settings; generate a new version to apply the new faculty availability.

## Validation

See docs/GENERATION_TEST_REPORT.md for the actual generation outcomes and limits. Successful results are independently audited before saving. A timeout is reported as a timeout; an incomplete candidate is never labelled successful.
