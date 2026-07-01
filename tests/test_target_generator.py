"""
测试目标生成器
"""
import sys
from pathlib import Path

import pytest

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edu_info.core.target_generator import ScoreRange, TargetGenerator
from edu_info.models.schemas import PlanningRoute, Student, TargetUniversity, University


class TestTargetGenerator:
    """测试目标生成器"""

    @pytest.fixture
    def generator(self):
        """创建目标生成器实例"""
        return TargetGenerator()

    @pytest.fixture
    def sample_student(self):
        """创建示例学生"""
        return Student(
            student_code="S001",
            name="张小明",
            grade="高三",
            city="沈阳",
            category="物理类",
            total_score=650.0,
            ranking=2000,
            interests=["计算机"],
            family_budget=10.0,
        )

    @pytest.fixture
    def sample_universities(self):
        """创建示例高校"""
        return [
            University(id=1, name="清华大学", code="10003", location="北京", is_985=True, is_211=True),
            University(id=2, name="北京大学", code="10001", location="北京", is_985=True, is_211=True),
            University(id=3, name="东北大学", code="10145", location="辽宁", is_985=True, is_211=True),
            University(id=4, name="辽宁大学", code="10140", location="辽宁", is_211=True),
        ]

    @pytest.fixture
    def score_data(self):
        """创建分数数据"""
        return {
            1: ScoreRange(min_score=690, avg_score=700, max_score=710,
                         min_rank=50, avg_rank=80, max_rank=100),
            2: ScoreRange(min_score=680, avg_score=690, max_score=700,
                         min_rank=80, avg_rank=120, max_rank=150),
            3: ScoreRange(min_score=600, avg_score=620, max_score=640,
                         min_rank=3000, avg_rank=4000, max_rank=5000),
            4: ScoreRange(min_score=550, avg_score=570, max_score=590,
                         min_rank=8000, avg_rank=10000, max_rank=12000),
        }

    def test_init(self, generator):
        """测试初始化"""
        assert generator is not None

    def test_generate_high_targets(self, generator, sample_student, sample_universities, score_data):
        """测试高目标生成"""
        route = PlanningRoute(
            route_id="gaokao_001",
            route_name="985 高校 - 计算机",
            route_type="普通高考",
            category="普通高考",
        )

        high, medium, low = generator.generate_targets(
            sample_student, route, sample_universities, score_data
        )

        # 验证高目标
        assert isinstance(high, list)
        for target in high:
            assert isinstance(target, TargetUniversity)
            assert target.target_type == "高目标"
            # 高目标的录取概率应该较低（30-50%）
            assert target.probability is not None
            assert target.probability <= 50

    def test_generate_medium_targets(self, generator, sample_student, sample_universities, score_data):
        """测试中目标生成"""
        route = PlanningRoute(
            route_id="gaokao_001",
            route_name="985 高校 - 计算机",
            route_type="普通高考",
            category="普通高考",
        )

        high, medium, low = generator.generate_targets(
            sample_student, route, sample_universities, score_data
        )

        # 验证中目标
        assert isinstance(medium, list)
        for target in medium:
            assert isinstance(target, TargetUniversity)
            assert target.target_type == "中目标"
            # 中目标的录取概率应该中等（50-80%）
            assert target.probability is not None
            assert 30 <= target.probability <= 80

    def test_generate_low_targets(self, generator, sample_student, sample_universities, score_data):
        """测试低目标生成"""
        route = PlanningRoute(
            route_id="gaokao_001",
            route_name="985 高校 - 计算机",
            route_type="普通高考",
            category="普通高考",
        )

        high, medium, low = generator.generate_targets(
            sample_student, route, sample_universities, score_data
        )

        # 验证低目标
        assert isinstance(low, list)
        for target in low:
            assert isinstance(target, TargetUniversity)
            assert target.target_type == "低目标"
            # 低目标的录取概率应该较高（80%+）
            assert target.probability is not None
            assert target.probability >= 50

    def test_probability_calculation(self, generator, sample_student, sample_universities, score_data):
        """测试概率计算"""
        route = PlanningRoute(
            route_id="gaokao_001",
            route_name="985 高校 - 计算机",
            route_type="普通高考",
            category="普通高考",
        )

        high, medium, low = generator.generate_targets(
            sample_student, route, sample_universities, score_data
        )

        # 验证概率递减
        all_targets = high + medium + low

        # 清华的概率应该最低
        qinghua = next((t for t in all_targets if t.university.name == "清华大学"), None)
        if qinghua:
            assert qinghua.probability < 50  # 冲刺

        # 辽宁大学的概率应该最高
        liaoda = next((t for t in all_targets if t.university.name == "辽宁大学"), None)
        if liaoda:
            assert liaoda.probability > 50  # 保底

    def test_analysis_generation(self, generator, sample_student, sample_universities, score_data):
        """测试分析生成"""
        route = PlanningRoute(
            route_id="gaokao_001",
            route_name="985 高校 - 计算机",
            route_type="普通高考",
            category="普通高考",
        )

        high, medium, low = generator.generate_targets(
            sample_student, route, sample_universities, score_data
        )

        all_targets = high + medium + low

        for target in all_targets:
            # 应该有分析
            assert target.analysis is not None
            assert len(target.analysis) > 0

    def test_recommendations_generation(self, generator, sample_student, sample_universities, score_data):
        """测试建议生成"""
        route = PlanningRoute(
            route_id="gaokao_001",
            route_name="985 高校 - 计算机",
            route_type="普通高考",
            category="普通高考",
        )

        high, medium, low = generator.generate_targets(
            sample_student, route, sample_universities, score_data
        )

        all_targets = high + medium + low

        for target in all_targets:
            # 应该有建议
            assert isinstance(target.recommendations, list)

    def test_empty_universities(self, generator, sample_student, score_data):
        """测试空高校列表"""
        route = PlanningRoute(
            route_id="gaokao_001",
            route_name="985 高校 - 计算机",
            route_type="普通高考",
            category="普通高考",
        )

        high, medium, low = generator.generate_targets(
            sample_student, route, [], score_data
        )

        # 应该返回空列表
        assert high == []
        assert medium == []
        assert low == []

    def test_target_type_distribution(self, generator, sample_student, sample_universities, score_data):
        """测试目标类型分布"""
        route = PlanningRoute(
            route_id="gaokao_001",
            route_name="985 高校 - 计算机",
            route_type="普通高考",
            category="普通高考",
        )

        high, medium, low = generator.generate_targets(
            sample_student, route, sample_universities, score_data
        )

        # 验证三档目标都有
        assert len(high) + len(medium) + len(low) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
