import logging

import duckdb

logger = logging.getLogger(__name__)

class ScraperScheduler:
    """
    调度器与断点续爬系统，管理高校爬取进度。
    """
    def __init__(self, db_path: str | duckdb.DuckDBPyConnection):
        self.db_path = db_path
        self._conn: duckdb.DuckDBPyConnection | None = None
        self._is_external_conn = isinstance(db_path, duckdb.DuckDBPyConnection)

    def _get_conn(self):
        if self._is_external_conn:
            return self.db_path
        if self._conn is None:
            self._conn = duckdb.connect(self.db_path)
        return self._conn

    def init_checkpoints(self):
        """
        同步 universities 表中的所有高校 ID 到 scraping_checkpoints 表。
        """
        logger.info("正在初始化爬取检查点...")
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO scraping_checkpoints (
                    university_id, status, retry_count, created_at, updated_at
                )
                SELECT id, 'pending', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                FROM universities
                ON CONFLICT (university_id) DO NOTHING
            """)
            logger.info("检查点初始化完成。")
        except Exception as e:
            logger.error(f"初始化检查点失败: {e}")
            raise
        finally:
            if not self._is_external_conn and self._conn is not None:
                self._conn.close()
                self._conn = None

    def get_next_batch(self, limit: int = 5) -> list[tuple[int, str, str]]:
        """
        获取下一批待爬取的高校。
        优先级：985 > 211 > ID。
        仅选择状态为 'pending' 或 'failed' (且 retry_count < 3) 的高校。
        """
        query = """
            SELECT cp.university_id, u.name, u.code
            FROM scraping_checkpoints cp
            JOIN universities u ON cp.university_id = u.id
            WHERE (cp.status = 'pending' OR cp.status = 'failed')
              AND cp.retry_count < 3
            ORDER BY
                u.is_985 DESC,
                u.is_211 DESC,
                u.id ASC
            LIMIT ?
        """
        conn = self._get_conn()
        try:
            results = conn.execute(query, (limit,)).fetchall()
            return results
        except Exception as e:
            logger.error(f"获取下一批爬取任务失败: {e}")
            return []
        finally:
            if not self._is_external_conn and self._conn is not None:
                self._conn.close()
                self._conn = None

    def update_status(self, uni_id: int, status: str, error_msg: str | None = None):
        """
        更新爬取状态、错误信息及重试次数。
        """
        conn = self._get_conn()
        try:
            if status == 'failed':
                conn.execute("""
                    UPDATE scraping_checkpoints
                    SET status = ?,
                        error_msg = ?,
                        retry_count = retry_count + 1,
                        last_tried_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE university_id = ?
                """, (status, error_msg, uni_id))
            else:
                conn.execute("""
                    UPDATE scraping_checkpoints
                    SET status = ?,
                        error_msg = ?,
                        last_tried_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE university_id = ?
                """, (status, error_msg, uni_id))
            conn.commit()
            logger.info(f"高校 {uni_id} 的状态已更新为 {status}")
        except Exception as e:
            logger.error(f"更新高校 {uni_id} 状态失败: {e}")
            raise
        finally:
            if not self._is_external_conn and self._conn is not None:
                self._conn.close()
                self._conn = None
