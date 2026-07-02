"""
规划引擎主类

整合所有核心模块，提供完整的规划流程
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from edu_info.core.feasibility_assessor import FeasibilityAssessor
from edu_info.core.matching_engine import MatchingEngine
from edu_info.core.route_enumerator import RouteEnumerator
from edu_info.core.target_generator import ScoreRange, TargetGenerator
from edu_info.models.schemas import (
    PlanningResult,
    RouteMatch,
    Student,
    TargetUniversity,
)
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class PlanningRequest:
    """规划请求"""
    student: Student
    include_routes: bool = True  # 是否包含路线推荐
    include_targets: bool = True  # 是否包含目标高校
    top_n_routes: int = 10  # 推荐路线数量
    universities: list | None = None  # 高校列表
    score_data: dict[int, ScoreRange] | None = None  # 分数数据


class PlanningEngine:
    """规划引擎主类"""

    def __init__(self, db_path: str | None = None):
        """
        初始化规划引擎

        Args:
            db_path: 数据库路径（可选）
        """
        self.db_path = db_path
        self.route_enumerator = RouteEnumerator()
        self.matching_engine = MatchingEngine()
        self.target_generator = TargetGenerator(db_path)
        self.feasibility_assessor = FeasibilityAssessor()

        logger.info("规划引擎初始化完成")

    def generate_plan(
        self,
        student: Student,
        universities: list | None = None,
        score_data: dict[int, ScoreRange] | None = None
    ) -> PlanningResult:
        """
        生成完整规划方案

        Args:
            student: 学生信息
            universities: 高校列表（可选）
            score_data: 分数数据（可选）

        Returns:
            规划结果
        """
        logger.info(f"开始生成规划方案：{student.name}")

        # 1. 路线穷举
        routes = self.route_enumerator.enumerate_all(student.grade)
        logger.info(f"生成 {len(routes)} 条路线")

        # 2. 路线匹配
        matches = self.matching_engine.match_all(student, routes)
        logger.info(f"完成路线匹配，最高分：{matches[0].match_score:.2f}")

        # 3. 选择 Top 路线
        top_routes = matches[:10]

        # 4. 生成目标高校
        high_targets = []
        medium_targets = []
        low_targets = []

        if universities and score_data:
            # 依次尝试匹配排名前列的路线，直到生成出非空的目标高校为止（避开选科冲突等过滤）
            for idx, route_match in enumerate(top_routes):
                high, medium, low = self.target_generator.generate_targets(
                    student, route_match.route, universities, score_data
                )
                if high or medium or low:
                    high_targets = high
                    medium_targets = medium
                    low_targets = low
                    # 动态将该非冲突路线调整为最佳推荐路线
                    if idx > 0:
                        logger.info(f"由于首选路线存在选科等冲突，自动切换并推荐次优路线：{route_match.route.route_name}")
                        top_routes.insert(0, top_routes.pop(idx))
                    break
            logger.info(f"最终生成目标数量：高={len(high_targets)}, 中={len(medium_targets)}, 低={len(low_targets)}")

        # 5. 可行性评估
        feasibility_report = self.feasibility_assessor.generate_feasibility_report(
            student, top_routes, high_targets + medium_targets + low_targets
        )

        # 6. 组织结果
        result = PlanningResult(
            student_id=student.id or 0,
            created_at=datetime.now(),
            top_routes=top_routes,
            high_targets=high_targets,
            medium_targets=medium_targets,
            low_targets=low_targets,
            overall_feasibility=feasibility_report["route_assessments"][0]["feasibility_score"] if feasibility_report["route_assessments"] else 0,
            risk_assessment=feasibility_report["overall_recommendation"],
            summary=self._generate_summary(student, top_routes, high_targets),
            action_items=self._generate_action_items(student, top_routes),
        )

        logger.info("规划方案生成完成")
        return result

    def _generate_summary(
        self,
        student: Student,
        top_routes: list[RouteMatch],
        high_targets: list[TargetUniversity]
    ) -> str | None:
        """
        生成规划总结

        Args:
            student: 学生信息
            top_routes: 推荐路线
            high_targets: 高目标高校

        Returns:
            总结文本
        """
        if not top_routes:
            return None

        best_route = top_routes[0]

        summary_parts = [
            f"{student.name}同学，根据你的情况和兴趣，",
            f"最推荐的路线是**{best_route.route.route_name}**（匹配度{best_route.match_score:.1f}分）。",
        ]

        if high_targets:
            summary_parts.append(
                f"建议冲刺**{high_targets[0].university.name}**等高校。"
            )

        return " ".join(summary_parts)

    def _generate_action_items(
        self,
        student: Student,
        top_routes: list[RouteMatch]
    ) -> list[str] | None:
        """
        生成行动建议

        Args:
            student: 学生信息
            top_routes: 推荐路线

        Returns:
            行动建议列表
        """
        if not top_routes:
            return None

        action_items = []

        # 根据最佳路线生成建议
        best_route = top_routes[0]

        if best_route.recommendations:
            action_items.extend(best_route.recommendations[:3])

        # 根据学生情况生成建议
        if student.total_score and student.total_score < 650:
            action_items.append("制定学习计划，重点提升弱势科目")

        if not student.specialities:
            action_items.append("参加竞赛或活动，培养特长")

        return action_items

    def quick_plan(self, student: Student) -> dict[str, Any]:
        """
        快速规划（仅路线推荐）

        Args:
            student: 学生信息

        Returns:
            快速规划结果字典
        """
        logger.info(f"开始快速规划：{student.name}")

        # 路线穷举
        routes = self.route_enumerator.enumerate_all(student.grade)

        # 路线匹配
        matches = self.matching_engine.match_all(student, routes)

        # 组织结果
        return {
            "student_name": student.name,
            "top_routes": [
                {
                    "route_name": match.route.route_name,
                    "match_score": match.match_score,
                    "recommendations": match.recommendations,
                }
                for match in matches[:5]
            ],
            "timestamp": datetime.now().isoformat(),
        }


def create_planning_engine(db_path: str | None = None) -> PlanningEngine:
    """
    创建规划引擎实例

    Args:
        db_path: 数据库路径

    Returns:
        规划引擎实例
    """
    return PlanningEngine(db_path)
