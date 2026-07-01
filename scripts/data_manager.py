#!/usr/bin/env python3
"""
数据管理中心

统一的爬虫和数据导入入口
支持批量爬取、数据验证、导入数据库
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
import json

from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


class DataManager:
    """数据管理中心"""

    def __init__(self):
        """初始化数据管理中心"""
        self.data_dir = Path("data/raw")
        self.db_path = Path("data/duckdb/edu_planning.db")

        logger.info("数据管理中心初始化完成")
        logger.info(f"  数据目录：{self.data_dir}")
        logger.info(f"  数据库：{self.db_path}")

    def crawl(self,
              year: int = 2025,
              universities: list[str] | None = None,
              output_dir: str | None = None):
        """
        爬取高校数据

        Args:
            year: 年份
            universities: 高校列表（None 则使用默认列表）
            output_dir: 输出目录
        """
        from scripts.crawl_2025_data import Data2025Crawler

        logger.info("=" * 60)
        logger.info(f"爬取 {year} 年高校数据")
        logger.info("=" * 60)

        # 创建爬虫
        if output_dir:
            crawler = Data2025Crawler(output_dir)
        else:
            crawler = Data2025Crawler()

        # 使用自定义高校列表或默认列表
        uni_list = universities or Data2025Crawler.PRIORITY_UNIVERSITIES

        # 开始爬取
        stats = crawler.crawl_batch(uni_list)

        # 保存数据
        crawler.save_data()

        # 输出统计
        logger.info("\n爬取统计:")
        logger.info(f"  高校：{stats['universities']} 所")
        logger.info(f"  专业：{stats['majors']} 个")
        logger.info(f"  分数：{stats['scores']} 条")
        logger.info(f"  错误：{stats['errors']} 个")

        return stats

    def import_data(self,
                    year: int = 2025,
                    data_dir: str | None = None):
        """
        导入数据到数据库

        Args:
            year: 年份
            data_dir: 数据目录
        """
        import importlib.util

        import duckdb

        # 动态加载 import_2025_data 模块
        spec = importlib.util.spec_from_file_location(
            "import_2025_data",
            Path(__file__).parent / "import_2025_data.py"
        )
        import_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(import_module)

        load_json = import_module.load_json
        import_universities = import_module.import_universities
        import_majors = import_module.import_majors
        import_scores = import_module.import_scores

        logger.info("=" * 60)
        logger.info(f"导入 {year} 年数据到数据库")
        logger.info("=" * 60)

        # 数据目录
        if data_dir:
            data_path = Path(data_dir)
        else:
            data_path = self.data_dir / str(year)

        # 检查文件
        uni_file = data_path / "universities_2025.json"
        major_file = data_path / "majors_2025.json"
        score_file = data_path / "scores_2025.json"

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
        logger.info(f"\n连接数据库：{self.db_path}")
        conn = duckdb.connect(str(self.db_path))

        try:
            # 导入数据
            import_universities(conn, universities)
            import_majors(conn, majors)
            import_scores(conn, scores)

            conn.commit()

            # 验证
            logger.info("\n数据验证:")
            result = conn.execute("SELECT COUNT(*) FROM universities").fetchone()[0]
            logger.info(f"  高校总数：{result}")

            result = conn.execute("SELECT COUNT(*) FROM majors").fetchone()[0]
            logger.info(f"  专业总数：{result}")

            result = conn.execute(
                f"SELECT COUNT(*) FROM admission_scores WHERE year={year}"
            ).fetchone()[0]
            logger.info(f"  {year}年分数：{result}")

            logger.info("\n✅ 数据导入完成！")

        except Exception as e:
            logger.error(f"导入失败：{e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def list_available_data(self):
        """列出所有可用的数据"""
        logger.info("\n可用数据:")
        logger.info("=" * 60)

        if not self.data_dir.exists():
            logger.info("  暂无数据")
            return

        for year_dir in sorted(self.data_dir.iterdir()):
            if year_dir.is_dir():
                year = year_dir.name
                uni_file = year_dir / "universities_2025.json"
                major_file = year_dir / "majors_2025.json"
                score_file = year_dir / "scores_2025.json"

                uni_count = 0
                major_count = 0
                score_count = 0

                if uni_file.exists():
                    with open(uni_file, encoding='utf-8') as f:
                        uni_count = len(json.load(f))

                if major_file.exists():
                    with open(major_file, encoding='utf-8') as f:
                        major_count = len(json.load(f))

                if score_file.exists():
                    with open(score_file, encoding='utf-8') as f:
                        score_count = len(json.load(f))

                logger.info(f"\n{year}年:")
                logger.info(f"  高校：{uni_count} 所")
                logger.info(f"  专业：{major_count} 个")
                logger.info(f"  分数：{score_count} 条")
                logger.info(f"  路径：{year_dir}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="数据管理中心 - 统一的爬虫和数据导入入口"
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # crawl 命令
    crawl_parser = subparsers.add_parser("crawl", help="爬取高校数据")
    crawl_parser.add_argument("--year", type=int, default=2025, help="年份")
    crawl_parser.add_argument(
        "--universities",
        type=str,
        nargs="+",
        help="高校列表（空格分隔）"
    )
    crawl_parser.add_argument(
        "--output",
        type=str,
        help="输出目录"
    )

    # import 命令
    import_parser = subparsers.add_parser("import", help="导入数据到数据库")
    import_parser.add_argument("--year", type=int, default=2025, help="年份")
    import_parser.add_argument("--data-dir", type=str, help="数据目录")

    # list 命令
    subparsers.add_parser("list", help="列出可用数据")

    args = parser.parse_args()

    # 创建数据管理中心
    dm = DataManager()

    # 执行命令
    if args.command == "crawl":
        dm.crawl(
            year=args.year,
            universities=args.universities,
            output_dir=args.output
        )
    elif args.command == "import":
        dm.import_data(
            year=args.year,
            data_dir=args.data_dir
        )
    elif args.command == "list":
        dm.list_available_data()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
