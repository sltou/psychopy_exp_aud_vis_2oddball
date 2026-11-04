# Ten-session oddball study

This branch is the portable deployment for the 10-session study. It contains the three PsychoPy task scripts, primary stimuli, fixed distractor allocations, instruction voiceovers, and the enrollment table. After cloning or pulling this branch, the tasks use relative paths and do not need any computer-specific stimulus configuration.

## Enrollment model

`allocation/participant_profiles.csv` is the only file that stores participant IDs. A CRC enters a new ID in the first blank `participant_id` cell and changes nothing else.

```text
participant ID entered in PsychoPy
              |
              v
participant_profiles.csv
   | sequence_id                 | pattern_id
   v                             v
distractor assignment CSVs   pattern_visit_schedule.csv
   |                             |
   +------------ session + task--+
                     |
                     v
        exact stimuli for this task run
```

- `pattern_id` determines the visual, auditory-response, and auditory-no-response stimulus set for each of the 10 sessions.
- `sequence_id` determines the fixed randomized distractors for all three tasks and all 10 sessions.
- The participant ID is not copied into the schedule or distractor files, which removes the possibility of inconsistent participant entries.
- `test` is already assigned to `TEST` / `PAT07` for equipment checks.

See [allocation/README.md](allocation/README.md) and [docs/CRC_INSTRUCTIONS.md](docs/CRC_INSTRUCTIONS.md) for the exact workflow.

## Run the tasks

Use the PsychoPy version and lab hardware configuration already established on the experiment computer. Run the generated Python files directly:

- `visual_oddball_2ob.py` — visual response task (`VIS`)
- `auditory_oddball_2ob.py` — auditory response task (`AUR`)
- `auditory_no_response_oddball.py` — passive auditory task (`AUN`)

At launch, enter the participant ID exactly as recorded in `participant_profiles.csv` and enter session `1` through `10`. Each script resolves and validates its stimulus set and distractor files before continuing.

Do not open, save, or regenerate the Builder files on a computer with a different PsychoPy version. The `.psyexp` files in `builder_sources/` are retained as structural source references; the deployed `.py` files contain the current allocation logic.

## Preflight validation

From the repository root:

```bash
python3 tools/validate_deployment.py --profiles-only
python3 tools/validate_deployment.py
```

The first command is the quick check after enrollment edits. The second verifies mappings, media counts, hashes, stimulus formats, no-repeat constraints, and Python syntax. It does not launch PsychoPy or alter experiment files.

## Repository layout

- `allocation/` — the one enrollment table plus fixed pattern and distractor mappings
- `stimuli/visual/` — 10 visual sets, with SVG masters and same-size PNG deployment copies
- `stimuli/auditory/` — 10 auditory sets, each containing five 250 ms WAV files
- `stimuli/distractors/` — auditory distractors, 400 familiar-object images, and practice assets
- `resource/voiceover/` — task-specific neutral American female instruction recordings
- `docs/` — protocol, CRC workflow, voiceover record, and randomization records
- `builder_sources/` — preserved Builder source references
- `tools/` — read-only deployment validation

## Trigger codes

The existing lab hardware interface and response mapping are preserved.

| Event | Code |
|---|---:|
| Task start | 100 |
| Auditory response task | 110 |
| Visual response task | 111 |
| Auditory no-response task | 112 |
| Block start | 122 |
| Block end | 123 |
| EEG recording start | 126 |
| EEG recording stop | 127 |
| Standard stimulus | 41 |
| Target stimulus | 42 |
| Distractor stimulus | 43 |

Output data are written under `data/<participant_id>/`; `data/` is intentionally excluded from Git.
