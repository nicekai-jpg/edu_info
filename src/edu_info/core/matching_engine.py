"""
匹配引擎

多维度匹配学生与升学路线
"""
from typing import Any

from edu_info.models.schemas import PlanningRoute, RouteMatch, Student
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


class MatchingEngine:
    """匹配引擎"""

    # 匹配权重配置
    WEIGHTS = {
        "interest": 0.40,    # 兴趣匹配 (40%)
        "ability": 0.25,     # 能力匹配 (25%)
        "economic": 0.20,    # 经济匹配 (20%)
        "time": 0.10,        # 时间匹配 (10%)
        "region": 0.05,      # 地域匹配 (5%)
    }

    def __init__(self, weights: dict[str, float] | None = None):
        """
        初始化匹配引擎

        Args:
            weights: 权重配置（可选），默认使用 WEIGHTS
        """
        self.weights = weights or self.WEIGHTS.copy()
        self._validate_weights()
        logger.info("匹配引擎初始化完成")

    def _validate_weights(self):
        """验证权重和是否为 1.0"""
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            logger.warning(f"权重和为 {total}，建议调整为 1.0")

    def match_all(
        self,
        student: Student,
        routes: list[PlanningRoute]
    ) -> list[RouteMatch]:
        """
        匹配所有路线

        Args:
            student: 学生信息
            routes: 路线列表

        Returns:
            匹配结果列表（按匹配度降序排序）
        """
        logger.info(f"开始匹配 {len(routes)} 条路线")

        matches = []
        for route in routes:
            match = self.match_single(student, route)
            matches.append(match)

        # 按匹配度排序
        matches.sort(key=lambda x: x.match_score, reverse=True)

        logger.info(f"匹配完成，最高分：{matches[0].match_score if matches else 0:.2f}")
        return matches

    def match_single(self, student: Student, route: PlanningRoute) -> RouteMatch:
        """
        匹配单条路线

        Args:
            student: 学生信息
            route: 路线

        Returns:
            匹配结果
        """
        # 计算各维度匹配度
        interest_score = self._calculate_interest_match(student, route)
        ability_score = self._calculate_ability_match(student, route)
        economic_score = self._calculate_economic_match(student, route)
        time_score = self._calculate_time_match(student, route)
        region_score = self._calculate_region_match(student, route)

        # 计算总分
        match_score = (
            interest_score * self.weights["interest"] +
            ability_score * self.weights["ability"] +
            economic_score * self.weights["economic"] +
            time_score * self.weights["time"] +
            region_score * self.weights["region"]
        )

        # 生成建议
        recommendations = self._generate_recommendations(
            student, route, interest_score, ability_score, economic_score
        )

        # 创建匹配结果
        match = RouteMatch(
            route=route,
            match_score=match_score,
            interest_score=interest_score,
            ability_score=ability_score,
            economic_score=economic_score,
            time_score=time_score,
            region_score=region_score,
            recommendations=recommendations,
        )

        return match

    def _calculate_interest_match(
        self,
        student: Student,
        route: PlanningRoute
    ) -> float:
        """
        计算兴趣匹配度 (40%)

        Args:
            student: 学生信息
            route: 路线

        Returns:
            兴趣匹配度 (0-100)
        """
        if not student.interests:
            return 50.0  # 默认中等

        student_interests = set(student.interests)

        # 从路线描述和类别中提取关键词
        route_keywords = self._extract_route_keywords(route)

        # 计算重合度
        common = student_interests & route_keywords
        if not common:
            return 30.0  # 无兴趣匹配

        # 匹配度 = 重合数 / 学生兴趣数
        match_ratio = len(common) / len(student_interests)

        # 转换为 0-100 分
        score = 30.0 + match_ratio * 70.0  # 基础 30 分，最高 100 分

        return min(100.0, max(0.0, score))

    def _calculate_ability_match(
        self,
        student: Student,
        route: PlanningRoute
    ) -> float:
        """
        计算能力匹配度 (25%)

        Args:
            student: 学生信息
            route: 路线

        Returns:
            能力匹配度 (0-100)
        """
        # 基础分：根据成绩
        base_score = 50.0

        if student.total_score:
            # 假设满分 750
            score_ratio = student.total_score / 750.0
            base_score = 40.0 + score_ratio * 60.0  # 40-100 分

        # 根据路线难度调整
        difficulty_modifier = {
            "低": 1.2,
            "中等": 1.0,
            "高": 0.9,
            "极高": 0.8,
        }

        modifier = difficulty_modifier.get(route.difficulty, 1.0)

        # 考虑特长
        if student.specialities and route.requirements:
            # 检查是否满足特长要求
            has_speciality = self._check_speciality_match(
                student.specialities,
                route.requirements
            )
            if has_speciality:
                base_score += 10.0

        score = base_score * modifier
        return min(100.0, max(0.0, score))

    def _calculate_economic_match(
        self,
        student: Student,
        route: PlanningRoute
    ) -> float:
        """
        计算经济匹配度 (20%)

        Args:
            student: 学生信息
            route: 路线

        Returns:
            经济匹配度 (0-100)
        """
        if not student.family_budget or not route.cost_min:
            return 50.0  # 默认中等

        # 路线成本（取中间值）
        route_cost = (route.cost_min + (route.cost_max or route.cost_min)) / 2

        # 预算充足度
        budget_ratio = student.family_budget / route_cost

        if budget_ratio >= 2.0:
            return 100.0  # 预算非常充足
        elif budget_ratio >= 1.5:
            return 90.0
        elif budget_ratio >= 1.0:
            return 80.0
        elif budget_ratio >= 0.8:
            return 60.0
        elif budget_ratio >= 0.5:
            return 40.0
        else:
            return 20.0  # 预算严重不足

    def _calculate_time_match(
        self,
        student: Student,
        route: PlanningRoute
    ) -> float:
        """
        计算时间匹配度 (10%)

        Args:
            student: 学生信息
            route: 路线

        Returns:
            时间匹配度 (0-100)
        """
        # 根据年级评估剩余时间
        grade_time_map = {
            "初一": 6, "初二": 5, "初三": 4,
            "高一": 3, "高二": 2, "高三": 1,
        }

        remaining_years = grade_time_map.get(student.grade, 3)

        # 从路线要求中获取准备时间
        if route.requirements and "准备时间" in route.requirements:
            time_str = route.requirements["准备时间"]
            required_years = self._parse_time_requirement(time_str)

            if remaining_years >= required_years:
                return 100.0
            elif remaining_years >= required_years * 0.8:
                return 80.0
            elif remaining_years >= required_years * 0.6:
                return 60.0
            else:
                return 30.0

        # 默认时间充足
        return 80.0

    def _calculate_region_match(
        self,
        student: Student,
        route: PlanningRoute
    ) -> float:
        """
        计算地域匹配度 (5%)

        Args:
            student: 学生信息
            route: 路线

        Returns:
            地域匹配度 (0-100)
        """
        if not student.preferred_locations:
            return 50.0  # 默认中等

        # 路线没有明确地域要求，默认匹配
        if not route.target_university_types:
            return 70.0

        # 根据偏好地区数量评估
        num_preferences = len(student.preferred_locations)

        if num_preferences >= 3:
            return 80.0  # 偏好广泛，容易匹配
        elif num_preferences >= 2:
            return 70.0
        else:
            return 60.0  # 偏好单一，可能难匹配

    def _extract_route_keywords(self, route: PlanningRoute) -> set:
        """从路线中提取关键词"""
        keywords = set()

        # 从路线名称提取
        if "计算机" in route.route_name or "信息" in route.route_name:
            keywords.add("计算机")
            keywords.add("编程")

        if "电子" in route.route_name:
            keywords.add("电子")

        if "机械" in route.route_name or "机器人" in route.route_name:
            keywords.add("机器人")

        if "医学" in route.route_name:
            keywords.add("医学")

        if "经济" in route.route_name or "金融" in route.route_name:
            keywords.add("经济")

        # 从类别提取
        if route.category == "特长生":
            if "科技" in route.route_name:
                keywords.add("编程")
                keywords.add("机器人")
            if "艺术" in route.route_name:
                keywords.add("艺术")

        # 从学生兴趣中添加同义词
        if "编程" in keywords:
            keywords.add("计算机")

        return keywords

    def _check_speciality_match(
        self,
        specialities: list[str],
        requirements: dict[str, Any]
    ) -> bool:
        """检查特长是否匹配要求"""
        if not specialities or not requirements:
            return False

        # 检查竞赛要求
        if "竞赛要求" in requirements:
            req_keywords = ["竞赛", "奖项", "一等奖", "二等奖", "省级", "市级"]
            has_competition = any(
                keyword in spec
                for spec in specialities
                for keyword in req_keywords
            )
            if has_competition:
                return True

        # 检查专业要求
        if "专业要求" in requirements:
            req_keywords = ["专业", "水平", "等级", "十级"]
            has_professional = any(
                keyword in spec
                for spec in specialities
                for keyword in req_keywords
            )
            if has_professional:
                return True

        return False

    def _parse_time_requirement(self, time_str: str) -> float:
        """解析时间要求字符串（如"2-3 年"）"""
        import re

        # 提取数字
        numbers = re.findall(r'\d+', time_str)
        if not numbers:
            return 2.0  # 默认 2 年

        # 取最大值
        return float(max(numbers))

    def _generate_recommendations(
        self,
        student: Student,
        route: PlanningRoute,
        interest_score: float,
        ability_score: float,
        economic_score: float
    ) -> list[str]:
        """生成建议"""
        recommendations = []

        # 兴趣建议
        if interest_score < 50:
            recommendations.append(
                "建议培养对该方向的兴趣，可以参加相关活动或阅读相关书籍"
            )

        # 能力建议
        if ability_score < 60:
            recommendations.append(
                "建议提升学业成绩，特别是相关科目"
            )

        # 经济建议
        if economic_score < 50:
            recommendations.append(
                "该路线经济压力较大，建议考虑奖学金或助学贷款"
            )

        # 路线特定建议
        if route.difficulty == "极高":
            recommendations.append(
                "该路线难度极高，建议同时准备备选方案"
            )

        if not recommendations:
            recommendations.append("该路线与你的匹配度较高，建议重点考虑")

        return recommendations

    def get_top_matches(
        self,
        student: Student,
        routes: list[PlanningRoute],
        top_n: int = 10
    ) -> list[RouteMatch]:
        """
        获取 Top N 匹配路线

        Args:
            student: 学生信息
            routes: 路线列表
            top_n: 返回数量

        Returns:
            Top N 匹配结果
        """
        all_matches = self.match_all(student, routes)
        return all_matches[:top_n]
