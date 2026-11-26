#!/usr/bin/env python3
"""log_cleanup.py — compress old log files and delete very old archives.

Rules (defaults):
  * *.log files older than 7 days  -> gzip to *.log.gz (original removed)
  * *.log.gz files older than 30 days -> deleted

Usage:
  python3 log_cleanup.py /var/log/myapp            # dry run, prints the plan
  python3 log_cleanup.py /var/log/myapp --apply    # actually do it
"""

from __future__ import annotations

import argparse
import gzip
import shutil
import sys
import time
from pathlib import Path

DAY = 24 * 60 * 60


def age_days(path: Path, now: float) -> float:
    return (now - path.stat().st_mtime) / DAY


def plan(log_dir: Path, compress_after: int, delete_after: int, now: float | None = None):
    """Return (to_compress, to_delete) lists without touching any file."""
    now = now if now is not None else time.time()
    to_compress = [p for p in sorted(log_dir.rglob("*.log")) if age_days(p, now) > compress_after]
    to_delete = [p for p in sorted(log_dir.rglob("*.log.gz")) if age_days(p, now) > delete_after]
    return to_compress, to_delete


def compress(path: Path) -> Path:
    target = path.with_name(path.name + ".gz")
    with path.open("rb") as src, gzip.open(target, "wb") as dst:
        shutil.copyfileobj(src, dst)
    shutil.copystat(path, target)  # keep the original timestamp for the delete rule
    path.unlink()
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("log_dir", type=Path)
    parser.add_argument("--compress-after", type=int, default=7, help="days (default 7)")
    parser.add_argument("--delete-after", type=int, default=30, help="days (default 30)")
    parser.add_argument("--apply", action="store_true", help="make changes (default is dry run)")
    args = parser.parse_args(argv)

    if not args.log_dir.is_dir():
        print(f"error: {args.log_dir} is not a directory", file=sys.stderr)
        return 2

    to_compress, to_delete = plan(args.log_dir, args.compress_after, args.delete_after)
    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"[{mode}] compress {len(to_compress)} file(s), delete {len(to_delete)} archive(s)")

    for path in to_compress:
        print(f"  compress {path}")
        if args.apply:
            compress(path)
    for path in to_delete:
        print(f"  delete   {path}")
        if args.apply:
            path.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
