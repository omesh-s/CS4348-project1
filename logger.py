#!/usr/bin/env python3
"""Read ACTION message lines from stdin and append timestamped log records."""

from datetime import datetime
import sys


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 logger.py LOGFILE", file=sys.stderr)
        return 1
    try:
        with open(sys.argv[1], "a", encoding="utf-8") as logfile:
            for line in sys.stdin:
                parts = line.split(maxsplit=1)
                if not parts:
                    continue
                action = parts[0]
                if action == "QUIT":
                    break
                message = parts[1].rstrip("\r\n") if len(parts) == 2 else ""
                stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                logfile.write(f"{stamp} [{action}] {message}\n")
                logfile.flush()
    except OSError as error:
        print(f"Logger error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
