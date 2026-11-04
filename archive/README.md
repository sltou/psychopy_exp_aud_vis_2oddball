# Archive and supporting files

The project root is intentionally limited to the three active task files and `allocation/`. Everything else is organized here.

- `runtime_assets/` contains the stimuli and instruction voiceovers required by the three active tasks. Despite the parent folder name, these files are active and must not be deleted or edited.
- `docs/` contains the protocol, CRC instructions, voiceover record, and randomization records.
- `tools/` contains deployment validation and the local-extra cleanup utility.
- `legacy_builder_sources/` contains old `.psyexp` structural references for possible future redevelopment. Do not run or regenerate the active Python tasks from them.
- `local_extras_<timestamp>/` directories may be created on an experiment computer by `archive/tools/archive_local_extras.py --apply`. They contain recoverable untracked or ignored legacy files from that computer and are intentionally excluded from Git.

Only the three root-level `.py` files are task entry points.
