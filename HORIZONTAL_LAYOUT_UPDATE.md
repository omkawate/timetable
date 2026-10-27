# Horizontal timetable presentation

This update is based on the supplied MAIN TIMETABLE.zip. It changes presentation only.

- Days run down the left; period times run across the top.
- Two-hour practicals appear once in a merged cell spanning both periods. Parallel batches remain on separate lines, with their individual teacher and room.
- Lectures, tutorials and projects retain their saved start times, durations and assignments.
- Subject and teacher abbreviations have full-name legends. Abbreviations are display labels, not edits to academic data; duplicate abbreviations receive a numerical suffix.
- Division, professor, classroom and lab views share one layout with PDF and Excel exports.
- PDF uses landscape A3 with embedded fonts and 11-point timetable text. Excel uses real merged cells, 11-point text and landscape printing. Large legends may continue to another printed page rather than shrink the text.
- The small information button opens the existing free-resource check for the complete merged session. Hover over a session for its full names and time range.

## Use

Stop the old application, back up your current data folder, extract this ZIP, and copy your current data folder into the new project if it contains newer data. Start normally and press Ctrl+F5. Existing successful timetables display in the new layout without regenerating.

## Verification

The source database, scheduler and all optimisation modules were compared byte-for-byte with the uploaded ZIP and are unchanged. Only the export code, a read-only layout endpoint and the timetable frontend were modified; presentation modules, fonts and tests were added.

Tests verified layout coverage without overlapping cells, merged two-period labs, source immutability, and PDF/Excel output across 8 divisions, 26 faculty, 7 classrooms and 6 labs. Browser checks covered all four views and the free-resource dialog without JavaScript errors. The verified eight-division PDF fits on eight pages.
