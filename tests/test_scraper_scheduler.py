import duckdb
import pytest

from src.edu_info.database.schema import init_database
from src.edu_info.services.major_scraper.scheduler import ScraperScheduler


@pytest.fixture
def db_conn():
    conn = duckdb.connect(":memory:")
    init_database(conn)

    # Insert some universities for testing
    conn.execute("""
        INSERT INTO universities (id, name, is_985, is_211) VALUES
        (1, 'Uni 1 (985)', TRUE, TRUE),
        (2, 'Uni 2 (211)', FALSE, TRUE),
        (3, 'Uni 3 (Ordinary)', FALSE, FALSE),
        (4, 'Uni 4 (985)', TRUE, TRUE),
        (5, 'Uni 5 (211)', FALSE, TRUE)
    """)
    return conn

def test_init_checkpoints(db_conn):
    scheduler = ScraperScheduler(db_conn)
    scheduler.init_checkpoints()

    # Check if checkpoints are created
    count = db_conn.execute("SELECT COUNT(*) FROM scraping_checkpoints").fetchone()[0]
    assert count == 5

    # Run again, should not fail and count should still be 5
    scheduler.init_checkpoints()
    count = db_conn.execute("SELECT COUNT(*) FROM scraping_checkpoints").fetchone()[0]
    assert count == 5

def test_get_next_batch_priority(db_conn):
    scheduler = ScraperScheduler(db_conn)
    scheduler.init_checkpoints()

    # Priority: 985 first, then 211, then ID
    # Expected order: 1 (985), 4 (985), 2 (211), 5 (211), 3 (Ordinary)
    batch = scheduler.get_next_batch(limit=2)
    assert len(batch) == 2
    assert batch[0][0] == 1  # (id, name, code)
    assert batch[1][0] == 4

    # Update status to simulate progress
    for item in batch:
        uni_id = item[0]
        scheduler.update_status(uni_id, 'success')

    next_batch = scheduler.get_next_batch(limit=3)
    # Remaining pending: 2, 5, 3
    assert len(next_batch) == 3
    assert next_batch[0][0] == 2
    assert next_batch[1][0] == 5
    assert next_batch[2][0] == 3

def test_update_status_and_retry(db_conn):
    scheduler = ScraperScheduler(db_conn)
    scheduler.init_checkpoints()

    uni_id = 1
    # Test failed status incrementing retry count
    scheduler.update_status(uni_id, 'failed', 'Network error')

    checkpoint = db_conn.execute("SELECT status, error_msg, retry_count FROM scraping_checkpoints WHERE university_id = ?", (uni_id,)).fetchone()
    assert checkpoint[0] == 'failed'
    assert checkpoint[1] == 'Network error'
    assert checkpoint[2] == 1

    # Next batch should still include it because retry_count < 3
    batch = scheduler.get_next_batch(limit=10)
    batch_ids = [item[0] for item in batch]
    assert uni_id in batch_ids

    # Fail 2 more times
    scheduler.update_status(uni_id, 'failed', 'Error 2')
    scheduler.update_status(uni_id, 'failed', 'Error 3')

    checkpoint = db_conn.execute("SELECT retry_count FROM scraping_checkpoints WHERE university_id = ?", (uni_id,)).fetchone()
    assert checkpoint[0] == 3

    # Now it should NOT be in next batch
    batch = scheduler.get_next_batch(limit=10)
    batch_ids = [item[0] for item in batch]
    assert uni_id not in batch_ids

    # Success update should reset or just set status
    scheduler.update_status(uni_id, 'success')
    checkpoint = db_conn.execute("SELECT status FROM scraping_checkpoints WHERE university_id = ?", (uni_id,)).fetchone()
    assert checkpoint[0] == 'success'

    batch = scheduler.get_next_batch(limit=10)
    batch_ids = [item[0] for item in batch]
    assert uni_id not in batch_ids
