"""
匹配理由生成器

根据学生的五维匹配分数，生成详细的匹配理由和行动建议
"""
from typing import Any

from edu_info.models.schemas import RouteMatch, Student
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


class MatchingReasonGenerator:
    """匹配理由生成器"""

    def __init__(self):
        """初始化生成器"""
        self.dimension_weights = {
            "interest": 0.40,    # 兴趣 40%
            "ability": 0.25,     # 能力 25%
            "economic": 0.20,    # 经济 20%
            "time": 0.10,        # 时间 10%
            "region": 0.05       # 地域 5%
        }

    def generate_reasons(
        self,
        student: Student,
        route_match: RouteMatch
    ) -> dict[str, Any]:
        """
        生成匹配理由

        Args:
            student: 学生信息
            route_match: 路线匹配结果

        Returns:
            包含各维度匹配理由的字典
        """
        reasons: dict[str, Any] = {
            "interest": self._generate_interest_reason(student, route_match),
            "ability": self._generate_ability_reason(student, route_match),
            "economic": self._generate_economic_reason(student, route_match),
            "time": self._generate_time_reason(student, route_match),
            "region": self._generate_region_reason(student, route_match),
        }

        # 生成综合评价
        reasons["summary"] = self._generate_summary_reason(student, route_match, reasons)

        # 生成行动建议
        reasons["action_items"] = self._generate_action_items(student, route_match, reasons)

        return reasons

    def _generate_interest_reason(
        self,
        student: Student,
        route_match: RouteMatch
    ) -> dict[str, Any]:
        """生成兴趣匹配理由"""
        score = route_match.interest_score
        interests = student.interests or []
        specialities = student.specialities or []

        # 分析兴趣匹配点
        interest_points = []
        if interests:
            interest_points.append(f"你的兴趣方向是【{', '.join(interests[:3])}】")
        if specialities:
            interest_points.append(f"特长包括【{', '.join(specialities[:2])}】")

        # 生成评价
        if score >= 80:
            evaluation = "与推荐赛道高度契合"
            suggestion = "继续保持并深化这些兴趣，它们将成为你升学的重要优势"
        elif score >= 60:
            evaluation = "与推荐赛道有一定匹配度"
            suggestion = "建议进一步培养相关兴趣，参加相关活动或竞赛"
        else:
            evaluation = "与推荐赛道匹配度较低"
            suggestion = "建议重新思考兴趣方向，或考虑其他更适合的赛道"

        return {
            "score": score,
            "weight": self.dimension_weights["interest"],
            "points": interest_points,
            "evaluation": evaluation,
            "suggestion": suggestion,
            "level": "excellent" if score >= 80 else "good" if score >= 60 else "needs_improvement"
        }

    def _generate_ability_reason(
        self,
        student: Student,
        route_match: RouteMatch
    ) -> dict[str, Any]:
        """生成能力匹配理由"""
        score = route_match.ability_score
        total_score = student.total_score or 0
        ranking = student.ranking or 0

        # 计算百分比
        score_percent = (total_score / 750 * 100) if total_score > 0 else 0

        # 识别优势科目
        advantage_subjects = []
        if student.chinese_score and student.chinese_score >= 120:
            advantage_subjects.append("语文")
        if student.math_score and student.math_score >= 130:
            advantage_subjects.append("数学")
        if student.english_score and student.english_score >= 125:
            advantage_subjects.append("英语")

        # 生成评价
        if score >= 80:
            evaluation = f"具备冲击重点高校的学术能力（前{score_percent:.1f}%）"
            suggestion = "保持优势科目的同时，继续提升弱势科目"
        elif score >= 60:
            evaluation = f"具备良好的学习基础（前{score_percent:.1f}%）"
            suggestion = "建议重点提升总分排名，争取进入更高层次高校"
        else:
            evaluation = f"学术能力有待提升（前{score_percent:.1f}%）"
            suggestion = "制定详细的学习计划，重点突破弱势科目"

        return {
            "score": score,
            "weight": self.dimension_weights["ability"],
            "total_score": total_score,
            "ranking": ranking,
            "score_percent": score_percent,
            "advantage_subjects": advantage_subjects,
            "evaluation": evaluation,
            "suggestion": suggestion,
            "level": "excellent" if score >= 80 else "good" if score >= 60 else "needs_improvement"
        }

    def _generate_economic_reason(
        self,
        student: Student,
        route_match: RouteMatch
    ) -> dict[str, Any]:
        """生成经济匹配理由"""
        score = route_match.economic_score
        budget = student.family_budget or 0

        # 生成评价
        if score >= 80:
            evaluation = "家庭经济条件充足，可支持各类升学路径"
            suggestion = "可以充分考虑高校的地域和专业，不必过度担心费用问题"
        elif score >= 60:
            evaluation = "家庭经济条件良好，可支持大部分升学路径"
            suggestion = "建议关注奖学金政策，985/211 高校奖学金覆盖率较高"
        else:
            evaluation = "经济条件略显紧张"
            suggestion = "建议优先考虑公费师范生、军校等免学费项目，或申请助学贷款"

        return {
            "score": score,
            "weight": self.dimension_weights["economic"],
            "budget": budget,
            "evaluation": evaluation,
            "suggestion": suggestion,
            "level": "excellent" if score >= 80 else "good" if score >= 60 else "needs_improvement"
        }

    def _generate_time_reason(
        self,
        student: Student,
        route_match: RouteMatch
    ) -> dict[str, Any]:
        """生成时间匹配理由"""
        score = route_match.time_score
        grade = student.grade or ""

        # 估算剩余时间
        time_map = {
            "初一": "6 年", "初二": "5 年", "初三": "4 年",
            "高一": "3 年", "高二": "2 年", "高三": "1 年"
        }
        remaining_time = time_map.get(grade, "未知")

        # 生成评价
        if score >= 80:
            evaluation = f"准备时间非常充足（剩余{remaining_time}）"
            suggestion = "制定长期规划，分阶段实施，不要急于求成"
        elif score >= 60:
            evaluation = f"准备时间较为充足（剩余{remaining_time}）"
            suggestion = "合理安排时间，平衡课内学习和升学准备"
        else:
            evaluation = f"准备时间紧张（剩余{remaining_time}）"
            suggestion = "立即行动，优先完成最重要的准备工作"

        return {
            "score": score,
            "weight": self.dimension_weights["time"],
            "grade": grade,
            "remaining_time": remaining_time,
            "evaluation": evaluation,
            "suggestion": suggestion,
            "level": "excellent" if score >= 80 else "good" if score >= 60 else "needs_improvement"
        }

    def _generate_region_reason(
        self,
        student: Student,
        route_match: RouteMatch
    ) -> dict[str, Any]:
        """生成地域匹配理由"""
        score = route_match.region_score
        preferred_locations = student.preferred_locations or []

        # 生成评价
        if score >= 80:
            evaluation = "高校地域分布与你的偏好高度匹配"
            suggestion = "可以优先考虑这些地区的高校，生活环境适应度更高"
        elif score >= 60:
            evaluation = "高校地域分布与你的偏好有一定匹配"
            suggestion = "建议开放心态，考虑更多地区的高校"
        else:
            evaluation = "高校地域分布与你的偏好匹配度较低"
            suggestion = "建议重新考虑地域偏好，或接受异地求学"

        return {
            "score": score,
            "weight": self.dimension_weights["region"],
            "preferred_locations": preferred_locations,
            "evaluation": evaluation,
            "suggestion": suggestion,
            "level": "excellent" if score >= 80 else "good" if score >= 60 else "needs_improvement"
        }

    def _generate_summary_reason(
        self,
        student: Student,
        route_match: RouteMatch,
        reasons: dict[str, Any]
    ) -> str:
        """生成综合评价"""
        total_score = route_match.match_score

        # 找出最强维度
        dimensions = [
            ("兴趣", reasons["interest"]["score"]),
            ("能力", reasons["ability"]["score"]),
            ("经济", reasons["economic"]["score"]),
            ("时间", reasons["time"]["score"]),
            ("地域", reasons["region"]["score"])
        ]
        best_dim = max(dimensions, key=lambda x: x[1])
        worst_dim = min(dimensions, key=lambda x: x[1])

        # 生成总结
        if total_score >= 80:
            summary = (
                f"这条赛道与你的匹配度非常高（{total_score:.1f}分）。"
                f"{best_dim[0]}是你的最大优势（{best_dim[1]:.0f}分），"
                f"建议重点关注这条赛道。"
            )
        elif total_score >= 60:
            summary = (
                f"这条赛道与你的匹配度良好（{total_score:.1f}分）。"
                f"{best_dim[0]}表现突出（{best_dim[1]:.0f}分），"
                f"但{worst_dim[0]}需要加强（{worst_dim[1]:.0f}分）。"
            )
        else:
            summary = (
                f"这条赛道与你的匹配度一般（{total_score:.1f}分）。"
                f"建议重点提升{worst_dim[0]}方面（{worst_dim[1]:.0f}分），"
                f"或考虑其他更适合的赛道。"
            )

        return summary

    def _generate_action_items(
        self,
        student: Student,
        route_match: RouteMatch,
        reasons: dict[str, Any]
    ) -> list[str]:
        """生成行动建议"""
        action_items = []

        # 根据各维度生成建议
        if reasons["interest"]["level"] == "needs_improvement":
            action_items.append(
                f"兴趣培养：{reasons['interest']['suggestion']}"
            )

        if reasons["ability"]["level"] == "needs_improvement":
            action_items.append(
                f"能力提升：{reasons['ability']['suggestion']}"
            )

        if reasons["economic"]["score"] < 70:
            action_items.append(
                f"经济规划：{reasons['economic']['suggestion']}"
            )

        if reasons["time"]["score"] < 70:
            action_items.append(
                f"时间管理：{reasons['time']['suggestion']}"
            )

        # 通用建议
        if len(action_items) == 0:
            action_items.append("继续保持当前的学习状态和兴趣发展")

        action_items.append("定期复盘规划进展，根据实际情况调整目标")
        action_items.append("与家长、老师保持沟通，获取多方建议")

        return action_items[:5]  # 最多 5 条建议
