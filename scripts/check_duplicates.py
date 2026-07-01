
import duckdb

db_path = "data/duckdb/edu_planning.db"
conn = duckdb.connect(db_path)
try:
    print("--- Checking for duplicates (university_id, name) ---")
    res = conn.execute("""
        SELECT university_id, name, COUNT(*)
        FROM majors
        GROUP BY university_id, name
        HAVING COUNT(*) > 1;
    """).fetchall()
    if res:
        print("Duplicates found:")
        for row in res:
            print(row)
    else:
        print("No duplicates found.")
finally:
    conn.close()
