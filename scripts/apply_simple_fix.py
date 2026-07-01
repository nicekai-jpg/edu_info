
import duckdb

db_path = "data/duckdb/edu_planning.db"
conn = duckdb.connect(db_path)

try:
    print("Applying is_ln_recruiting DEFAULT FALSE...")
    conn.execute("ALTER TABLE majors ALTER COLUMN is_ln_recruiting SET DEFAULT FALSE;")

    print("Updating existing NULL values in is_ln_recruiting to FALSE...")
    conn.execute("UPDATE majors SET is_ln_recruiting = FALSE WHERE is_ln_recruiting IS NULL;")

    print("Creating UNIQUE INDEX on (university_id, name)...")
    conn.execute("CREATE UNIQUE INDEX idx_majors_univ_name_unique ON majors(university_id, name);")

    print("Success.")
except Exception as e:
    print(f"Failed: {e}")
finally:
    conn.close()
