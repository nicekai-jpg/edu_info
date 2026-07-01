"""数据库初始化脚本"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edu_info.database import create_database
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """主函数"""
    # 数据库路径
    db_path = Path(__file__).parent.parent / "data" / "duckdb" / "edu_planning.db"

    logger.info(f"创建数据库：{db_path}")

    # 创建数据库
    conn = create_database(str(db_path))

    # 验证表已创建
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
    ).fetchall()

    logger.info(f"成功创建 {len(tables)} 个表:")
    for table in tables:
        logger.info(f"  - {table[0]}")

    conn.close()
    logger.info("数据库初始化完成 ✅")


if __name__ == "__main__":
    main()
