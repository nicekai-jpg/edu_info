#!/usr/bin/env python3
"""
数据管理工具

整合数据收集、导入、管理功能
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edu_info.services.university_crawler import UniversityCrawler
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


def collect_universities():
    """收集高校信息"""
    logger.info("=" * 60)
    logger.info("收集高校信息")
    logger.info("=" * 60)

    crawler = UniversityCrawler()
    universities = crawler.crawl_from_sun_gaokao()

    # 保存
    output_path = "src/edu_info/data/universities_985_211.json"
    crawler.save_to_json(universities, output_path)

    # 统计
    logger.info("\n收集完成:")
    logger.info(f"  - 985 高校：{len([u for u in universities if u.is_985])} 所")
    logger.info(f"  - 211 高校：{len([u for u in universities if u.is_211])} 所")

    return universities


def main():
    """主函数"""
    logger.info("\n" + "=" * 60)
    logger.info("升学规划系统 - 数据管理工具")
    logger.info("=" * 60)

    # 1. 收集高校信息
    collect_universities()

    logger.info("\n✅ 数据收集完成！")
    logger.info("\n下一步:")
    logger.info("  1. 收集分数线数据（手动整理或爬虫）")
    logger.info("  2. 导入数据到数据库")
    logger.info("  3. 测试规划引擎")

    logger.info("\n" + "=" * 60)


if __name__ == "__main__":
    main()
