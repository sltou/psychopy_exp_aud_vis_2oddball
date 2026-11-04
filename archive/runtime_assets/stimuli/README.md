# Stimulus package

Primary stimulus folders are immutable deployment inputs. Folder names are the unique stimulus IDs used by `allocation/pattern_visit_schedule.csv`.

- `visual/`: 10 sets. Every set has five numbered SVG vector masters and five matching transparent 1000 × 1000 PNG deployment files.
- `auditory/`: 10 sets. Every set has five numbered, 250 ms, 44.1 kHz stereo, 16-bit PCM WAV files.
- `distractors/auditory/`: 400 standardized main distractors plus the universal `DESRA/BIRDA2.WAV` practice sound.
- `distractors/visual/IMAGINE_familiar/png/`: 400 transparent, standardized 1000 × 1000 familiar-object images. Source attribution is retained beside the bank.
- `distractors/visual/practice/book.png`: separate practice-only image.

Do not rename, replace, normalize, or edit deployed media after allocation. Assignment CSVs contain both relative paths and SHA-256 hashes; the tasks will reject altered or missing files.
