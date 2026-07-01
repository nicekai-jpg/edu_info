#!/usr/bin/env python3
"""
导入 2025 年爬取的数据到数据库
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json

import duckdb

from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


def load_json(file_path: Path) -> list[dict]:
    """加载 JSON 文件"""
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def import_universities(conn: duckdb.DuckDBPyConnection, universities: list[dict]):
    """导入高校数据"""
    logger.info(f"导入 {len(universities)} 所高校...")

    count = 0
    # 插入数据库（使用 INSERT OR IGNORE）
    for uni in universities:
        try:
            conn.execute("""
                INSERT INTO universities (
                    id, name, code, location, type,
                    is_985, is_211, is_double_first_class, project_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (code) DO NOTHING
            """, (
                uni["id"],
                uni["name"],
                uni["code"],
                uni["location"],
                uni["type"],
                uni["is_985"],
                uni["is_211"],
                uni["is_double_first_class"],
                uni.get("project_type"),
            ))
            count += 1
        except Exception as e:
            logger.debug(f"跳过已存在的高校 {uni['name']}: {e}")

    logger.info(f"✅ 高校导入成功 (新增 {count} 所)")


def import_majors(conn: duckdb.DuckDBPyConnection, majors: list[dict]):
    """导入专业数据"""
    logger.info(f"导入 {len(majors)} 个专业...")

    # 先获取高校 ID 映射（code -> id）
    result = conn.execute("SELECT id, code FROM universities").fetchall()
    code_to_id = {code: id for id, code in result}

    # 准备数据
    count = 0
    for major in majors:
        uni_code = major["university_id"]  # 爬虫中使用的是代码
        uni_id = code_to_id.get(str(uni_code))

        if not uni_id:
            logger.debug(f"跳过专业 {major['name']} - 高校不存在：{uni_code}")
            continue

        try:
            conn.execute("""
                INSERT INTO majors (
                    id, university_id, name, code, category, degree
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO NOTHING
            """, (
                major["id"],
                uni_id,
                major["name"],
                major.get("code"),
                major.get("category"),
                major.get("degree"),
            ))
            count += 1
        except Exception as e:
            logger.debug(f"跳过已存在专业 {major['name']}: {e}")

    logger.info(f"✅ 专业导入成功 (新增 {count} 个)")


def import_scores(conn: duckdb.DuckDBPyConnection, scores: list[dict]):
    """导入录取分数数据"""
    logger.info(f"导入 {len(scores)} 条录取分数...")

    # 确保序列存在
    conn.execute("CREATE SEQUENCE IF NOT EXISTS scores_id_seq;")

    # 准备数据
    data = []
    for score in scores:
        data.append((
            score["university_id"],
            score["major_id"],
            score["year"],
            score["province"],
            score["category"],
            score.get("min_score"),
            score.get("min_rank"),
            score.get("batch"),
        ))

    # 插入数据库
    conn.executemany("""
        INSERT OR IGNORE INTO admission_scores (
            id, university_id, major_id, year, province, category,
            min_score, min_rank, batch
        ) VALUES (nextval('scores_id_seq'), ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)

    logger.info("✅ 录取分数导入成功")


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("导入 2025 年数据到数据库")
    logger.info("=" * 60)

    # 数据目录
    data_dir = Path("data/raw/2025")
    db_path = Path("data/duckdb/edu_planning.db")

    # 检查数据文件
    uni_file = data_dir / "universities_2025.json"
    major_file = data_dir / "majors_2025.json"
    score_file = data_dir / "scores_2025.json"

    if not all([uni_file.exists(), major_file.exists(), score_file.exists()]):
        logger.error("数据文件不存在！")
        return

    # 加载数据
    logger.info("\n加载数据...")
    universities = load_json(uni_file)
    majors = load_json(major_file)
    scores = load_json(score_file)

    logger.info("加载完成:")
    logger.info(f"  高校：{len(universities)} 所")
    logger.info(f"  专业：{len(majors)} 个")
    logger.info(f"  分数：{len(scores)} 条")

    # 连接数据库
    logger.info(f"\n连接数据库：{db_path}")
    conn = duckdb.connect(str(db_path))

    try:
        # 导入数据
        import_universities(conn, universities)
        import_majors(conn, majors)
        import_scores(conn, scores)

        # 提交事务
        conn.commit()

        # 验证数据
        logger.info("\n验证数据...")

        # 统计高校
        result = conn.execute("SELECT COUNT(*) FROM universities").fetchone()[0]
        logger.info(f"  高校总数：{result}")

        # 统计专业
        result = conn.execute("SELECT COUNT(*) FROM majors").fetchone()[0]
        logger.info(f"  专业总数：{result}")

        # 统计分数
        result = conn.execute("SELECT COUNT(*) FROM admission_scores WHERE year=2025").fetchone()[0]
        logger.info(f"  2025 年分数：{result}")

        # 查询示例
        logger.info("\n2025 年录取分数示例（前 5 条）:")
        result = conn.execute("""
            SELECT u.name, m.name, a.min_score, a.min_rank
            FROM admission_scores a
            JOIN universities u ON a.university_id = u.id
            JOIN majors m ON a.major_id = m.id
            WHERE a.year = 2025
            ORDER BY a.min_score DESC
            LIMIT 5
        """).fetchall()

        for row in result:
            logger.info(f"  {row[0]} - {row[1]}: {row[2]}分 (位次：{row[3]})")

        logger.info("\n" + "=" * 60)
        logger.info("✅ 数据导入完成！")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"导入失败：{e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
