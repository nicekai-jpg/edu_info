#!/usr/bin/env python3
"""
测试路线穷举器脚本
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edu_info.core.route_enumerator import RouteEnumerator
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("路线穷举器测试")
    logger.info("=" * 60)

    # 创建路线穷举器
    enumerator = RouteEnumerator()

    # 穷举所有路线
    logger.info("\n开始穷举路线...")
    routes = enumerator.enumerate_all("初三")

    # 统计结果
    logger.info("\n✅ 路线穷举完成！")
    logger.info(f"总路线数：{len(routes)}")

    # 按类型统计
    logger.info("\n按类型统计:")
    route_types = {}
    for route in routes:
        route_types[route.route_type] = route_types.get(route.route_type, 0) + 1

    for route_type, count in sorted(route_types.items(), key=lambda x: -x[1]):
        logger.info(f"  - {route_type}: {count} 条")

    # 按难度统计
    logger.info("\n按难度统计:")
    difficulties = {}
    for route in routes:
        difficulties[route.difficulty] = difficulties.get(route.difficulty, 0) + 1

    for difficulty, count in sorted(difficulties.items()):
        logger.info(f"  - {difficulty}: {count} 条")

    # 展示部分路线
    logger.info("\n部分路线示例:")
    for i, route in enumerate(routes[:10], 1):
        logger.info(f"  {i}. {route.route_name} ({route.difficulty})")

    # 保存到文件
    output_path = Path(__file__).parent.parent / "src" / "edu_info" / "data" / "sample_routes.json"
    enumerator.save_routes(str(output_path))

    logger.info(f"\n✅ 路线已保存到：{output_path}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
