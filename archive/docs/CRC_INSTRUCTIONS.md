# CRC instructions

## Enroll a participant once

1. Pull the `10_sessions` branch on the experiment computer before enrollment changes are made.
2. Open `allocation/participant_profiles.csv`.
3. Find the first blank cell in the `participant_id` column, starting at `SEQ001` and moving downward.
4. Enter the participant's study ID in that cell only. Do not edit, sort, or autofill the `sequence_id` or `pattern_id` columns.
5. Save as CSV without changing the filename or adding another sheet.
6. From the repository root, run `python3 archive/tools/validate_deployment.py --profiles-only`.
7. Commit and push the updated `participant_profiles.csv` according to the lab's approved data-management procedure so the same enrollment table is used at later sessions.

An enrolled or withdrawn ID stays on its assigned row. Never erase or reuse it. If a participant ID was entered incorrectly, correct that same cell and rerun validation; do not create a second entry.

## Run a participant session

1. Confirm the participant's ID appears exactly once in `allocation/participant_profiles.csv`.
2. Confirm the visit number: `1` through `10`.
3. Start the appropriate generated Python task file:
   - visual response: `visual_oddball_2ob.py`
   - auditory response: `auditory_oddball_2ob.py`
   - auditory no-response: `auditory_no_response_oddball.py`
4. Enter the participant ID exactly as written in the profile table and enter the visit number in the `session` field.
5. Verify the task opens without a configuration error. The resolved `sequence_id`, `pattern_id`, and task stimulus ID are automatically written into the PsychoPy result metadata.
6. Follow the task-specific examiner prompts. Do not manually select stimulus folders or distractor files.

Run all three tasks with the same participant ID and session number. The two auditory tasks will automatically receive different primary stimulus IDs in the same session and disjoint distractor sounds.

## Equipment test

Use participant ID `test` with any session number from `1` through `10`. It resolves to the reserved `TEST` distractor sequence and `PAT07` stimulus pattern. Never replace or remove the `test` row.

## If an error appears

- “Expected one participant profile”: check spelling, capitalization, leading/trailing spaces, and duplicate IDs in `participant_profiles.csv`.
- “Expected one schedule row”: restore `pattern_visit_schedule.csv` from Git; do not repair it manually during a session.
- Missing file or SHA-256 mismatch: stop and restore the deployment from Git. Do not substitute or rename a stimulus.
- Validation failure after enrollment: undo only the most recent participant-ID cell edit or correct it in place, then rerun the profile validator.
