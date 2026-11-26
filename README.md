# Linux Health Check & Log Cleanup

Bash and Python scripts that automate routine Linux maintenance: a server health report and a log cleanup job, with a CI pipeline that lints and tests every change.

| File | What it does |
| --- | --- |
| `health_check.sh` | Checks CPU load per core, memory, disk usage and failed systemd services. Exits `1` if any threshold is exceeded, so cron or monitoring can alert on it. |
| `log_cleanup.py` | Compresses `*.log` files older than 7 days and deletes `*.log.gz` archives older than 30 days. Dry run by default. |
| `tests/` | pytest tests for the cleanup rules. |
| `.github/workflows/ci.yml` · `.gitlab-ci.yml` | Same pipeline for GitHub Actions and GitLab CI: `shellcheck` + `ruff` lint, then `pytest` and a smoke run of the health check. |

## Run it

```bash
# Health check with default limits (disk 80%, memory 85%, load 1.5/core)
./health_check.sh

# Custom limits, append the report to a file
./health_check.sh -d 90 -m 90 -o /tmp/health.log

# Log cleanup: preview first, then apply
python3 log_cleanup.py /var/log/myapp
python3 log_cleanup.py /var/log/myapp --apply

# Tests
pip install pytest && pytest -v
```

Example output:

```text
Health check for web-01 at 2026-11-26 09:00:00
[OK]   CPU load 0.21/core
[OK]   Memory 42% used
[WARN] Disk /var 86% used (limit 80%)
[OK]   No failed systemd services
```

## Schedule with cron

```cron
*/15 * * * *  /opt/scripts/health_check.sh -o /var/log/health.log
0 2 * * *     /usr/bin/python3 /opt/scripts/log_cleanup.py /var/log/myapp --apply
```

## Design choices

- **Exit codes over emails:** the script only reports and returns a status, so it plugs into cron, CI or a monitoring agent.
- **Dry run by default:** the cleanup script never deletes anything unless `--apply` is passed.
- **Timestamps kept on compress:** `.gz` files keep the original modified time, so the 30-day delete rule counts from when the log was written.

## What I learned

<!-- Write 3-4 lines in your own words: problems you hit, what you would improve next. -->
