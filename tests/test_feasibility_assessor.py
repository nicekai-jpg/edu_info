"""
测试可行性评估器
"""
import sys
from pathlib import Path

import pytest

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edu_info.core.feasibility_assessor import FeasibilityAssessor
from edu_info.models.schemas import PlanningRoute, RouteMatch, Student, TargetUniversity, University


class TestFeasibilityAssessor:
    """测试可行性评估器"""

    @pytest.fixture
    def assessor(self):
        """创建可行性评估器实例"""
        return FeasibilityAssessor()

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
            specialities=["信息学竞赛省二"],
            family_budget=10.0,
        )

    @pytest.fixture
    def sample_route_match(self):
        """创建示例路线匹配"""
        route = PlanningRoute(
            route_id="keji_001",
            route_name="科技特长生 - 信息学",
            route_type="科技特长生",
            category="科技特长生",
            difficulty="高",
        )

        return RouteMatch(
            route=route,
            match_score=85.0,
            interest_score=90.0,
            ability_score=80.0,
            economic_score=85.0,
            time_score=75.0,
            region_score=70.0,
            recommendations=["建议重点准备"],
        )

    @pytest.fixture
    def sample_target(self):
        """创建示例目标高校"""
        university = University(
            id=1,
            name="清华大学",
            code="10003",
            location="北京",
            is_985=True,
            is_211=True,
        )

        return TargetUniversity(
            university=university,
            target_type="高目标",
            major="计算机科学与技术",
            min_score=690,
            min_rank=100,
            probability=30.0,
        )

    def test_init(self, assessor):
        """测试初始化"""
        assert assessor is not None

    def test_assess_route(self, assessor, sample_student, sample_route_match):
        """测试路线评估"""
        result = assessor.assess_route(sample_student, sample_route_match)

        # 验证评估结果
        assert 0 <= result.overall_score <= 100
        assert result.risk_level in ["低", "中", "高"]
        assert 0 <= result.success_probability <= 100
        assert isinstance(result.strengths, list)
        assert isinstance(result.weaknesses, list)
        assert isinstance(result.recommendations, list)

    def test_assess_target(self, assessor, sample_student, sample_target):
        """测试目标高校评估"""
        result = assessor.assess_target(sample_student, sample_target)

        # 验证评估结果
        assert result.overall_score == sample_target.probability
        assert result.risk_level in ["低", "中", "高"]
        assert result.success_probability == sample_target.probability
        assert isinstance(result.strengths, list)
        assert isinstance(result.weaknesses, list)
        assert isinstance(result.recommendations, list)

    def test_risk_level_determination(self, assessor, sample_student, sample_route_match):
        """测试风险等级判定"""
        # 高匹配度 - 应该低风险
        sample_route_match.match_score = 85.0
        result = assessor.assess_route(sample_student, sample_route_match)
        assert result.risk_level in ["低", "中"]

        # 中等匹配度 - 应该中风险
        sample_route_match.match_score = 60.0
        result = assessor.assess_route(sample_student, sample_route_match)
        assert result.risk_level in ["中", "高"]

        # 低匹配度 - 应该高风险
        sample_route_match.match_score = 40.0
        result = assessor.assess_route(sample_student, sample_route_match)
        assert result.risk_level == "高"

    def test_strength_analysis(self, assessor, sample_student, sample_route_match):
        """测试优势分析"""
        # 高兴趣匹配度
        sample_route_match.interest_score = 90.0
        result = assessor.assess_route(sample_student, sample_route_match)

        # 应该有兴趣相关的优势
        assert any("兴趣" in s for s in result.strengths)

    def test_weakness_analysis(self, assessor, sample_student, sample_route_match):
        """测试劣势分析"""
        # 低兴趣匹配度
        sample_route_match.interest_score = 30.0
        result = assessor.assess_route(sample_student, sample_route_match)

        # 应该有兴趣相关的劣势
        assert any("兴趣" in w for w in result.weaknesses)

    def test_recommendations_generation(self, assessor, sample_student, sample_route_match):
        """测试建议生成"""
        result = assessor.assess_route(sample_student, sample_route_match)

        # 应该有建议
        assert len(result.recommendations) > 0

        # 建议应该具体
        for rec in result.recommendations:
            assert len(rec) > 5

    def test_overall_score_calculation(self, assessor, sample_student, sample_route_match):
        """测试综合评分计算"""
        result = assessor.assess_route(sample_student, sample_route_match)

        # 综合评分应该考虑多个因素
        assert result.overall_score <= sample_route_match.match_score

        # 经济因素差应该降低评分
        sample_route_match.economic_score = 30.0
        result_low_econ = assessor.assess_route(sample_student, sample_route_match)
        assert result_low_econ.overall_score < result.overall_score

    def test_generate_feasibility_report(self, assessor, sample_student, sample_route_match, sample_target):
        """测试可行性报告生成"""
        route_matches = [sample_route_match]
        targets = [sample_target]

        report = assessor.generate_feasibility_report(sample_student, route_matches, targets)

        # 验证报告结构
        assert "student_name" in report
        assert "route_assessments" in report
        assert "target_assessments" in report
        assert "overall_recommendation" in report

        # 验证内容
        assert report["student_name"] == sample_student.name
        assert len(report["route_assessments"]) > 0
        assert len(report["target_assessments"]) > 0

    def test_target_probability_based_risk(self, assessor, sample_student):
        """测试基于录取概率的风险评估"""
        # 高概率 - 低风险
        high_prob_target = TargetUniversity(
            university=University(id=1, name="A 大学", code="001", location="辽宁"),
            target_type="低目标",
            probability=90.0,
        )
        result = assessor.assess_target(sample_student, high_prob_target)
        assert result.risk_level == "低"

        # 中概率 - 中风险
        mid_prob_target = TargetUniversity(
            university=University(id=2, name="B 大学", code="002", location="北京"),
            target_type="中目标",
            probability=60.0,
        )
        result = assessor.assess_target(sample_student, mid_prob_target)
        assert result.risk_level == "中"

        # 低概率 - 高风险
        low_prob_target = TargetUniversity(
            university=University(id=3, name="C 大学", code="003", location="上海"),
            target_type="高目标",
            probability=20.0,
        )
        result = assessor.assess_target(sample_student, low_prob_target)
        assert result.risk_level == "高"

    def test_score_comparison(self, assessor, sample_student, sample_target):
        """测试分数对比分析"""
        # 学生分数高于目标 - 优势
        sample_student.total_score = 700.0
        result = assessor.assess_target(sample_student, sample_target)
        assert any("分数" in s for s in result.strengths)

        # 学生分数低于目标 - 劣势
        sample_student.total_score = 600.0
        result = assessor.assess_target(sample_student, sample_target)
        assert any("分数" in w for w in result.weaknesses)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
