# Generation and verification report — 31 October 2026

## Delivery status

The requested faculty timing, laboratory preference, lecture-window priority, preferred academic year, automatic workload and guarded data reset features are implemented. **A complete eight-division schedule with the updated faculty timings has not yet been verified.** Do not treat this build as confirmation that all eight divisions will generate within the search limit. Failed searches retain the explicit timeout/infeasible status; no incomplete schedule is presented as successful.

## Passing checks

- 15 automated regression tests passed, including required laboratory and lecture-window enforcement, soft-preference fallback, room-year restrictions, CSV/Excel round trips, correct shared-elective workload counting, and reset backup/revision protection.
- Chromium browser check passed: faculty preference save, preferred room year save, workload display and guarded reset, with no JavaScript errors. Reset tests used a disposable database.
- Academic data comparison: all eight divisions, 24 batches, 34 subjects and 191 assignment identities/counts preserved. Professor–subject–batch mappings are unchanged. The nine previously authorized IKS practicals use Auto classroom; all practicals remain two hours and lectures remain one hour.
- Actual-data SE A generation passed in about 11 seconds with Kadam required lab 902, Vidya Kubde required lectures 10:00–13:00 and room 705 preferred for second year. Independent audit: zero hard conflicts and zero internal student gaps.
- Actual-data BE A+B generation passed in about 18 seconds under those preferences. Independent audit: zero hard conflicts and zero internal student gaps.
- Actual-data six-division generation (SE A/B/C, TE A, BE A/B) passed in about 61 seconds under those preferences. Independent audit: zero hard conflicts and zero internal student gaps.

## Remaining limitation

Complete eight-division searches, both with the updated timings alone and with the example preferences, reached the search limit, including 300-second attempts. Adding TE B/C while freezing the six-division result proved infeasible under those specific frozen placements; that does not prove the unrestricted eight-division problem impossible.

Pallavi has 34 assigned teaching hours within 35 usable weekly period-hours. This is a tight constraint, not a proven cause of impossibility. Raising the workload limit cannot create extra availability. Faculty working hours, mandatory preferences, room occupancy, separate batches and student continuity remain enforced.

The example Kadam/Vidya/705 preferences were applied only to disposable test databases. Configure your actual preferences in Faculty directory and Classrooms & Labs. The supplied database contains the spreadsheet faculty timings and automatic workload settings, with no invented faculty assignments.
