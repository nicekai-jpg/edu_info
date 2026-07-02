"""
目标生成器

基于匹配结果生成三档目标高校
"""
from dataclasses import dataclass

from edu_info.models.schemas import PlanningRoute, RouteMatch, Student, TargetUniversity, University
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ScoreRange:
    """分数范围"""
    min_score: int
    avg_score: int
    max_score: int
    min_rank: int
    avg_rank: int
    max_rank: int


def get_major_tuition(university: University, major_name: str) -> int:
    """
    依据具体专业名称，匹配高校细分专业收费标准。如果没有匹配，回退到学校默认的 tuition_fee。
    """
    if not university.major_tuition_fees:
        return university.tuition_fee or 5500
        
    # 匹配中外合作
    if "中外合作" in major_name or "联合培养" in major_name:
        if "中外合作" in university.major_tuition_fees:
            return university.major_tuition_fees["中外合作"]
            
    # 匹配艺术类
    if any(x in major_name for x in ["音乐", "美术", "设计", "艺术", "舞蹈", "戏剧", "播音", "主持"]):
        if "艺术类" in university.major_tuition_fees:
            return university.major_tuition_fees["艺术类"]
            
    # 匹配软件工程高收费
    if "软件工程" in major_name:
        if "软件工程" in university.major_tuition_fees:
            return university.major_tuition_fees["软件工程"]
        if "软件工程(高年级)" in university.major_tuition_fees:
            return university.major_tuition_fees["软件工程(高年级)"]
            
    # 匹配医学
    if any(x in major_name for x in ["医学", "临床", "口腔", "药学", "护理"]):
        if "医学类" in university.major_tuition_fees:
            return university.major_tuition_fees["医学类"]
            
    # 按照文理工科回退
    if any(x in major_name for x in ["理", "工", "计算机", "数学", "物理", "化学", "机械", "自动化", "电子"]):
        return university.major_tuition_fees.get("普通工科") or university.major_tuition_fees.get("普通理科") or university.major_tuition_fees.get("普通专业") or university.tuition_fee or 5500
    else:
        return university.major_tuition_fees.get("普通文科") or university.major_tuition_fees.get("普通专业") or university.tuition_fee or 5500


class TargetGenerator:
    """目标生成器"""

    # 三档目标的录取概率范围
    TARGET_PROBABILITY = {
        "高目标": (30, 50),    # 冲刺：30-50% 概率
        "中目标": (50, 80),    # 稳妥：50-80% 概率
        "低目标": (80, 95),    # 保底：80-95% 概率
    }

    # 分数浮动范围（分）
    SCORE_BUFFER = {
        "高目标": 10,   # 冲刺目标允许 10 分浮动
        "中目标": 5,    # 稳妥目标 5 分浮动
        "低目标": -10,  # 保底目标留 10 分余量
    }

    def __init__(self, db_path: str | None = None):
        """
        初始化目标生成器

        Args:
            db_path: 数据库路径（可选）
        """
        self.db_path = db_path
        logger.info("目标生成器初始化完成")

    def generate_targets(
        self,
        student: Student,
        route: PlanningRoute,
        universities: list[University],
        score_data: dict[int, ScoreRange]
    ) -> tuple[list[TargetUniversity], list[TargetUniversity], list[TargetUniversity]]:
        """
        生成三档目标

        Args:
            student: 学生信息
            route: 匹配的路线
            universities: 高校列表
            score_data: 分数数据 {university_id: ScoreRange}

        Returns:
            (高目标列表，中目标列表，低目标列表)
        """
        logger.info(f"开始生成目标（{len(universities)} 所高校）")

        high_targets = []
        medium_targets = []
        low_targets = []

        # 根据学生分数筛选高校
        filtered_universities = self._filter_universities(
            student, universities, score_data, route
        )

        logger.info(f"筛选后剩余 {len(filtered_universities)} 所高校")

        # 为每所高校生成目标
        for university in filtered_universities:
            score_range = score_data.get(university.id)
            if not score_range:
                continue

            # 评估录取概率
            probability = self._evaluate_probability(student, score_range)

            # 确定目标档次
            target_type = self._determine_target_type(probability)

            major = self._suggest_major(student, route)

            # 校验特定专业的学费预算限制
            specific_tuition = get_major_tuition(university, major)
            if student.family_budget is not None:
                tuition_in_wan = specific_tuition / 10000.0
                if tuition_in_wan > student.family_budget:
                    logger.info(f"【家庭预算拦截】跳过高校 {university.name}：专业 {major}，特定收费 {specific_tuition}元/年，超过家庭上限 {student.family_budget}万元/年")
                    continue

            # 校验身体体检限制条件
            constraints = university.admission_constraints or {}
            is_health_ok = True
            health_reason = ""
            if getattr(student, "color_blind", False):
                blind_limits = constraints.get("color_blindness_limit") or []
                if any(limit in major for limit in blind_limits):
                    is_health_ok = False
                    health_reason = "考生色盲受限"
            if getattr(student, "color_weak", False):
                weak_limits = constraints.get("color_weakness_limit") or []
                if any(limit in major for limit in weak_limits):
                    is_health_ok = False
                    health_reason = "考生色弱受限"
            if not is_health_ok:
                logger.info(f"【体检要求拦截】跳过高校 {university.name}：专业 {major} 因【{health_reason}】被拦截")
                continue

            # 校验单科成绩最低限制条件
            is_single_subject_ok = True
            subject_reason = ""
            single_subject_mins = constraints.get("single_subject_min") or {}
            for major_pattern, subject_limits in single_subject_mins.items():
                if major_pattern in major:
                    for sub_name, min_val in subject_limits.items():
                        if sub_name == "外语":
                            score_val = getattr(student, "english_score", None)
                            if score_val is not None and score_val < min_val:
                                is_single_subject_ok = False
                                subject_reason = f"外语单科分 {score_val} 低于专业下限 {min_val}"
                                break
                        elif sub_name == "数学":
                            score_val = getattr(student, "math_score", None)
                            if score_val is not None and score_val < min_val:
                                is_single_subject_ok = False
                                subject_reason = f"数学单科分 {score_val} 低于专业下限 {min_val}"
                                break
            if not is_single_subject_ok:
                logger.info(f"【单科成绩拦截】跳过高校 {university.name}：专业 {major} 因【{subject_reason}】被拦截")
                continue

            # 校验高考选科条件限制
            from edu_info.core.subject_validator import SubjectValidator
            student_subjects = getattr(student, "subjects", None)
            is_eligible, reason = SubjectValidator.is_eligible(student_subjects, major, student.category)
            if not is_eligible:
                logger.info(f"【选科要求拦截】跳过高校 {university.name}：专业 {major} 选科冲突（{reason}）")
                continue

            # 创建目标
            target = TargetUniversity(
                university=university,
                target_type=target_type,
                major=major,
                min_score=score_range.min_score,
                min_rank=score_range.min_rank,
                year=2025,
                probability=probability,
                analysis=self._generate_analysis(student, score_range, probability),
                recommendations=self._generate_recommendations(
                    student, university, score_range, probability
                ),
            )

            # 添加到对应档次
            if target_type == "高目标":
                high_targets.append(target)
            elif target_type == "中目标":
                medium_targets.append(target)
            else:
                low_targets.append(target)

        # 每档限制数量（最多 5 所）
        high_targets = high_targets[:5]
        medium_targets = medium_targets[:5]
        low_targets = low_targets[:5]

        logger.info(f"目标生成完成：高={len(high_targets)}, 中={len(medium_targets)}, 低={len(low_targets)}")

        return high_targets, medium_targets, low_targets

    def _filter_universities(
        self,
        student: Student,
        universities: list[University],
        score_data: dict[int, ScoreRange],
        route: PlanningRoute
    ) -> list[University]:
        """
        筛选符合条件的高校

        Args:
            student: 学生信息
            universities: 高校列表
            score_data: 分数数据
            route: 路线

        Returns:
            筛选后的高校列表
        """
        filtered = []

        for university in universities:
            # 检查高校类型匹配
            if route.target_university_types:
                uni_type = self._get_university_type(university)
                if uni_type not in route.target_university_types:
                    continue

            # 检查分数数据存在
            if university.id not in score_data:
                continue

            score_range = score_data[university.id]

            # 检查分数是否在合理范围（±30 分）
            if student.total_score:
                score_diff = abs(student.total_score - score_range.avg_score)
                if score_diff > 30:
                    continue

            # 学费预算限制校验移至 generate_targets 循环中进行具体专业级别比对

            filtered.append(university)

        return filtered

    def _get_university_type(self, university: University) -> str:
        """获取高校类型标签"""
        if university.is_985:
            return "985"
        elif university.is_211:
            return "211"
        elif university.is_double_first_class:
            return "双一流"
        else:
            return "普通"

    def _evaluate_probability(
        self,
        student: Student,
        score_range: ScoreRange
    ) -> float:
        """
        评估录取概率

        Args:
            student: 学生信息
            score_range: 分数范围

        Returns:
            录取概率 (0-100)
        """
        if not student.total_score:
            return 50.0  # 默认 50%

        # 基于分数的概率
        score_diff = student.total_score - score_range.avg_score

        if score_diff >= 20:
            # 超过平均分 20 分以上
            score_prob = 90.0 + min((score_diff - 20) / 10, 10)
        elif score_diff >= 10:
            # 超过 10-20 分
            score_prob = 70.0 + (score_diff - 10) * 2
        elif score_diff >= 0:
            # 超过 0-10 分
            score_prob = 50.0 + score_diff * 2
        elif score_diff >= -10:
            # 低于 0-10 分
            score_prob = 30.0 + (score_diff + 10) * 2
        else:
            # 低于 10 分以上
            score_prob = max(10.0, 30.0 + score_diff * 3)

        # 基于位次的概率
        if student.ranking and score_range.avg_rank:
            rank_ratio = student.ranking / score_range.avg_rank
            if rank_ratio <= 0.5:
                rank_prob = 95.0
            elif rank_ratio <= 0.8:
                rank_prob = 70.0 + (0.8 - rank_ratio) * 125
            elif rank_ratio <= 1.2:
                rank_prob = 50.0 + (1.2 - rank_ratio) * 100
            else:
                rank_prob = max(10.0, 50.0 - (rank_ratio - 1.2) * 50)

            # 综合分数和位次（分数权重 60%，位次权重 40%）
            probability = score_prob * 0.6 + rank_prob * 0.4
        else:
            probability = score_prob

        return min(100.0, max(0.0, probability))

    def _determine_target_type(self, probability: float) -> str:
        """
        根据概率确定目标档次

        Args:
            probability: 录取概率

        Returns:
            目标档次
        """
        for target_type, (prob_min, prob_max) in self.TARGET_PROBABILITY.items():
            if prob_min <= probability < prob_max:
                return target_type

        # 边界情况
        if probability >= 95:
            return "低目标"  # 超稳保底
        elif probability < 30:
            return "高目标"  # 超难冲刺
        else:
            return "中目标"

    def _suggest_major(
        self,
        student: Student,
        route: PlanningRoute
    ) -> str | None:
        """
        建议专业

        Args:
            student: 学生信息
            route: 路线

        Returns:
            建议专业名称
        """
        # 从路线中获取专业建议
        if route.target_major_types and len(route.target_major_types) > 0:
            return route.target_major_types[0]

        # 从兴趣推断
        if student.interests:
            interest_map = {
                "编程": "计算机类",
                "机器人": "自动化类",
                "数学": "数学类",
                "医学": "医学类",
                "经济": "经济类",
                "文学": "文学类",
            }
            for interest in student.interests:
                if interest in interest_map:
                    return interest_map[interest]

        return None

    def _generate_analysis(
        self,
        student: Student,
        score_range: ScoreRange,
        probability: float
    ) -> str:
        """
        生成目标分析

        Args:
            student: 学生信息
            score_range: 分数范围
            probability: 录取概率

        Returns:
            分析文本
        """
        if not student.total_score:
            return "暂无分数数据，无法详细分析"

        score_diff = student.total_score - score_range.avg_score

        if score_diff >= 10:
            advantage = f"分数优势明显（+{score_diff:.1f}分）"
        elif score_diff >= 0:
            advantage = f"分数略有优势（+{score_diff:.1f}分）"
        elif score_diff >= -10:
            advantage = f"分数稍处劣势（-{abs(score_diff):.1f}分）"
        else:
            advantage = f"分数明显劣势（-{abs(score_diff):.1f}分）"

        if student.ranking and score_range.avg_rank:
            rank_diff = student.ranking - score_range.avg_rank
            if rank_diff < 0:
                rank_text = f"位次优势明显（领先{abs(rank_diff)}名）"
            else:
                rank_text = f"位次处劣势（落后{rank_diff}名）"
        else:
            rank_text = ""

        return f"{advantage}{'; ' + rank_text if rank_text else ''}，录取概率{probability:.1f}%"

    def _generate_recommendations(
        self,
        student: Student,
        university: University,
        score_range: ScoreRange,
        probability: float
    ) -> list[str]:
        """
        生成建议

        Args:
            student: 学生信息
            university: 高校信息
            score_range: 分数范围
            probability: 录取概率

        Returns:
            建议列表
        """
        recommendations = []

        if probability >= 80:
            recommendations.append("录取希望较大，建议作为保底/稳妥选择")
            recommendations.append("保持当前学习状态，巩固优势科目")
        elif probability >= 50:
            recommendations.append("有一定录取希望，建议重点准备")
            recommendations.append("提升弱势科目，增加录取把握")
        elif probability >= 30:
            recommendations.append("冲刺目标，需要付出较大努力")
            recommendations.append("制定详细提升计划，重点关注位次提升")
        else:
            recommendations.append("难度较大，建议同时准备备选方案")
            recommendations.append("可以考虑该校的冷门专业或分校")

        # 高校特定建议
        if university.is_985:
            recommendations.append("985 高校竞争激烈，建议参加强基计划/综合评价增加机会")
        elif university.is_211:
            recommendations.append("211 高校，建议关注特殊类型招生政策")

        return recommendations

    def generate_from_matches(
        self,
        student: Student,
        matches: list[RouteMatch],
        universities: list[University],
        score_data: dict[int, ScoreRange],
        top_n: int = 3
    ) -> dict[str, dict[str, list[TargetUniversity]]]:
        """
        从匹配结果生成目标

        Args:
            student: 学生信息
            matches: 路线匹配结果
            universities: 高校列表
            score_data: 分数数据
            top_n: 选择 Top N 路线

        Returns:
            {路线名：{档次：目标列表}}
        """
        results = {}

        # 选择 Top N 路线
        top_matches = matches[:top_n]

        for match in top_matches:
            route_name = match.route.route_name

            # 生成该路线的三档目标
            high, medium, low = self.generate_targets(
                student, match.route, universities, score_data
            )

            results[route_name] = {
                "高目标": high,
                "中目标": medium,
                "低目标": low,
            }

        return results
