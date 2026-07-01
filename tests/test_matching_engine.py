"""
测试匹配引擎
"""
import sys
from pathlib import Path

import pytest

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edu_info.core.matching_engine import MatchingEngine
from edu_info.models.schemas import PlanningRoute, RouteMatch, Student


class TestMatchingEngine:
    """测试匹配引擎"""

    @pytest.fixture
    def engine(self):
        """创建匹配引擎实例"""
        return MatchingEngine()

    @pytest.fixture
    def sample_student(self):
        """创建示例学生"""
        return Student(
            student_code="S001",
            name="张小明",
            grade="初三",
            city="沈阳",
            category="物理类",
            total_score=680.0,
            ranking=1000,
            interests=["编程", "机器人", "数学"],
            specialities=["信息学竞赛省二"],
            family_budget=10.0,
            preferred_locations=["北京", "上海"],
        )

    @pytest.fixture
    def sample_routes(self):
        """创建示例路线"""
        return [
            PlanningRoute(
                route_id="keji_001",
                route_name="科技特长生 - 信息学",
                route_type="科技特长生",
                category="科技特长生",
                description="通过信息学竞赛特长生招生",
                difficulty="高",
                target_university_types=["985", "211"],
                target_major_types=["计算机类", "电子信息类"],
            ),
            PlanningRoute(
                route_id="gaokao_001",
                route_name="985 高校 - 计算机专业",
                route_type="普通高考",
                category="普通高考",
                description="通过普通高考考入 985 高校计算机专业",
                difficulty="高",
                target_university_types=["985"],
                target_major_types=["计算机类"],
            ),
            PlanningRoute(
                route_id="qiangji_001",
                route_name="强基计划 - 数学",
                route_type="强基计划",
                category="强基计划",
                description="通过强基计划考入数学专业",
                difficulty="极高",
                target_university_types=["985"],
                target_major_types=["数学类"],
            ),
        ]

    def test_init(self, engine):
        """测试初始化"""
        assert engine is not None

    def test_match_single(self, engine, sample_student, sample_routes):
        """测试单条路线匹配"""
        route = sample_routes[0]
        match = engine.match_single(sample_student, route)

        assert isinstance(match, RouteMatch)
        assert match.route == route
        assert 0 <= match.match_score <= 100
        assert 0 <= match.interest_score <= 100
        assert 0 <= match.ability_score <= 100
        assert 0 <= match.economic_score <= 100

    def test_match_all(self, engine, sample_student, sample_routes):
        """测试批量匹配"""
        matches = engine.match_all(sample_student, sample_routes)

        assert isinstance(matches, list)
        assert len(matches) == len(sample_routes)

        # 验证匹配度排序（降序）
        for i in range(len(matches) - 1):
            assert matches[i].match_score >= matches[i + 1].match_score

    def test_interest_matching(self, engine, sample_student, sample_routes):
        """测试兴趣匹配"""
        # 科技特长生应该兴趣匹配度更高
        matches = engine.match_all(sample_student, sample_routes)

        keji_match = next(m for m in matches if m.route.route_type == "科技特长生")
        gaokao_match = next(m for m in matches if m.route.route_type == "普通高考")

        # 科技特长生的兴趣匹配度应该不低于普通高考
        # （因为学生有兴趣是"编程"和"机器人"，与科技特长生更相关）
        assert keji_match.interest_score >= gaokao_match.interest_score

    def test_ability_matching(self, engine, sample_student, sample_routes):
        """测试能力匹配"""
        matches = engine.match_all(sample_student, sample_routes)

        for match in matches:
            # 能力匹配度应该在合理范围内
            assert 0 <= match.ability_score <= 100

            # 高难度路线的能力匹配度应该较低
            if match.route.difficulty == "极高":
                assert match.ability_score < 80

    def test_economic_matching(self, engine, sample_student, sample_routes):
        """测试经济匹配"""
        matches = engine.match_all(sample_student, sample_routes)

        for match in matches:
            # 经济匹配度应该在合理范围内
            assert 0 <= match.economic_score <= 100

    def test_recommendations_generation(self, engine, sample_student, sample_routes):
        """测试建议生成"""
        matches = engine.match_all(sample_student, sample_routes)

        for match in matches:
            # 应该有建议
            assert isinstance(match.recommendations, list)
            # 建议数量应该合理
            assert len(match.recommendations) >= 1

    def test_weights(self, engine, sample_student, sample_routes):
        """测试权重配置"""
        # 默认权重
        assert engine.weights["interest"] == 0.4
        assert engine.weights["ability"] == 0.25
        assert engine.weights["economic"] == 0.2
        assert engine.weights["time"] == 0.1
        assert engine.weights["region"] == 0.05

        # 权重总和应该为 1
        total_weight = sum(engine.weights.values())
        assert abs(total_weight - 1.0) < 0.01

    def test_match_score_calculation(self, engine, sample_student, sample_routes):
        """测试匹配度计算"""
        matches = engine.match_all(sample_student, sample_routes)

        for match in matches:
            # 验证总分计算
            expected_score = (
                match.interest_score * 0.4 +
                match.ability_score * 0.25 +
                match.economic_score * 0.2 +
                match.time_score * 0.1 +
                match.region_score * 0.05
            )

            # 允许小误差
            assert abs(match.match_score - expected_score) < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
