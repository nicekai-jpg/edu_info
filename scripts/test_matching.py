#!/usr/bin/env python3
"""
测试匹配引擎
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edu_info.core.matching_engine import MatchingEngine
from edu_info.core.route_enumerator import RouteEnumerator
from edu_info.models.schemas import Student
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("匹配引擎测试")
    logger.info("=" * 60)

    # 1. 创建路线穷举器
    logger.info("\n1. 生成路线...")
    enumerator = RouteEnumerator()
    routes = enumerator.enumerate_all("初三")
    logger.info(f"生成 {len(routes)} 条路线")

    # 2. 创建示例学生
    logger.info("\n2. 创建示例学生...")
    student = Student(
        student_code="S2026003",
        name="王小明的测试",
        grade="初三",
        school="沈阳市实验中学",
        city="沈阳",
        category="物理类",
        total_score=680.0,
        ranking=200,
        chinese_score=110.0,
        math_score=125.0,
        english_score=120.0,
        other_scores={"物理": 92, "化学": 88},
        interests=["编程", "机器人", "数学"],
        specialities=["信息学竞赛省二"],
        family_budget=80000.0,
        preferred_locations=["北京", "辽宁"],
    )
    logger.info(f"学生：{student.name}，总分：{student.total_score}")

    # 3. 匹配引擎
    logger.info("\n3. 开始匹配...")
    engine = MatchingEngine()

    # 获取 Top 10 匹配
    top_matches = engine.get_top_matches(student, routes, top_n=10)

    # 4. 展示结果
    logger.info("\n✅ Top 10 匹配路线:")
    logger.info("-" * 60)

    for i, match in enumerate(top_matches, 1):
        logger.info(f"{i}. {match.route.route_name}")
        logger.info(f"   总分：{match.match_score:.2f}")
        logger.info(f"   兴趣：{match.interest_score:.1f} | 能力：{match.ability_score:.1f} | 经济：{match.economic_score:.1f}")

        if match.recommendations:
            logger.info(f"   建议：{match.recommendations[0]}")
        logger.info("")

    # 5. 统计
    logger.info("-" * 60)
    logger.info("匹配统计:")

    scores = [m.match_score for m in top_matches]
    logger.info(f"  最高分：{max(scores):.2f}")
    logger.info(f"  最低分：{min(scores):.2f}")
    logger.info(f"  平均分：{sum(scores)/len(scores):.2f}")

    # 按类型统计 Top 10
    route_types = {}
    for match in top_matches:
        route_types[match.route.route_type] = route_types.get(match.route.route_type, 0) + 1

    logger.info("\nTop 10 路线类型分布:")
    for route_type, count in sorted(route_types.items(), key=lambda x: -x[1]):
        logger.info(f"  - {route_type}: {count} 条")

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
