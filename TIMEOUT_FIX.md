# Full-department timeout fix

The old search enforced a 9:00 arrival for every batch every day. The manual reference permits later arrivals while keeping the student's teaching day consecutive. New generations allow that flexibility within the same college opening/closing times. Internal gaps are still prohibited, and batch tutorials remain at day edges.

The generation form has an optional “Require every batch to start at college opening time” checkbox. Leave it unchecked for the verified complete plan. Turning it on imposes the stricter policy and may need more search time or be infeasible. Existing saved plans keep their original policy.

The solver first uses compact session intervals for compatible room pools. It tries regular lab start blocks first, then all valid starts if necessary; this does not change allowed practical duration. Other room configurations and preserved/locked plans use the general solver. A five-minute search option is also available. Exact-input verified hints are independently audited before reuse; academic edits invalidate them.

## Verified result

Using the last uploaded database, with all nine IKS batch assignments explicitly set to Auto classroom, the API generated all eight divisions together in approximately 25 seconds in the test environment. Independent audit: zero teacher/room/student clashes, zero internal gaps, zero early classroom changes. PDF and Excel exports passed. Runtime varies by computer and data.

Two-hour practicals, one-hour lectures, separate batch bookings, teacher/subject mappings, weekly counts, laboratory eligibility for technical practicals, and faculty limits were retained. No batches were combined. No academic data or room inventory was automatically changed.

## Upgrade without losing your IKS choices

1. Stop UniSched and back up your current project folder.
2. Extract the new ZIP into a new folder.
3. Copy your CURRENT data folder (including unisched.db) into the new folder, replacing the bundled older database. The bundled database is the unchanged last upload, not your later local edits.
4. Start with start_windows.bat, then press Ctrl+F5.
5. Keep IKS batch assignments set to Auto classroom. Generate all divisions with a 120-second search limit and the opening-time checkbox unchecked. For a fresh full plan, uncheck preservation of other divisions.

No extra teaching hours, additional labs, or reduced session durations were introduced.
