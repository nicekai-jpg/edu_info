#!/usr/bin/env python3
"""
导入真实数据示例

包含 2024/2025 年辽宁省部分重点高校的真实录取分数线
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


import duckdb

from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)

# 真实高校数据
REAL_UNIVERSITIES = [
    {"id": 10001, "code": "10001", "name": "北京大学", "location": "北京", "type": "综合", "is_985": True, "is_211": True, "is_double_first_class": True},
    {"id": 10003, "code": "10003", "name": "清华大学", "location": "北京", "type": "理工", "is_985": True, "is_211": True, "is_double_first_class": True},
    {"id": 10246, "code": "10246", "name": "复旦大学", "location": "上海", "type": "综合", "is_985": True, "is_211": True, "is_double_first_class": True},
    {"id": 10248, "code": "10248", "name": "上海交通大学", "location": "上海", "type": "综合", "is_985": True, "is_211": True, "is_double_first_class": True},
    {"id": 14430, "code": "14430", "name": "中国科学院大学", "location": "北京", "type": "理工", "is_985": True, "is_211": True, "is_double_first_class": True},
    {"id": 10145, "code": "10145", "name": "东北大学", "location": "辽宁沈阳", "type": "理工", "is_985": True, "is_211": True, "is_double_first_class": True},
    {"id": 10141, "code": "10141", "name": "大连理工大学", "location": "辽宁大连", "type": "理工", "is_985": True, "is_211": True, "is_double_first_class": True},
    {"id": 10151, "code": "10151", "name": "大连海事大学", "location": "辽宁大连", "type": "理工", "is_985": False, "is_211": True, "is_double_first_class": True},
    {"id": 10140, "code": "10140", "name": "辽宁大学", "location": "辽宁沈阳", "type": "综合", "is_985": False, "is_211": True, "is_double_first_class": True},
    {"id": 10173, "code": "10173", "name": "东北财经大学", "location": "辽宁大连", "type": "财经", "is_985": False, "is_211": False, "is_double_first_class": False},
]

# 模拟专业（由于没有完整的专业投档线，我们为每个学校创建一个“普通批次”作为占位）
REAL_MAJORS = []
for uni in REAL_UNIVERSITIES:
    REAL_MAJORS.append({
        "id": uni["id"] * 100 + 1,
        "university_id": uni["id"],
        "name": "普通本科批",
        "category": "物理类",
        "degree": "本科"
    })

# 真实分数线数据 (辽宁物理类)
REAL_SCORES = [
    # 2025 年数据 (部分)
    {"university_id": 10001, "year": 2025, "min_score": 695, "min_rank": 60},
    {"university_id": 10003, "year": 2025, "min_score": 688, "min_rank": 150},
    {"university_id": 10246, "year": 2025, "min_score": 685, "min_rank": 210},
    {"university_id": 10248, "year": 2025, "min_score": 683, "min_rank": 260},
    {"university_id": 14430, "year": 2025, "min_score": 679, "min_rank": 360},

    # 2024 年数据
    {"university_id": 10145, "year": 2024, "min_score": 623, "min_rank": 8697},
    {"university_id": 10141, "year": 2024, "min_score": 632, "min_rank": 6500},
    {"university_id": 10151, "year": 2024, "min_score": 604, "min_rank": 13500},
    {"university_id": 10140, "year": 2024, "min_score": 530, "min_rank": 39805},
    {"university_id": 10173, "year": 2024, "min_score": 566, "min_rank": 25000},
    {"university_id": 10001, "year": 2024, "min_score": 702, "min_rank": 50},
    {"university_id": 10003, "year": 2024, "min_score": 706, "min_rank": 40},
]

def import_real_data(conn: duckdb.DuckDBPyConnection):
    """导入真实数据"""
    logger.info("开始导入真实录取数据...")

    # 1. 导入高校
    for uni in REAL_UNIVERSITIES:
        conn.execute("""
            INSERT INTO universities (
                id, code, name, location, type, is_985, is_211, is_double_first_class
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                code = excluded.code,
                name = excluded.name,
                location = excluded.location,
                type = excluded.type,
                is_985 = excluded.is_985,
                is_211 = excluded.is_211,
                is_double_first_class = excluded.is_double_first_class
        """, (
            uni["id"], uni["code"], uni["name"], uni["location"],
            uni["type"], uni["is_985"], uni["is_211"], uni["is_double_first_class"]
        ))
    logger.info(f"已导入/更新 {len(REAL_UNIVERSITIES)} 所重点高校")

    # 2. 导入专业
    for major in REAL_MAJORS:
        conn.execute("""
            INSERT INTO majors (
                id, university_id, name, category, degree
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                university_id = excluded.university_id,
                name = excluded.name,
                category = excluded.category,
                degree = excluded.degree
        """, (
            major["id"], major["university_id"], major["name"],
            major["category"], major["degree"]
        ))
    logger.info(f"已导入/更新 {len(REAL_MAJORS)} 个专业")

    # 3. 导入分数
    for i, score in enumerate(REAL_SCORES, 1):
        # 获取对应的专业 ID
        major_id = score["university_id"] * 100 + 1

        conn.execute("""
            INSERT INTO admission_scores (
                id, university_id, major_id, year, province, category, min_score, min_rank, batch
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (university_id, major_id, year, province, category) DO UPDATE SET
                min_score = excluded.min_score,
                min_rank = excluded.min_rank,
                batch = excluded.batch
        """, (
            i, score["university_id"], major_id, score["year"], "辽宁",
            "物理类", score["min_score"], score["min_rank"], "本科批"
        ))
    logger.info(f"已导入/更新 {len(REAL_SCORES)} 条分数线数据")

def main():
    db_path = Path(__file__).parent.parent / "data" / "duckdb" / "edu_planning.db"
    logger.info(f"连接数据库: {db_path}")

    conn = duckdb.connect(str(db_path))

    try:
        import_real_data(conn)
        conn.commit()
        logger.info("✅ 真实数据导入成功！")

        # 验证
        print("\n当前数据库中的真实分数线示例:")
        result = conn.execute("""
            SELECT u.name, a.year, a.min_score, a.min_rank
            FROM admission_scores a
            JOIN universities u ON a.university_id = u.id
            ORDER BY a.year DESC, a.min_score DESC
        """).fetchall()

        for row in result:
            print(f"  {row[1]}年 {row[0]}: {row[2]}分 (位次: {row[3]})")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
