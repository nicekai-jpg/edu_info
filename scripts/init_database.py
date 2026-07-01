#!/usr/bin/env python3
"""
初始化数据库并导入示例数据
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edu_info.database import create_database
from edu_info.services.data_importer import import_sample_data
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("初始化数据库")
    logger.info("=" * 60)

    # 数据库路径
    db_path = Path(__file__).parent.parent / "data" / "duckdb" / "edu_planning.db"

    logger.info(f"数据库路径：{db_path}")

    # 创建数据库
    logger.info("\n创建数据库...")
    conn = create_database(str(db_path))
    logger.info("✅ 数据库创建成功")

    # 导入示例数据
    logger.info("\n导入示例数据...")
    import_sample_data(conn, "all")
    logger.info("✅ 示例数据导入成功")

    # 验证
    logger.info("\n验证数据...")
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
    ).fetchall()

    logger.info(f"数据表数量：{len(tables)}")
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
        logger.info(f"  - {table[0]}: {count} 条记录")

    conn.close()

    logger.info("\n" + "=" * 60)
    logger.info("✅ 数据库初始化完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
