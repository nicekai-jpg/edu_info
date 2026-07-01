#!/usr/bin/env python3
"""
正确的数据导入流程

严格按照高校代码（而非自增 ID）作为主键
确保数据一致性和外键约束
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json

import duckdb

from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


def load_json(file_path: Path) -> list[dict]:
    """加载 JSON 文件"""
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def validate_university_code(code: str) -> bool:
    """验证高校代码格式"""
    # 高校代码应该是 5 位数字
    return len(code) == 5 and code.isdigit()


def import_universities_with_codes(
    conn: duckdb.DuckDBPyConnection,
    universities: list[dict]
) -> tuple[int, int]:
    """
    导入高校数据（使用代码作为主键）

    Returns:
        (成功数量，失败数量)
    """
    logger.info(f"导入 {len(universities)} 所高校（使用代码作为主键）...")

    success = 0
    failed = 0

    for uni in universities:
        try:
            # 验证代码
            if not validate_university_code(uni["code"]):
                logger.warning(f"高校代码格式错误：{uni['name']} - {uni['code']}")
                failed += 1
                continue

            # 插入或更新
            conn.execute("""
                INSERT INTO universities (
                    id, code, name, location, type,
                    is_985, is_211, is_double_first_class, project_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET
                    code = excluded.code,
                    name = excluded.name,
                    location = excluded.location,
                    type = excluded.type,
                    is_985 = excluded.is_985,
                    is_211 = excluded.is_211,
                    is_double_first_class = excluded.is_double_first_class,
                    project_type = excluded.project_type
            """, (
                int(uni["code"]),  # 使用代码作为 ID
                uni["code"],
                uni["name"],
                uni["location"],
                uni["type"],
                uni["is_985"],
                uni["is_211"],
                uni["is_double_first_class"],
                uni.get("project_type"),
            ))
            success += 1

        except Exception as e:
            logger.error(f"导入高校失败 {uni['name']}: {e}")
            failed += 1

    logger.info(f"高校导入完成：成功 {success} 所，失败 {failed} 所")
    return success, failed


def import_majors_with_mapping(
    conn: duckdb.DuckDBPyConnection,
    majors: list[dict]
) -> tuple[int, int]:
    """
    导入专业数据（使用代码映射）

    专业 ID 生成规则：university_code * 1000 + 序号
    """
    logger.info(f"导入 {len(majors)} 个专业...")

    # 先建立 university_code -> university_id 映射
    result = conn.execute("SELECT id, code FROM universities").fetchall()
    code_to_id = {code: int(id) for id, code in result}

    logger.info(f"已加载 {len(code_to_id)} 所高校的 ID 映射")

    success = 0
    failed = 0

    for major in majors:
        try:
            uni_code = str(major["university_id"])  # 爬虫中存的是代码

            # 查找对应的数据库 ID
            if uni_code not in code_to_id:
                logger.warning(f"专业 {major['name']} 的高校不存在：{uni_code}")
                failed += 1
                continue

            uni_db_id = code_to_id[uni_code]

            # 生成专业 ID（如果还没有）
            major_id = major.get("id")
            if not major_id:
                # 使用规则生成：uni_db_id * 1000 + 序号
                major_id = uni_db_id * 1000 + (success % 1000 + 1)

            # 插入专业
            conn.execute("""
                INSERT INTO majors (
                    id, university_id, name, code, category, degree
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET
                    university_id = excluded.university_id,
                    name = excluded.name,
                    code = excluded.code,
                    category = excluded.category,
                    degree = excluded.degree
            """, (
                major_id,
                uni_db_id,  # 使用数据库 ID（外键）
                major["name"],
                major.get("code", ""),
                major.get("category", ""),
                major.get("degree", "本科"),
            ))
            success += 1

        except Exception as e:
            logger.error(f"导入专业失败 {major.get('name', '未知')}: {e}")
            failed += 1

    logger.info(f"专业导入完成：成功 {success} 个，失败 {failed} 个")
    return success, failed


def import_scores_with_mapping(
    conn: duckdb.DuckDBPyConnection,
    scores: list[dict]
) -> tuple[int, int]:
    """
    导入录取分数（使用代码映射）
    """
    logger.info(f"导入 {len(scores)} 条录取分数...")

    # 建立映射表
    result = conn.execute("SELECT id, code FROM universities").fetchall()
    uni_code_to_id = {code: int(id) for id, code in result}

    result = conn.execute("SELECT id, university_id FROM majors").fetchall()
    major_id_map = {id: id for id, _ in result}  # major_id -> major_id

    logger.info(f"已加载 {len(uni_code_to_id)} 所高校，{len(major_id_map)} 个专业的映射")

    success = 0
    failed = 0
    skipped = 0

    for score in scores:
        try:
            uni_code = str(score["university_id"])
            score["major_id"]

            # 查找高校 ID
            if uni_code not in uni_code_to_id:
                logger.debug(f"分数对应高校不存在：{uni_code}")
                skipped += 1
                continue

            uni_db_id = uni_code_to_id[uni_code]

            # 查找或生成专业 ID
            # 专业 ID 规则：university_db_id * 1000 + 序号
            uni_db_id * 1000

            # 尝试查找已存在的专业
            major_db_id = None
            result = conn.execute("""
                SELECT id FROM majors
                WHERE university_id = ? AND name = ?
            """, (uni_db_id, score.get("major_name", ""))).fetchone()

            if result:
                major_db_id = result[0]
            else:
                # 专业不存在，跳过（应该先导入专业）
                logger.debug(f"专业不存在：{uni_code} - {score.get('major_name', '')}")
                skipped += 1
                continue

            # 插入分数
            conn.execute("""
                INSERT INTO admission_scores (
                    university_id, major_id, year, province, category,
                    min_score, min_rank, batch
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (university_id, major_id, year, province, category)
                DO NOTHING
            """, (
                uni_db_id,
                major_db_id,
                score["year"],
                score.get("province", "辽宁"),
                score.get("category", "物理类"),
                score.get("min_score"),
                score.get("min_rank"),
                score.get("batch", "本科批"),
            ))
            success += 1

        except Exception as e:
            logger.error(f"导入分数失败：{e}")
            failed += 1

    logger.info(f"分数导入完成：成功 {success} 条，失败 {failed} 条，跳过 {skipped} 条")
    return success, failed


def verify_import(conn: duckdb.DuckDBPyConnection):
    """验证导入结果"""
    logger.info("\n=== 数据验证 ===")

    # 统计
    uni_count = conn.execute("SELECT COUNT(*) FROM universities").fetchone()[0]
    major_count = conn.execute("SELECT COUNT(*) FROM majors").fetchone()[0]
    score_count = conn.execute("SELECT COUNT(*) FROM admission_scores WHERE year=2025").fetchone()[0]

    logger.info(f"高校总数：{uni_count}")
    logger.info(f"专业总数：{major_count}")
    logger.info(f"2025 年分数：{score_count}")

    # 示例数据
    logger.info("\n2025 年录取分数示例（前 3 条）:")
    result = conn.execute("""
        SELECT u.name, m.name, a.min_score, a.min_rank
        FROM admission_scores a
        JOIN universities u ON a.university_id = u.id
        JOIN majors m ON a.major_id = m.id
        WHERE a.year = 2025
        ORDER BY a.min_score DESC
        LIMIT 3
    """).fetchall()

    for row in result:
        logger.info(f"  {row[0]} - {row[1]}: {row[2]}分 (位次：{row[3]})")


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("正确的数据导入流程")
    logger.info("=" * 60)

    # 数据目录
    data_dir = Path("data/raw/2025")
    db_path = Path("data/duckdb/edu_planning.db")

    # 检查文件
    uni_file = data_dir / "universities_2025.json"
    major_file = data_dir / "majors_2025.json"
    score_file = data_dir / "scores_2025.json"

    if not all([uni_file.exists(), major_file.exists(), score_file.exists()]):
        logger.error("数据文件不完整！")
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
        # 1. 导入高校（使用代码作为 ID）
        import_universities_with_codes(conn, universities)

        # 2. 导入专业（使用 ID 映射）
        import_majors_with_mapping(conn, majors)

        # 3. 导入分数（使用 ID 映射）
        import_scores_with_mapping(conn, scores)

        # 提交
        conn.commit()

        # 验证
        verify_import(conn)

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
