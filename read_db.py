import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('tasks.db')
c = conn.cursor()
c.execute("SELECT id, time, tps, result_text FROM jobs WHERE type = 'OCR'")
rows = c.fetchall()

for r in rows:
    print(f"==== {r[0]} ({r[1]:.2f}s | {r[2]:.1f} tps) ====")
    print(r[3])
    print("\n")
