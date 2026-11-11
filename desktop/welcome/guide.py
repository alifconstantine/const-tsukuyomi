#!/usr/bin/python
"""Panduan shortcut QML; marker hanya ditulis sesudah penutupan normal."""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import sys

from catalog import dismiss_welcome, welcome_marker


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--first-login', action='store_true')
    args = parser.parse_args()
    marker = welcome_marker()
    runtime = Path(os.environ['XDG_RUNTIME_DIR'])
    with (runtime / 'constos-welcome.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        if args.first_login and marker.is_file():
            return 0
        result = subprocess.run(['/usr/bin/qs', '-p', str(Path(__file__).resolve().parent / 'qml')])
        if result.returncode == 0:
            dismiss_welcome(marker)
        return result.returncode


if __name__ == '__main__':
    sys.exit(main())
