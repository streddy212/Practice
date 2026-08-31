#!/usr/bin/env bash
# Wrapper for scheduled runs (cron, Task Scheduler) -- pulls new leads,
# emails a digest of whatever's new, and appends a timestamped record to
# fetch_log.txt so you can see what happened without opening a terminal.
set -euo pipefail
cd "$(dirname "$0")"

{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
  python3 fetch_jobs.py
  python3 send_digest.py
  echo
} >> fetch_log.txt 2>&1
