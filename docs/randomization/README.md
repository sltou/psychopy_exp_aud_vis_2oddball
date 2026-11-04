# Distractor randomization records

The two JSON records preserve the randomization method, master seed, per-sequence derived seeds, bank size, assignment file hash, practice asset, and generation timestamp.

For each of `SEQ001` through `SEQ020` and `TEST`, a deterministic sequence seed was derived as SHA-256 of `master_seed + ":" + sequence_id`. A Python Fisher–Yates shuffle then produced an independent ordering for that sequence.

- Auditory: all 400 nonpractice WAVs are assigned once across 10 sessions × 2 tasks × 20 distractors. No main sound repeats within a sequence.
- Visual: the first 200 items of the independently shuffled 400-image familiar-object bank are assigned across 10 sessions × 20 distractors. No main image repeats within a sequence.

The PsychoPy tasks do not randomize which distractor file is assigned to a trial slot. They read the fixed assignment rows. They still generate the standard/target/distractor presentation order within each constrained 10-trial chunk at runtime.

Do not edit the JSON or assignment CSV files during enrollment. Participant linkage is exclusively through `allocation/participant_profiles.csv`.
