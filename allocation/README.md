# Allocation files

There are four active allocation files. Only one is edited during enrollment.

## The only CRC-edited file

`participant_profiles.csv` has three columns:

| Column | Purpose | CRC action |
|---|---|---|
| `participant_id` | Study ID entered at PsychoPy launch | Enter the new ID in the first blank row |
| `sequence_id` | Fixed distractor randomization profile | Never edit |
| `pattern_id` | Fixed 10-session task-stimulus profile | Never edit |

The 20 enrollment rows are in a prebalanced order. Always fill from top to bottom. Do not reuse a row after withdrawal, delete an enrolled ID, sort the file, insert rows, or move IDs between rows. The final `test,TEST,PAT07` row is reserved for equipment checks.

After editing, run:

```bash
python3 tools/validate_deployment.py --profiles-only
```

## Fixed backend files

- `pattern_visit_schedule.csv`: one row for each `pattern_id` and session. The task selects one of the visual, auditory-response, or auditory-no-response columns. Auditory response and no-response IDs are different in every pattern/session.
- `auditory_distractor_assignments.csv`: keyed by `sequence_id + session + task`; provides four distractors per block for five blocks. Each sequence uses all 400 main sounds exactly once across the two auditory tasks and ten sessions.
- `visual_distractor_assignments.csv`: keyed by `sequence_id + session + task`; provides four distractors per block for five blocks. Each sequence uses 200 different familiar-object images, with no repeat across ten visual sessions.

The universal practice rows have blank `sequence_id` values. All participants and `test` use the same practice assets, which are separate from the main allocations.

Participant IDs deliberately do not appear in these three backend mapping files. PsychoPy first looks up the participant's fixed `sequence_id` and `pattern_id` in `participant_profiles.csv`, then joins to the backend mappings. This is the single-source-of-truth design.
