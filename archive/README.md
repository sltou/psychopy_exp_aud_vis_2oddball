# Archive

Nothing in this directory is used by the deployed experiment.

- `builder_sources/` contains old `.psyexp` structural references for possible future redevelopment. Do not run or regenerate the active Python tasks from them.
- `local_extras_<timestamp>/` directories may be created on an experiment computer by `tools/archive_local_extras.py --apply`. They contain recoverable untracked or ignored legacy files from that computer and are intentionally excluded from Git.

The active experiment consists of the three root-level Python task files plus `allocation/`, `stimuli/`, and `resource/voiceover/`. The `docs/` and `tools/` directories support operation and validation.
