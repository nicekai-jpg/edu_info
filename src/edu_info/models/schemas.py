"""
数据模型定义

使用 Pydantic 进行数据验证和序列化
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class University(BaseModel):
    """高校信息模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    location: str
    type: str = "综合"
    is_985: bool = False
    is_211: bool = False
    is_double_first_class: bool = False
    project_type: str | None = None
    ownership: str | None = None
    tuition_fee: int | None = None


class Major(BaseModel):
    """专业信息模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    university_id: int
    name: str
    code: str | None = None
    category: str | None = None
    degree: str | None = None


class Student(BaseModel):
    """学生档案模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    student_code: str
    name: str
    grade: str  # 初一/初二/初三/高一/高二/高三
    school: str | None = None
    city: str
    category: str  # 物理类/历史类
    total_score: float | None = None
    ranking: int | None = None

    # 单科成绩
    chinese_score: float | None = None
    math_score: float | None = None
    english_score: float | None = None
    other_scores: dict[str, Any] | None = None

    # 兴趣特长
    interests: list[str] | None = None
    specialities: list[str] | None = None
    awards: list[dict[str, Any]] | None = None

    # 选考科目组合
    subjects: list[str] | None = None

    # 家庭情况
    family_budget: float | None = None
    preferred_locations: list[str] | None = None
    constraints: dict[str, Any] | None = None

    planning_status: str = "未开始"


class PlanningRoute(BaseModel):
    """升学路线模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    route_id: str  # 唯一标识，如 "gaokao_985_cs"
    route_name: str  # 如 "985 高校 - 计算机专业"
    route_type: str  # 普通高考/强基计划/科技特长生/等
    category: str  # 路线类别

    # 路线详情
    description: str = ""
    stages: list[dict[str, Any]] | None = None  # 阶段规划
    requirements: dict[str, Any] | None = None  # 要求条件
    timeline: dict[str, Any] | None = None  # 时间安排

    # 目标高校类型
    target_university_types: list[str] | None = None
    target_major_types: list[str] | None = None

    # 成本估算（万元）
    cost_min: float | None = None
    cost_max: float | None = None

    # 难度和成功率
    difficulty: str = "中等"  # 低/中等/高/极高
    success_rate: str | None = None

    # 关联政策
    related_policies: list[str] | None = None


class RouteMatch(BaseModel):
    """路线匹配结果模型"""
    model_config = ConfigDict(from_attributes=True)

    route: PlanningRoute
    match_score: float  # 总分 0-100

    # 各维度匹配度
    interest_score: float = 0.0  # 兴趣匹配 (40%)
    ability_score: float = 0.0  # 能力匹配 (25%)
    economic_score: float = 0.0  # 经济匹配 (20%)
    time_score: float = 0.0  # 时间匹配 (10%)
    region_score: float = 0.0  # 地域匹配 (5%)

    # 评估
    feasibility_score: float | None = None
    risk_level: str | None = None
    recommendations: list[str] | None = None


class TargetUniversity(BaseModel):
    """目标高校模型（三档目标）"""
    model_config = ConfigDict(from_attributes=True)

    university: University
    target_type: str  # 高目标/中目标/低目标
    major: str | None = None

    # 录取数据
    min_score: int | None = None
    min_rank: int | None = None
    year: int | None = None

    # 达成概率
    probability: float | None = None  # 0-100%

    # 分析
    analysis: str | None = None
    recommendations: list[str] | None = None


class PlanningResult(BaseModel):
    """规划结果模型"""
    model_config = ConfigDict(from_attributes=True)

    student_id: int
    created_at: datetime = Field(default_factory=datetime.now)

    # 推荐路线（Top 10）
    top_routes: list[RouteMatch] = []

    # 三档目标
    high_targets: list[TargetUniversity] = []  # 冲刺目标
    medium_targets: list[TargetUniversity] = []  # 稳妥目标
    low_targets: list[TargetUniversity] = []  # 保底目标

    # 可行性评估
    overall_feasibility: float | None = None
    risk_assessment: str | None = None

    # 建议
    summary: str | None = None
    action_items: list[str] | None = None
