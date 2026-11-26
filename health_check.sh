#!/usr/bin/env bash
# health_check.sh — quick server health report for Linux hosts.
# Checks CPU load, memory, disk usage and failed systemd services.
# Exit code: 0 = healthy, 1 = at least one threshold exceeded.
#
# Usage: ./health_check.sh [-d DISK_PCT] [-m MEM_PCT] [-l LOAD_PER_CPU] [-o REPORT_FILE]

set -euo pipefail

DISK_LIMIT=80      # % used per filesystem
MEM_LIMIT=85       # % memory used
LOAD_LIMIT=1.5     # 1-minute load average per CPU core
REPORT=""

while getopts "d:m:l:o:h" opt; do
  case "$opt" in
    d) DISK_LIMIT="$OPTARG" ;;
    m) MEM_LIMIT="$OPTARG" ;;
    l) LOAD_LIMIT="$OPTARG" ;;
    o) REPORT="$OPTARG" ;;
    h|*) grep '^# Usage' "$0" | sed 's/^# //'; exit 0 ;;
  esac
done

status=0
lines=()

log() { lines+=("$1"); }
warn() { lines+=("[WARN] $1"); status=1; }

log "Health check for $(hostname) at $(date '+%Y-%m-%d %H:%M:%S')"

# --- CPU load ---------------------------------------------------------------
cores=$(nproc)
load1=$(cut -d ' ' -f1 /proc/loadavg)
load_per_core=$(awk -v l="$load1" -v c="$cores" 'BEGIN { printf "%.2f", l / c }')
if awk -v x="$load_per_core" -v y="$LOAD_LIMIT" 'BEGIN { exit !(x > y) }'; then
  warn "CPU load ${load_per_core}/core (limit ${LOAD_LIMIT})"
else
  log "[OK]   CPU load ${load_per_core}/core"
fi

# --- Memory -----------------------------------------------------------------
mem_pct=$(free | awk '/^Mem:/ { printf "%d", ($2 - $7) / $2 * 100 }')
if (( mem_pct > MEM_LIMIT )); then
  warn "Memory ${mem_pct}% used (limit ${MEM_LIMIT}%)"
else
  log "[OK]   Memory ${mem_pct}% used"
fi

# --- Disk -------------------------------------------------------------------
while read -r use mount; do
  pct=${use%\%}
  if (( pct > DISK_LIMIT )); then
    warn "Disk ${mount} ${pct}% used (limit ${DISK_LIMIT}%)"
  else
    log "[OK]   Disk ${mount} ${pct}% used"
  fi
done < <(df -P -x tmpfs -x devtmpfs -x overlay | awk 'NR > 1 { print $5, $6 }')

# --- Failed services (systemd hosts only) -----------------------------------
if command -v systemctl >/dev/null 2>&1; then
  failed=$(systemctl --failed --no-legend 2>/dev/null | awk '{ print $1 }' | tr '\n' ' ')
  if [[ -n "${failed// /}" ]]; then
    warn "Failed services: ${failed}"
  else
    log "[OK]   No failed systemd services"
  fi
fi

# --- Output -----------------------------------------------------------------
printf '%s\n' "${lines[@]}"
if [[ -n "$REPORT" ]]; then
  printf '%s\n' "${lines[@]}" >> "$REPORT"
fi

exit "$status"
