import gzip
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import log_cleanup

DAY = 24 * 60 * 60


def make_file(path: Path, days_old: int, content: bytes = b"hello\n") -> Path:
    path.write_bytes(content)
    ts = time.time() - days_old * DAY
    os.utime(path, (ts, ts))
    return path


def test_plan_picks_only_old_files(tmp_path):
    old_log = make_file(tmp_path / "old.log", 10)
    make_file(tmp_path / "new.log", 1)
    old_gz = make_file(tmp_path / "ancient.log.gz", 40)
    make_file(tmp_path / "recent.log.gz", 5)

    to_compress, to_delete = log_cleanup.plan(tmp_path, compress_after=7, delete_after=30)

    assert to_compress == [old_log]
    assert to_delete == [old_gz]


def test_dry_run_changes_nothing(tmp_path):
    make_file(tmp_path / "old.log", 10)
    log_cleanup.main([str(tmp_path)])
    assert (tmp_path / "old.log").exists()
    assert not (tmp_path / "old.log.gz").exists()


def test_apply_compresses_and_deletes(tmp_path):
    make_file(tmp_path / "old.log", 10, b"line 1\nline 2\n")
    make_file(tmp_path / "ancient.log.gz", 40)

    log_cleanup.main([str(tmp_path), "--apply"])

    assert not (tmp_path / "old.log").exists()
    assert not (tmp_path / "ancient.log.gz").exists()
    with gzip.open(tmp_path / "old.log.gz") as fh:
        assert fh.read() == b"line 1\nline 2\n"
