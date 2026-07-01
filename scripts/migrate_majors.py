
import duckdb

db_path = "data/duckdb/edu_planning.db"
conn = duckdb.connect(db_path)

try:
    conn.execute("BEGIN TRANSACTION;")

    # 1. Create the new table with the correct schema
    conn.execute("""
        CREATE TABLE majors_new (
            id INTEGER PRIMARY KEY,
            university_id INTEGER REFERENCES universities(id),
            name VARCHAR NOT NULL,
            code VARCHAR,
            category VARCHAR,
            degree VARCHAR,
            duration INTEGER DEFAULT 4,
            discipline_rank VARCHAR,
            is_national_key BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            major_class VARCHAR,
            is_ln_recruiting BOOLEAN DEFAULT FALSE,
            ln_code VARCHAR,
            UNIQUE(university_id, name)
        );
    """)

    # 2. Copy data from the old table
    # We should map the columns explicitly to be sure
    conn.execute("""
        INSERT INTO majors_new (
            id, university_id, name, code, category, degree, duration,
            discipline_rank, is_national_key, created_at, major_class,
            is_ln_recruiting, ln_code
        )
        SELECT
            id, university_id, name, code, category, degree, duration,
            discipline_rank, is_national_key, created_at, major_class,
            COALESCE(is_ln_recruiting, FALSE), ln_code
        FROM majors;
    """)

    # 3. Drop the old table.
    # Note: DuckDB doesn't seem to support DROP TABLE ... CASCADE for FKs in all versions,
    # but it might be necessary to drop the referencing FK first.

    # Let's check if we can just drop it.
    try:
        conn.execute("DROP TABLE majors;")
    except duckdb.ConstraintException:
        # If it fails due to FK, we drop the referencing FK first (if possible)
        # Actually in DuckDB, we might need to recreate the referencing table if it doesn't support ALTER TABLE DROP CONSTRAINT
        print("Dependency detected, dropping referencing constraints/tables if needed.")
        # admission_scores references majors
        # We'll have to recreate admission_scores too if we can't drop the FK.
        # But wait, DuckDB often doesn't enforce FKs unless enabled, but here they seem to be present.
        raise

    # 4. Rename the new table
    conn.execute("ALTER TABLE majors_new RENAME TO majors;")

    # 5. Re-add indexes
    conn.execute("CREATE INDEX idx_major_category ON majors(category);")
    conn.execute("CREATE INDEX idx_major_univ ON majors(university_id);")

    conn.execute("COMMIT;")
    print("Migration successful.")

except Exception as e:
    conn.execute("ROLLBACK;")
    print(f"Migration failed: {e}")
finally:
    conn.close()
