#!/usr/bin/env python3
"""Preview or archive local files that are not part of this Git deployment."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROTECTED_TOP_LEVEL = {".git", "archive", "data"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Move the previewed files into a timestamped archive.",
    )
    return parser.parse_args()


def git_root(script_root: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(script_root),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    root = Path(result.stdout.strip()).resolve()
    if root != script_root.resolve():
        raise RuntimeError(
            "This utility must remain inside the deployment repository: {}"
            .format(script_root)
        )
    return root


def tracked_files(root: Path) -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=str(root),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        value.decode("utf-8", errors="surrogateescape")
        for value in result.stdout.split(b"\0")
        if value
    }


def local_extras(root: Path, tracked: set[str]) -> list[Path]:
    extras = []
    for current, directory_names, file_names in os.walk(root, topdown=True):
        current_path = Path(current)
        relative_current = current_path.relative_to(root)
        if relative_current.parts:
            top_level = relative_current.parts[0]
            if top_level in PROTECTED_TOP_LEVEL:
                directory_names[:] = []
                continue
        directory_names[:] = [
            name for name in directory_names
            if not (
                (relative_current / name).parts
                and (relative_current / name).parts[0] in PROTECTED_TOP_LEVEL
            )
        ]
        for name in file_names:
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if Path(relative).parts[0] in PROTECTED_TOP_LEVEL:
                continue
            if relative not in tracked:
                extras.append(path)
        for name in list(directory_names):
            path = current_path / name
            if path.is_symlink():
                relative = path.relative_to(root).as_posix()
                if relative not in tracked:
                    extras.append(path)
                directory_names.remove(name)
    return sorted(extras, key=lambda path: path.relative_to(root).as_posix())


def new_archive_directory(root: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = root / "archive" / "local_extras_{}".format(stamp)
    suffix = 1
    while candidate.exists():
        candidate = root / "archive" / "local_extras_{}_{}".format(stamp, suffix)
        suffix += 1
    return candidate


def remove_empty_directories(root: Path) -> None:
    for current, directory_names, _ in os.walk(root, topdown=False):
        path = Path(current)
        if path == root:
            continue
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] in PROTECTED_TOP_LEVEL:
            continue
        try:
            path.rmdir()
        except OSError:
            pass


def main() -> int:
    args = parse_args()
    script_root = Path(__file__).resolve().parents[1]
    try:
        root = git_root(script_root)
        extras = local_extras(root, tracked_files(root))
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print("ARCHIVE CHECK FAILED: {}".format(error), file=sys.stderr)
        return 1

    if not extras:
        print("No local files exist outside the tracked deployment.")
        return 0

    print("Local non-deployment files ({}):".format(len(extras)))
    for path in extras:
        print("  {}".format(path.relative_to(root).as_posix()))

    if not args.apply:
        print("\nPreview only; nothing was moved.")
        print("Run again with --apply to move these files into archive/.")
        return 0

    destination_root = new_archive_directory(root)
    for source in extras:
        relative = source.relative_to(root)
        destination = destination_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
    remove_empty_directories(root)
    print("\nMoved {} files to {}".format(
        len(extras), destination_root.relative_to(root).as_posix()
    ))
    print("The archive is recoverable and ignored by Git.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
