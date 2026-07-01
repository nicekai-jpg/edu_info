#!/usr/bin/env python3
"""
测试目标生成器
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edu_info.core.matching_engine import MatchingEngine
from edu_info.core.route_enumerator import RouteEnumerator
from edu_info.core.target_generator import ScoreRange, TargetGenerator
from edu_info.models.schemas import Student, University
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("目标生成器测试")
    logger.info("=" * 60)

    # 1. 准备数据
    logger.info("\n1. 准备测试数据...")

    # 创建示例学生
    student = Student(
        student_code="S2026003",
        name="张小明",
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
        interests=["编程", "机器人"],
        specialities=["信息学竞赛省二"],
        family_budget=80000.0,
        preferred_locations=["北京", "辽宁"],
    )

    # 创建示例高校
    universities = [
        University(
            id=1, name="清华大学", code="10003", location="北京",
            type="综合", is_985=True, is_211=True, is_double_first_class=True
        ),
        University(
            id=2, name="北京大学", code="10001", location="北京",
            type="综合", is_985=True, is_211=True, is_double_first_class=True
        ),
        University(
            id=3, name="东北大学", code="10145", location="辽宁沈阳",
            type="理工", is_985=True, is_211=True, is_double_first_class=True
        ),
        University(
            id=4, name="大连理工大学", code="10141", location="辽宁大连",
            type="理工", is_985=True, is_211=True, is_double_first_class=True
        ),
        University(
            id=5, name="辽宁大学", code="10140", location="辽宁沈阳",
            type="综合", is_985=False, is_211=True, is_double_first_class=True
        ),
    ]

    # 创建示例分数数据
    score_data = {
        1: ScoreRange(700, 710, 720, 50, 80, 100),    # 清华
        2: ScoreRange(690, 700, 710, 80, 120, 150),   # 北大
        3: ScoreRange(620, 640, 660, 2000, 3000, 4000),  # 东北大学
        4: ScoreRange(610, 630, 650, 3000, 4000, 5000),  # 大工
        5: ScoreRange(580, 600, 620, 8000, 10000, 12000), # 辽大
    }

    logger.info(f"学生：{student.name}，总分：{student.total_score}")
    logger.info(f"高校：{len(universities)} 所")

    # 2. 路线穷举
    logger.info("\n2. 生成路线...")
    enumerator = RouteEnumerator()
    routes = enumerator.enumerate_all("初三")
    logger.info(f"生成 {len(routes)} 条路线")

    # 3. 匹配路线
    logger.info("\n3. 匹配路线...")
    engine = MatchingEngine()
    matches = engine.match_all(student, routes)
    logger.info(f"匹配完成，最高分：{matches[0].match_score:.2f}")

    # 4. 生成目标
    logger.info("\n4. 生成三档目标...")
    generator = TargetGenerator()

    # 选择 Top 3 路线生成目标
    top_matches = matches[:3]
    for match in top_matches:
        logger.info(f"\n路线：{match.route.route_name} (匹配度：{match.match_score:.2f})")
        logger.info("-" * 60)

        high, medium, low = generator.generate_targets(
            student, match.route, universities, score_data
        )

        if high:
            logger.info(f"🎯 高目标（冲刺）: {len(high)} 所")
            for target in high:
                logger.info(f"  - {target.university.name} (概率：{target.probability:.1f}%)")

        if medium:
            logger.info(f"✅ 中目标（稳妥）: {len(medium)} 所")
            for target in medium:
                logger.info(f"  - {target.university.name} (概率：{target.probability:.1f}%)")

        if low:
            logger.info(f"📌 低目标（保底）: {len(low)} 所")
            for target in low:
                logger.info(f"  - {target.university.name} (概率：{target.probability:.1f}%)")

    logger.info("\n" + "=" * 60)
    logger.info("✅ 目标生成器测试完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
