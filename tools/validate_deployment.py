#!/usr/bin/env python3
"""Validate the portable 10-session PsychoPy deployment."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import struct
import sys
import wave
from collections import Counter, defaultdict
from pathlib import Path


TASK_SCRIPTS = (
    "visual_oddball_2ob.py",
    "auditory_oddball_2ob.py",
    "auditory_no_response_oddball.py",
)
SCRIPT_REQUIREMENTS = {
    "visual_oddball_2ob.py": (
        "TASK_MODE = 'VIS'",
        "SCHEDULE_COLUMN = 'visual_stimulus_id'",
        "task_ID_code = 111",
    ),
    "auditory_oddball_2ob.py": (
        "TASK_MODE = 'AUR'",
        "SCHEDULE_COLUMN = 'auditory_response_stimulus_id'",
        "task_ID_code = 110",
        "if auditory_no_response_id == auditory_stimulus_id:",
    ),
    "auditory_no_response_oddball.py": (
        "TASK_MODE = 'AUN'",
        "SCHEDULE_COLUMN = 'auditory_no_response_stimulus_id'",
        "task_ID_code = 112",
        "if auditory_response_id == auditory_stimulus_id:",
    ),
}
EXPECTED_SEQUENCES = tuple(
    ["SEQ{:03d}".format(index) for index in range(1, 21)] + ["TEST"]
)
EXPECTED_PATTERNS = tuple("PAT{:02d}".format(index) for index in range(1, 9))
EXPECTED_PROFILE_PATTERNS = (
    "PAT07", "PAT05", "PAT01", "PAT04", "PAT08",
    "PAT02", "PAT04", "PAT03", "PAT02", "PAT04",
    "PAT03", "PAT06", "PAT08", "PAT01", "PAT01",
    "PAT07", "PAT07", "PAT06", "PAT06", "PAT05",
    "PAT07",  # TEST
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profiles-only",
        action="store_true",
        help="Check participant profile edits without hashing the media bank.",
    )
    return parser.parse_args()


def fail(message: str) -> None:
    raise RuntimeError(message)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        fail("Missing {}".format(path))
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_profiles(root: Path) -> list[dict[str, str]]:
    path = root / "allocation" / "participant_profiles.csv"
    rows = read_csv(path)
    if len(rows) != 21:
        fail("participant_profiles.csv must contain 20 enrollment rows plus TEST")
    expected_fields = ["participant_id", "sequence_id", "pattern_id"]
    if list(rows[0]) != expected_fields:
        fail("participant_profiles.csv columns must be {}".format(expected_fields))
    sequences = tuple(row["sequence_id"].strip() for row in rows)
    if sequences != EXPECTED_SEQUENCES:
        fail("Sequence rows were reordered or changed")
    patterns = tuple(row["pattern_id"].strip() for row in rows)
    if patterns != EXPECTED_PROFILE_PATTERNS:
        fail("The prebalanced pattern_id assignments were reordered or changed")
    test_rows = [row for row in rows if row["sequence_id"].strip() == "TEST"]
    if len(test_rows) != 1 or test_rows[0]["participant_id"].strip().lower() != "test":
        fail("TEST must have participant_id=test")
    participant_ids = [
        row["participant_id"].strip() for row in rows
        if row["participant_id"].strip()
    ]
    folded = [value.casefold() for value in participant_ids]
    duplicates = [value for value, count in Counter(folded).items() if count > 1]
    if duplicates:
        fail("Duplicate participant IDs: {}".format(", ".join(duplicates)))
    if any("," in value or "\n" in value or "\r" in value for value in participant_ids):
        fail("Participant IDs may not contain commas or line breaks")
    enrollment_ids = [row["participant_id"].strip() for row in rows[:-1]]
    seen_blank = False
    for row_number, participant_id in enumerate(enrollment_ids, start=2):
        if not participant_id:
            seen_blank = True
        elif seen_blank:
            fail(
                "Enrollment rows must be filled from top to bottom; participant ID "
                "on CSV row {} follows a blank row".format(row_number)
            )
    print(
        "Profiles: 20 enrollment sequences, TEST enabled, {} participant IDs filled"
        .format(len(participant_ids) - 1)
    )
    return rows


def validate_pattern_schedule(root: Path, profiles: list[dict[str, str]]) -> None:
    rows = read_csv(root / "allocation" / "pattern_visit_schedule.csv")
    if len(rows) != 80:
        fail("pattern_visit_schedule.csv must contain 8 patterns x 10 sessions")
    seen = set()
    for row in rows:
        pattern = row["pattern_id"].strip()
        session = int(row["session"])
        key = (pattern, session)
        if pattern not in EXPECTED_PATTERNS or session not in range(1, 11):
            fail("Invalid pattern/session in pattern_visit_schedule.csv")
        if key in seen:
            fail("Duplicate pattern/session {}".format(key))
        seen.add(key)
        visual = row["visual_stimulus_id"].strip()
        aur = row["auditory_response_stimulus_id"].strip()
        aun = row["auditory_no_response_stimulus_id"].strip()
        if not visual.startswith("VIS-") or not aur.startswith("AUD-") or not aun.startswith("AUD-"):
            fail("Invalid task stimulus ID for {}".format(key))
        if aur == aun:
            fail("AUR and AUN match for {}".format(key))
    if seen != {(pattern, session) for pattern in EXPECTED_PATTERNS for session in range(1, 11)}:
        fail("Pattern/session coverage is incomplete")
    used_patterns = {row["pattern_id"].strip() for row in profiles}
    if not used_patterns.issubset(set(EXPECTED_PATTERNS)):
        fail("A participant profile references an unknown pattern")
    print("Pattern schedule: 8 patterns x 10 sessions; AUR and AUN never match")


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        fail("Invalid PNG header: {}".format(path))
    return struct.unpack(">II", header[16:24])


def validate_primary_stimuli(root: Path) -> None:
    visual_root = root / "stimuli" / "visual"
    auditory_root = root / "stimuli" / "auditory"
    visual_sets = sorted(path for path in visual_root.iterdir() if path.is_dir())
    auditory_sets = sorted(path for path in auditory_root.iterdir() if path.is_dir())
    if len(visual_sets) != 10 or len(auditory_sets) != 10:
        fail("Expected 10 visual and 10 auditory stimulus folders")
    for folder in visual_sets:
        svgs = sorted(folder.glob("*.svg"))
        pngs = sorted(folder.glob("*.png"))
        if len(svgs) != 5 or len(pngs) != 5:
            fail("{} must contain five SVG/PNG pairs".format(folder))
        if [path.stem for path in svgs] != [path.stem for path in pngs]:
            fail("SVG/PNG names do not match in {}".format(folder))
        if any(png_size(path) != (1000, 1000) for path in pngs):
            fail("Visual deployment PNGs must be 1000x1000")
    for folder in auditory_sets:
        files = sorted(folder.glob("*.wav"))
        if len(files) != 5:
            fail("{} must contain five WAV files".format(folder))
        for path in files:
            with wave.open(str(path), "rb") as handle:
                values = (
                    handle.getframerate(),
                    handle.getnchannels(),
                    handle.getsampwidth(),
                    handle.getnframes(),
                )
            if values != (44100, 2, 2, 11025):
                fail("Primary auditory WAV has unexpected format: {} {}".format(path, values))
    print("Primary stimuli: 10 visual and 10 auditory sets validated")


def validate_assignment(
    root: Path,
    filename: str,
    expected_per_sequence: int,
    expected_tasks: tuple[str, ...],
) -> None:
    rows = read_csv(root / "allocation" / filename)
    expected_fields = [
        "sequence_id", "session", "task", "phase", "block",
        "distractor_slot", "distractor_id", "distractor_file", "sha256",
    ]
    if list(rows[0]) != expected_fields:
        fail("{} has unexpected columns".format(filename))
    practice = [row for row in rows if row["phase"].strip().lower() == "practice"]
    main = [row for row in rows if row["phase"].strip().lower() == "main"]
    if len(practice) != 1 or practice[0]["sequence_id"].strip():
        fail("{} must contain one universal practice row".format(filename))
    grouped = defaultdict(list)
    for row in main:
        grouped[row["sequence_id"].strip()].append(row)
    if set(grouped) != set(EXPECTED_SEQUENCES):
        fail("{} does not cover all sequences including TEST".format(filename))
    for sequence, sequence_rows in grouped.items():
        if len(sequence_rows) != expected_per_sequence:
            fail("{} has the wrong row count for {}".format(filename, sequence))
        files = [row["distractor_file"].strip() for row in sequence_rows]
        hashes = [row["sha256"].strip().lower() for row in sequence_rows]
        if len(files) != len(set(files)) or len(hashes) != len(set(hashes)):
            fail("{} repeats a distractor within {}".format(filename, sequence))
        for session in range(1, 11):
            for task in expected_tasks:
                subset = [
                    row for row in sequence_rows
                    if int(row["session"]) == session and row["task"].strip() == task
                ]
                if len(subset) != 20:
                    fail("{} {} session {} task {} does not have 20 rows".format(filename, sequence, session, task))
                keys = {
                    (int(row["block"]), int(row["distractor_slot"]))
                    for row in subset
                }
                if keys != {(block, slot) for block in range(1, 6) for slot in range(1, 5)}:
                    fail("Invalid block/slot coverage in {}".format(filename))

    expected_hash_by_file = {}
    for row in rows:
        relative = row["distractor_file"].strip()
        expected = row["sha256"].strip().lower()
        if relative in expected_hash_by_file and expected_hash_by_file[relative] != expected:
            fail("Conflicting hashes for {}".format(relative))
        expected_hash_by_file[relative] = expected
    for relative, expected in expected_hash_by_file.items():
        path = root / relative
        if not path.is_file():
            fail("Missing assigned distractor {}".format(relative))
        if sha256_file(path) != expected:
            fail("SHA-256 mismatch for {}".format(relative))
    print(
        "{}: {} sequences including TEST, no within-sequence repeats, hashes valid"
        .format(filename, len(grouped))
    )


def validate_media_banks(root: Path) -> None:
    audio = sorted(
        path
        for path in (root / "stimuli" / "distractors" / "auditory").rglob("*")
        if path.is_file() and path.suffix.lower() == ".wav"
    )
    visual = sorted((root / "stimuli" / "distractors" / "visual" / "IMAGINE_familiar" / "png").glob("*.png"))
    book = root / "stimuli" / "distractors" / "visual" / "practice" / "book.png"
    if len(audio) != 401 or len(visual) != 400 or not book.is_file():
        fail("Distractor bank count mismatch")
    if any(png_size(path) != (1000, 1000) for path in visual + [book]):
        fail("Visual distractors must use 1000x1000 deployment canvases")
    print("Media banks: 401 auditory, 400 visual main, 1 visual practice")


def validate_scripts_and_voiceovers(root: Path) -> None:
    referenced = set()
    forbidden = (
        "participant_visit_schedule_20.csv",
        "enrollment_ledger.csv",
        "allocation_slot",
    )
    for filename in TASK_SCRIPTS:
        path = root / filename
        source = path.read_text(encoding="utf-8-sig")
        compile(source, str(path), "exec")
        for required in SCRIPT_REQUIREMENTS[filename]:
            if required not in source:
                fail("{} is missing required logic: {}".format(filename, required))
        for required in (
            "regular_p300_code = 41",
            "oddball_p300_code = 42",
            "distractor_p300_code = 43",
        ):
            if required not in source:
                fail("{} is missing trigger definition {}".format(filename, required))
        for value in forbidden:
            if value in source:
                fail("{} still references outdated allocation field {}".format(filename, value))
        referenced.update(re.findall(r"resource/voiceover/[A-Za-z0-9_./-]+\.wav", source))
    voice_files = {
        path.relative_to(root).as_posix()
        for path in (root / "resource" / "voiceover").rglob("*.wav")
    }
    if len(voice_files) != 26:
        fail("Expected 26 deployed voiceovers; found {}".format(len(voice_files)))
    if referenced != voice_files:
        fail(
            "Voiceover references differ from deployed files; missing={}, unused={}"
            .format(sorted(referenced - voice_files), sorted(voice_files - referenced))
        )
    print("Task scripts: syntax valid; all {} voiceovers referenced exactly once or more".format(len(voice_files)))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    args = parse_args()
    try:
        profiles = validate_profiles(root)
        if args.profiles_only:
            print("Profile validation passed.")
            return 0
        validate_pattern_schedule(root, profiles)
        validate_primary_stimuli(root)
        validate_media_banks(root)
        validate_assignment(
            root,
            "auditory_distractor_assignments.csv",
            expected_per_sequence=400,
            expected_tasks=("AUR", "AUN"),
        )
        validate_assignment(
            root,
            "visual_distractor_assignments.csv",
            expected_per_sequence=200,
            expected_tasks=("VIS",),
        )
        validate_scripts_and_voiceovers(root)
    except Exception as error:
        print("VALIDATION FAILED: {}".format(error), file=sys.stderr)
        return 1
    print("Full deployment validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
