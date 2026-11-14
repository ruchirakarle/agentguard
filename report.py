"""Print a summary of everything in the log. Use these numbers on your resume."""
import sqlite3

from logger import DB_PATH

if not DB_PATH.exists():
    print("No log yet. Run 'pytest' first.")
    raise SystemExit

conn = sqlite3.connect(DB_PATH)
total = conn.execute("SELECT COUNT(*) FROM actions").fetchone()[0]
blocked = conn.execute("SELECT COUNT(*) FROM actions WHERE status LIKE 'blocked%'").fetchone()[0]
print(f"\nTotal tool calls logged : {total}")
print(f"Blocked                 : {blocked}")
print("\nBy status:")
print(f"  {'status':<18}{'count':>7}{'avg ms':>10}")
for status, count, avg in conn.execute(
    "SELECT status, COUNT(*), AVG(duration_ms) FROM actions GROUP BY status ORDER BY COUNT(*) DESC"
):
    print(f"  {status:<18}{count:>7}{avg:>10.0f}")

ok_runs = [r[0] for r in conn.execute(
    "SELECT duration_ms FROM actions WHERE tool='run_python' AND status='ok' ORDER BY duration_ms"
)]
if ok_runs:
    print(f"\nMedian sandbox run time : {ok_runs[len(ok_runs) // 2]:.0f} ms")
conn.close()
