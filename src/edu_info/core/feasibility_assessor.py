"""
可行性评估器

评估规划方案的可行性和录取概率
"""
from dataclasses import dataclass
from typing import Any

from edu_info.models.schemas import RouteMatch, Student, TargetUniversity
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class FeasibilityResult:
    """可行性评估结果"""
    overall_score: float  # 综合可行性评分 (0-100)
    risk_level: str  # 风险等级：低/中/高
    success_probability: float  # 成功概率 (0-100%)
    strengths: list[str]  # 优势
    weaknesses: list[str]  # 劣势
    recommendations: list[str]  # 建议


class FeasibilityAssessor:
    """可行性评估器"""

    # 风险等级阈值
    RISK_THRESHOLDS = {
        "低": 80,    # 80 分以上为低风险
        "中": 50,    # 50-80 分为中风险
        "高": 0,     # 50 分以下为高风险
    }

    def __init__(self):
        """初始化可行性评估器"""
        logger.info("可行性评估器初始化完成")

    def assess_route(self, student: Student, route_match: RouteMatch) -> FeasibilityResult:
        """
        评估路线的可行性

        Args:
            student: 学生信息
            route_match: 路线匹配结果

        Returns:
            可行性评估结果
        """
        # 计算综合评分
        overall_score = self._calculate_overall_score(student, route_match)

        # 确定风险等级
        risk_level = self._determine_risk_level(overall_score)

        # 计算成功概率
        success_probability = self._calculate_success_probability(student, route_match)

        # 分析优势和劣势
        strengths = self._analyze_strengths(student, route_match)
        weaknesses = self._analyze_weaknesses(student, route_match)

        # 生成建议
        recommendations = self._generate_recommendations(
            student, route_match, strengths, weaknesses
        )

        return FeasibilityResult(
            overall_score=overall_score,
            risk_level=risk_level,
            success_probability=success_probability,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
        )

    def assess_target(
        self,
        student: Student,
        target: TargetUniversity
    ) -> FeasibilityResult:
        """
        评估目标高校的可行性

        Args:
            student: 学生信息
            target: 目标高校

        Returns:
            可行性评估结果
        """
        # 计算录取概率
        probability = target.probability or 50.0

        # 确定风险等级
        if probability >= 80:
            risk_level = "低"
        elif probability >= 50:
            risk_level = "中"
        else:
            risk_level = "高"

        # 分析优势和劣势
        strengths = []
        weaknesses = []

        if student.total_score and target.min_score:
            score_diff = student.total_score - target.min_score
            if score_diff >= 10:
                strengths.append(f"分数优势明显（+{score_diff:.1f}分）")
            elif score_diff >= 0:
                strengths.append(f"分数略有优势（+{score_diff:.1f}分）")
            else:
                weaknesses.append(f"分数处劣势（-{abs(score_diff):.1f}分）")

        if student.ranking and target.min_rank:
            rank_diff = student.ranking - target.min_rank
            if rank_diff < 0:
                strengths.append(f"位次优势明显（领先{abs(rank_diff)}名）")
            else:
                weaknesses.append(f"位次处劣势（落后{rank_diff}名）")

        # 生成建议
        recommendations = self._generate_target_recommendations(
            student, target, probability, risk_level
        )

        return FeasibilityResult(
            overall_score=probability,
            risk_level=risk_level,
            success_probability=probability,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
        )

    def _calculate_overall_score(
        self,
        student: Student,
        route_match: RouteMatch
    ) -> float:
        """
        计算综合可行性评分

        Args:
            student: 学生信息
            route_match: 路线匹配结果

        Returns:
            综合评分 (0-100)
        """
        # 基础分：匹配度
        base_score = route_match.match_score

        # 调整因素
        adjustments = 0.0

        # 经济因素
        if route_match.economic_score < 50:
            adjustments -= 10.0  # 经济压力大，减分

        # 时间因素
        if route_match.time_score < 50:
            adjustments -= 5.0  # 时间紧张，减分

        # 计算最终评分
        final_score = base_score + adjustments

        return min(100.0, max(0.0, final_score))

    def _determine_risk_level(self, score: float) -> str:
        """
        根据评分确定风险等级

        Args:
            score: 综合评分

        Returns:
            风险等级
        """
        if score >= self.RISK_THRESHOLDS["低"]:
            return "低"
        elif score >= self.RISK_THRESHOLDS["中"]:
            return "中"
        else:
            return "高"

    def _calculate_success_probability(
        self,
        student: Student,
        route_match: RouteMatch
    ) -> float:
        """
        计算成功概率

        Args:
            student: 学生信息
            route_match: 路线匹配结果

        Returns:
            成功概率 (0-100%)
        """
        # 基础概率：匹配度
        base_probability = route_match.match_score

        # 根据难度调整
        difficulty_modifier = {
            "低": 1.1,
            "中等": 1.0,
            "高": 0.9,
            "极高": 0.8,
        }

        modifier = difficulty_modifier.get(route_match.route.difficulty, 1.0)

        # 计算最终概率
        probability = base_probability * modifier

        return min(100.0, max(0.0, probability))

    def _analyze_strengths(
        self,
        student: Student,
        route_match: RouteMatch
    ) -> list[str]:
        """
        分析优势

        Args:
            student: 学生信息
            route_match: 路线匹配结果

        Returns:
            优势列表
        """
        strengths = []

        # 兴趣匹配度高
        if route_match.interest_score >= 70:
            strengths.append("兴趣匹配度高，学习动力充足")

        # 能力匹配度高
        if route_match.ability_score >= 80:
            strengths.append("能力匹配度高，录取希望大")

        # 经济条件好
        if route_match.economic_score >= 80:
            strengths.append("经济条件充足，无后顾之忧")

        # 有特长
        if student.specialities and len(student.specialities) > 0:
            strengths.append("有特长或竞赛获奖，增加录取机会")

        return strengths

    def _analyze_weaknesses(
        self,
        student: Student,
        route_match: RouteMatch
    ) -> list[str]:
        """
        分析劣势

        Args:
            student: 学生信息
            route_match: 路线匹配结果

        Returns:
            劣势列表
        """
        weaknesses = []

        # 兴趣匹配度低
        if route_match.interest_score < 50:
            weaknesses.append("兴趣匹配度较低，可能影响学习积极性")

        # 能力匹配度低
        if route_match.ability_score < 60:
            weaknesses.append("能力匹配度较低，需要提升成绩")

        # 经济压力大
        if route_match.economic_score < 50:
            weaknesses.append("经济压力较大，建议考虑奖学金")

        # 时间紧张
        if route_match.time_score < 50:
            weaknesses.append("准备时间紧张，需要加快进度")

        return weaknesses

    def _generate_recommendations(
        self,
        student: Student,
        route_match: RouteMatch,
        strengths: list[str],
        weaknesses: list[str]
    ) -> list[str]:
        """
        生成建议

        Args:
            student: 学生信息
            route_match: 路线匹配结果
            strengths: 优势列表
            weaknesses: 劣势列表

        Returns:
            建议列表
        """
        recommendations = []

        # 根据风险等级生成建议
        risk_level = self._determine_risk_level(route_match.match_score)

        if risk_level == "低":
            recommendations.append("录取希望较大，建议作为重点考虑")
            recommendations.append("保持当前状态，巩固优势")
        elif risk_level == "中":
            recommendations.append("有一定录取希望，建议重点准备")
            recommendations.append("制定详细提升计划，增加录取把握")
        else:
            recommendations.append("难度较大，建议同时准备备选方案")
            recommendations.append("可以考虑相关专业的其他高校")

        # 根据劣势生成建议
        if "兴趣匹配度较低" in " ".join(weaknesses):
            recommendations.append("建议深入了解该方向，培养兴趣")

        if "能力匹配度较低" in " ".join(weaknesses):
            recommendations.append("建议制定学习计划，提升相关科目成绩")

        if "经济压力较大" in " ".join(weaknesses):
            recommendations.append("建议关注奖学金政策和助学贷款")

        return recommendations

    def _generate_target_recommendations(
        self,
        student: Student,
        target: TargetUniversity,
        probability: float,
        risk_level: str
    ) -> list[str]:
        """
        生成目标高校建议

        Args:
            student: 学生信息
            target: 目标高校
            probability: 录取概率
            risk_level: 风险等级

        Returns:
            建议列表
        """
        recommendations = []

        if risk_level == "低":
            recommendations.append("录取希望较大，建议作为保底/稳妥选择")
            recommendations.append("保持当前学习状态")
        elif risk_level == "中":
            recommendations.append("有一定录取希望，建议重点准备")
            recommendations.append("关注该校招生政策和特殊类型招生")
        else:
            recommendations.append("冲刺目标，需要付出较大努力")
            recommendations.append("建议同时准备备选方案")

        return recommendations

    def generate_feasibility_report(
        self,
        student: Student,
        route_matches: list[RouteMatch],
        targets: list[TargetUniversity]
    ) -> dict[str, Any]:
        """
        生成可行性评估报告

        Args:
            student: 学生信息
            route_matches: 路线匹配结果列表
            targets: 目标高校列表

        Returns:
            评估报告字典
        """
        # 评估所有路线
        route_assessments = []
        for match in route_matches[:5]:  # Top 5 路线
            assessment = self.assess_route(student, match)
            route_assessments.append({
                "route_name": match.route.route_name,
                "match_score": match.match_score,
                "feasibility_score": assessment.overall_score,
                "risk_level": assessment.risk_level,
                "success_probability": assessment.success_probability,
                "recommendations": assessment.recommendations,
            })

        # 评估所有目标
        target_assessments = []
        for target in targets:
            assessment = self.assess_target(student, target)
            target_assessments.append({
                "university_name": target.university.name,
                "target_type": target.target_type,
                "probability": assessment.success_probability,
                "risk_level": assessment.risk_level,
                "recommendations": assessment.recommendations,
            })

        # 综合评估
        overall_recommendation = self._generate_overall_recommendation(
            route_assessments, target_assessments
        )

        return {
            "student_name": student.name,
            "route_assessments": route_assessments,
            "target_assessments": target_assessments,
            "overall_recommendation": overall_recommendation,
        }

    def _generate_overall_recommendation(
        self,
        route_assessments: list[dict],
        target_assessments: list[dict]
    ) -> str:
        """
        生成综合建议

        Args:
            route_assessments: 路线评估列表
            target_assessments: 目标评估列表

        Returns:
            综合建议文本
        """
        # 计算平均成功率
        avg_route_prob = sum(a["success_probability"] for a in route_assessments) / len(route_assessments)
        avg_target_prob = sum(a["probability"] for a in target_assessments) / len(target_assessments)

        overall_prob = (avg_route_prob + avg_target_prob) / 2

        if overall_prob >= 70:
            return "整体可行性较高，建议按照规划方案执行，保持当前学习状态"
        elif overall_prob >= 50:
            return "整体可行性中等，建议重点关注匹配度高的路线，制定详细提升计划"
        else:
            return "整体可行性较低，建议调整目标或付出更大努力，同时准备备选方案"
