import logging
import re
from typing import Any

import duckdb

logger = logging.getLogger(__name__)

def sync_to_db(db_path: str, university_id: int, majors_list: list[dict[str, Any]]):
    """
    清洗爬取到的专业数据并同步到数据库
    """
    if not majors_list:
        logger.warning(f"高校 {university_id} 的专业列表为空，跳过同步。")
        return

    conn = duckdb.connect(db_path)
    try:
        # 创建序列用于自增 ID
        conn.execute("CREATE SEQUENCE IF NOT EXISTS majors_id_seq;")

        insert_sql = """
        INSERT INTO majors (
            id, university_id, name, category, major_class, duration, degree
        ) VALUES (nextval('majors_id_seq'), ?, ?, ?, ?, ?, ?)
        ON CONFLICT (university_id, name) DO UPDATE SET
            category = excluded.category,
            major_class = excluded.major_class,
            duration = excluded.duration,
            degree = excluded.degree;
        """

        success = 0
        for major in majors_list:
            # 数据清洗
            name = str(major.get("name", "")).strip()
            if not name:
                continue

            category = str(major.get("category", "")).strip() if major.get("category") else None
            major_class = str(major.get("major_class", "")).strip() if major.get("major_class") else None
            degree = str(major.get("degree", "")).strip() if major.get("degree") else None

            # 处理学制，通常是数字，有时是 "四年" 等
            duration_raw = str(major.get("duration", "4")).strip()
            duration = 4
            match = re.search(r'\d+', duration_raw)
            if match:
                duration = int(match.group())

            conn.execute(insert_sql, (
                university_id,
                name,
                category,
                major_class,
                duration,
                degree
            ))
            success += 1

        conn.commit()
        logger.info(f"成功同步 {success} 个专业到高校 {university_id}")
    except Exception as e:
        logger.error(f"同步数据到高校 {university_id} 失败: {e}", exc_info=True)
        conn.rollback()
    finally:
        conn.close()
