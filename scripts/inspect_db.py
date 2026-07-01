import os

import duckdb

db_path = "data/duckdb/edu_planning.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} does not exist.")
    exit(1)

conn = duckdb.connect(db_path)
try:
    print("--- Table: majors ---")
    res = conn.execute("DESCRIBE majors;").fetchall()
    for row in res:
        print(row)

    print("\n--- Constraints (via PRAGMA table_info) ---")
    res = conn.execute("PRAGMA table_info('majors');").fetchall()
    for row in res:
        print(row)

    print("\n--- Indexes ---")
    res = conn.execute("PRAGMA show_indexes('majors');").fetchall()
    for row in res:
        print(row)

finally:
    conn.close()
