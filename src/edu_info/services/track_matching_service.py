"""
赛道匹配服务

基于 Code Craft 原则：
- 单一职责：仅负责匹配计算，无数据访问
- 组合优于继承：由多个维度组件组合而成
- 封装：私有方法 + 公共接口
"""

from datetime import datetime
from typing import Any

from ..core.matching_reason_generator import MatchingReasonGenerator
from ..data.repositories.track_repository import TrackRepository
from ..models.schemas import Student
from ..models.track import StudentTrackMatch, Track
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class TrackMatchingService:
    """赛道匹配服务 - 组合多个维度"""

    # 匹配权重配置（与现有系统一致）
    WEIGHTS = {
        "interest": 0.40,    # 兴趣匹配 (40%)
        "ability": 0.25,     # 能力匹配 (25%)
        "economic": 0.20,    # 经济匹配 (20%)
        "time": 0.10,        # 时间匹配 (10%)
        "region": 0.05,      # 地域匹配 (5%)
    }

    def __init__(
        self,
        track_repo: TrackRepository | None = None,
        weights: dict[str, float] | None = None
    ):
        """
        初始化赛道匹配服务

        Args:
            track_repo: 赛道数据仓库（可选，默认创建实例）
            weights: 权重配置（可选）
        """
        self.track_repo = track_repo or TrackRepository()
        self.weights = weights or self.WEIGHTS.copy()
        self.reason_generator = MatchingReasonGenerator()

        self._validate_weights()
        logger.info("赛道匹配服务初始化完成")

    def _validate_weights(self):
        """验证权重和是否为 1.0"""
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            logger.warning(f"权重和为 {total}，建议调整为 1.0")

    def match_all_tracks(self, student: Student) -> list[StudentTrackMatch]:
        """
        匹配所有赛道

        Args:
            student: 学生信息

        Returns:
            匹配结果列表（按匹配度降序排序）
        """
        logger.info(f"开始赛道匹配，学生：{student.name}")

        # 获取所有赛道
        all_tracks = self.track_repo.get_all_tracks()
        logger.info(f"共加载 {len(all_tracks)} 个赛道")

        matches = []
        for track in all_tracks:
            match = self.match_single_track(student, track)
            matches.append(match)

        # 按匹配度排序
        matches.sort(key=lambda x: x.match_score, reverse=True)

        logger.info(
            f"赛道匹配完成，最高分：{matches[0].match_score if matches else 0:.2f}, "
            f"赛道：{matches[0].track_id if matches else 'N/A'}"
        )

        return matches

    def match_single_track(
        self,
        student: Student,
        track: Track
    ) -> StudentTrackMatch:
        """
        匹配单个赛道

        Args:
            student: 学生信息
            track: 赛道信息

        Returns:
            匹配结果
        """
        # 计算各维度匹配度
        interest_score = self._calculate_interest_match(student, track)
        ability_score = self._calculate_ability_match(student, track)
        economic_score = self._calculate_economic_match(student, track)
        time_score = self._calculate_time_match(student, track)
        region_score = self._calculate_region_match(student, track)

        # 计算总分
        match_score = (
            interest_score * self.weights["interest"] +
            ability_score * self.weights["ability"] +
            economic_score * self.weights["economic"] +
            time_score * self.weights["time"] +
            region_score * self.weights["region"]
        )

        # 生成匹配理由（五维分析）
        match_reasons = self._generate_match_reasons(
            student, track, interest_score, ability_score,
            economic_score, time_score, region_score
        )

        # 生成差距分析
        gaps = self._analyze_gaps(student, track)

        # 生成行动建议
        action_items = self._generate_action_items(
            student, track, match_reasons
        )

        # 创建匹配结果
        match = StudentTrackMatch(
            match_id=int(datetime.now().timestamp() * 1000) % 10**18,
            student_id=student.id or 0,
            track_id=track.track_id,
            match_score=round(match_score, 2),
            interest_score=round(interest_score, 2),
            ability_score=round(ability_score, 2),
            economic_score=round(economic_score, 2),
            time_score=round(time_score, 2),
            regional_score=round(region_score, 2),
            match_reasons=match_reasons,
            gaps=gaps,
            action_items=action_items,
            generated_at=datetime.now()
        )

        return match

    def _calculate_interest_match(
        self,
        student: Student,
        track: Track
    ) -> float:
        """
        计算兴趣匹配度 (40%)

        Args:
            student: 学生信息
            track: 赛道信息

        Returns:
            兴趣匹配度 (0-100)
        """
        if not student.interests:
            return 50.0  # 默认中等

        student_interests = set(student.interests)

        # 从赛道名称和描述中提取关键词
        track_keywords = self._extract_track_keywords(track)

        # 计算重合度
        common = student_interests & track_keywords
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
        track: Track
    ) -> float:
        """
        计算能力匹配度 (25%)

        Args:
            student: 学生信息
            track: 赛道信息

        Returns:
            能力匹配度 (0-100)
        """
        # 基础分：根据成绩
        base_score = 50.0

        if student.total_score:
            # 假设满分 750
            score_ratio = student.total_score / 750.0
            base_score = 40.0 + score_ratio * 60.0  # 40-100 分

        # 检查赛道能力要求
        if track.requirements and track.requirements.score_requirements:
            score_reqs = track.requirements.score_requirements

            # 检查是否满足分数要求
            if student.total_score:
                required_total = score_reqs.get("总分", 0)
                if required_total > 0:
                    if student.total_score >= required_total:
                        base_score += 10.0  # 满足要求，加分
                    else:
                        # 差距越大，扣分越多
                        gap = required_total - student.total_score
                        base_score -= min(20.0, gap / 10.0)

        return min(100.0, max(0.0, base_score))

    def _calculate_economic_match(
        self,
        student: Student,
        track: Track
    ) -> float:
        """
        计算经济匹配度 (20%)

        Args:
            student: 学生信息
            track: 赛道信息

        Returns:
            经济匹配度 (0-100)
        """
        if not student.family_budget:
            return 50.0  # 默认中等

        # 获取赛道就业薪资信息
        if not track.employment_info or not track.employment_info.avg_salary:
            return 50.0  # 无薪资数据，默认中等

        # 假设培养成本与未来薪资正相关
        # 这里简化处理：用薪资的 1/5 作为培养成本估算
        estimated_cost = track.employment_info.avg_salary / 5

        # 预算充足度
        budget_ratio = student.family_budget / estimated_cost if estimated_cost > 0 else 1.0

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
        track: Track
    ) -> float:
        """
        计算时间匹配度 (10%)

        Args:
            student: 学生信息
            track: 赛道信息

        Returns:
            时间匹配度 (0-100)
        """
        # 根据年级评估剩余时间
        grade_time_map = {
            "初一": 6, "初二": 5, "初三": 4,
            "高一": 3, "高二": 2, "高三": 1,
        }

        remaining_years = grade_time_map.get(student.grade, 3)

        # 默认时间充足
        if remaining_years >= 3:
            return 100.0
        elif remaining_years >= 2:
            return 90.0
        elif remaining_years >= 1:
            return 80.0
        else:
            return 60.0

    def _calculate_region_match(
        self,
        student: Student,
        track: Track
    ) -> float:
        """
        计算地域匹配度 (5%)

        Args:
            student: 学生信息
            track: 赛道信息

        Returns:
            地域匹配度 (0-100)
        """
        if not student.preferred_locations:
            return 50.0  # 默认中等

        # 赛道没有明确地域要求，默认匹配
        if not track.domains:
            return 70.0

        # 根据偏好地区数量评估
        num_preferences = len(student.preferred_locations)

        if num_preferences >= 3:
            return 80.0  # 偏好广泛，容易匹配
        elif num_preferences >= 2:
            return 70.0
        else:
            return 60.0  # 偏好单一，可能难匹配

    def _extract_track_keywords(self, track: Track) -> set:
        """从赛道中提取关键词"""
        keywords = set()

        # 从赛道名称提取
        track_name = track.track_name

        if "AI" in track_name or "人工智能" in track_name or "算法" in track_name:
            keywords.add("计算机")
            keywords.add("编程")
            keywords.add("AI")

        if "数据" in track_name:
            keywords.add("数据分析")
            keywords.add("计算机")

        if "机器人" in track_name:
            keywords.add("机器人")

        if "飞行器" in track_name or "低空" in track_name or "航空" in track_name:
            keywords.add("航空航天")

        if "非遗" in track_name:
            keywords.add("文化")
            keywords.add("非遗")

        if "传播" in track_name or "媒体" in track_name:
            keywords.add("传媒")
            keywords.add("文化传播")

        # 从赛道描述提取
        if track.description:
            if "算法" in track.description:
                keywords.add("编程")
            if "设计" in track.description:
                keywords.add("设计")

        return keywords

    def _analyze_gaps(
        self,
        student: Student,
        track: Track
    ) -> list[dict[str, Any]]:
        """分析学生与赛道的差距"""
        gaps = []

        # 分数差距
        if track.requirements and track.requirements.score_requirements:
            score_reqs = track.requirements.score_requirements
            required_total = score_reqs.get("总分", 0)

            if student.total_score and required_total > 0:
                gap = required_total - student.total_score
                if gap > 0:
                    gaps.append({
                        "type": "score",
                        "description": f"总分差距：还需提升{gap}分",
                        "current": student.total_score,
                        "target": required_total,
                        "priority": "high" if gap > 50 else "medium"
                    })

        # 技能差距
        if track.requirements and track.requirements.required_skills:
            student_skills = set(student.specialities or [])
            required_skills = set(track.requirements.required_skills)

            missing_skills = required_skills - student_skills
            if missing_skills:
                gaps.append({
                    "type": "skills",
                    "description": f"需要培养的技能：{', '.join(missing_skills)}",
                    "missing": list(missing_skills),
                    "priority": "medium"
                })

        return gaps

    def _generate_action_items(
        self,
        student: Student,
        track: Track,
        match_reasons: dict[str, Any]
    ) -> list[str]:
        """生成行动建议"""
        action_items = []

        # 根据匹配理由生成建议
        if match_reasons:
            # 兴趣匹配建议
            if "interest" in match_reasons:
                interest_reason = match_reasons["interest"]
                if interest_reason.get("score", 100) < 50:
                    action_items.append(
                        "培养对该赛道的兴趣：参加相关活动、阅读专业书籍"
                    )

            # 能力匹配建议
            if "ability" in match_reasons:
                ability_reason = match_reasons["ability"]
                if ability_reason.get("score", 100) < 60:
                    action_items.append(
                        "提升学业成绩，特别是数学、物理等相关科目"
                    )

            # 经济匹配建议
            if "economic" in match_reasons:
                economic_reason = match_reasons["economic"]
                if economic_reason.get("score", 100) < 50:
                    action_items.append(
                        "了解奖学金政策，规划教育资金"
                    )

        # 根据赛道特性生成建议
        if track.requirements and track.requirements.required_skills:
            skills = track.requirements.required_skills[:3]  # 取前 3 个
            action_items.append(
                f"提前学习相关技能：{', '.join(skills)}"
            )

        # 如果建议太少，添加通用建议
        if not action_items:
            action_items.append(
                "保持当前学习状态，关注赛道最新动态"
            )

        return action_items[:5]  # 最多 5 条建议

    def _generate_match_reasons(
        self,
        student: Student,
        track: Track,
        interest_score: float,
        ability_score: float,
        economic_score: float,
        time_score: float,
        region_score: float
    ) -> dict[str, Any]:
        """生成匹配理由（五维分析）"""
        reasons = {}

        # 兴趣匹配理由
        if student.interests and track.track_name:
            track_keywords = self._extract_track_keywords(track)
            common_interests = set(student.interests) & track_keywords
            if common_interests:
                comment = f"你的兴趣 ({', '.join(common_interests)}) 与该赛道高度契合"
            else:
                comment = "该赛道与你的兴趣关联度一般，建议了解赛道内容"
            reasons["interest"] = {
                "score": interest_score,
                "comment": comment,
                "suggestion": "参加相关活动培养兴趣" if interest_score < 50 else "保持兴趣优势"
            }

        # 能力匹配理由
        if student.total_score and track.requirements and track.requirements.score_requirements:
            required_score = track.requirements.score_requirements.get("总分", 0)
            if required_score > 0:
                gap = required_score - student.total_score
                if gap <= 0:
                    comment = f"你的成绩达到赛道要求（{required_score}分）"
                elif gap <= 30:
                    comment = f"成绩接近赛道要求，还需提升{gap}分"
                else:
                    comment = f"成绩与赛道要求有差距，需提升{gap}分"
            else:
                comment = "成绩水平与赛道匹配度良好"
            reasons["ability"] = {
                "score": ability_score,
                "comment": comment,
                "suggestion": "重点提升相关科目成绩" if ability_score < 60 else "保持学业优势"
            }

        # 经济匹配理由
        if student.family_budget:
            if economic_score >= 80:
                comment = "家庭经济条件可以支持该赛道发展"
            elif economic_score >= 50:
                comment = "经济条件基本满足，建议规划教育资金"
            else:
                comment = "经济压力较大，建议了解奖学金政策"
            reasons["economic"] = {
                "score": economic_score,
                "comment": comment,
                "suggestion": "了解奖学金和助学贷款" if economic_score < 50 else "合理规划教育支出"
            }

        # 时间匹配理由
        grade_time_map = {"初一": 6, "初二": 5, "初三": 4, "高一": 3, "高二": 2, "高三": 1}
        remaining_years = grade_time_map.get(student.grade, 3)
        if remaining_years >= 3:
            comment = f"准备时间充足（{remaining_years}年）"
        elif remaining_years >= 2:
            comment = f"准备时间较紧张（{remaining_years}年）"
        else:
            comment = f"准备时间紧迫（{remaining_years}年）"
        reasons["time"] = {
            "score": time_score,
            "comment": comment,
            "suggestion": "制定高效学习计划" if time_score < 70 else "合理安排时间"
        }

        # 地域匹配理由
        if student.preferred_locations:
            if len(student.preferred_locations) >= 3:
                comment = "地域偏好广泛，选择灵活"
            elif len(student.preferred_locations) >= 2:
                comment = "地域偏好适中"
            else:
                comment = "地域偏好较为集中"
        else:
            comment = "无明确地域偏好"
        reasons["region"] = {
            "score": region_score,
            "comment": comment,
            "suggestion": "考虑赛道产业分布地区" if region_score < 60 else "地域匹配良好"
        }

        return reasons

    def _create_temp_route_match(
        self,
        track: Track,
        interest_score: float,
        ability_score: float,
        economic_score: float,
        time_score: float,
        region_score: float
    ) -> dict[str, Any]:
        """创建临时 RouteMatch 对象用于生成理由"""
        # 为了兼容现有的 MatchingReasonGenerator
        return {
            "track": track,
            "interest_score": interest_score,
            "ability_score": ability_score,
            "economic_score": economic_score,
            "time_score": time_score,
            "region_score": region_score,
        }

    def get_top_tracks(
        self,
        student: Student,
        top_n: int = 10
    ) -> list[StudentTrackMatch]:
        """
        获取 Top N 匹配赛道

        Args:
            student: 学生信息
            top_n: 返回数量

        Returns:
            Top N 匹配结果
        """
        all_matches = self.match_all_tracks(student)
        return all_matches[:top_n]

    def save_match_result(
        self,
        match: StudentTrackMatch
    ) -> None:
        """
        保存匹配结果到数据库

        Args:
            match: 匹配结果
        """
        self.track_repo.save_student_track_match(match)
        logger.debug(f"保存匹配结果：学生{match.student_id}, 赛道{match.track_id}")

    def get_matches_by_student(
        self,
        student_id: int
    ) -> list[StudentTrackMatch]:
        """
        根据学生 ID 获取匹配结果

        Args:
            student_id: 学生 ID

        Returns:
            匹配结果列表
        """
        return self.track_repo.get_student_matches(student_id)
