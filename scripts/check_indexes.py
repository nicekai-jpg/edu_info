
import duckdb

db_path = "data/duckdb/edu_planning.db"
conn = duckdb.connect(db_path)
try:
    print("--- Indexes ---")
    res = conn.execute("SELECT * FROM duckdb_indexes WHERE table_name = 'majors';").fetchall()
    for row in res:
        print(row)
finally:
    conn.close()
