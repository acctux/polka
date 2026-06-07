#!/usr/bin/env python3
import subprocess
import tempfile
from pathlib import Path
import os
import sys


def y(*args):
    with tempfile.NamedTemporaryFile(prefix="yazi-cwd.", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        subprocess.run(["yazi", *args, f"--cwd-file={tmp_path}"], check=True)
        cwd = tmp_path.read_text().strip()
        if cwd and Path(cwd).is_dir() and cwd != str(Path.cwd()):
            os.chdir(cwd)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


if __name__ == "__main__":
    y(*sys.argv[1:])
