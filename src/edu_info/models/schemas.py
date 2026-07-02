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
    
    # 1. 基础信息与沿革
    english_name: str | None = None
    abbreviation_cn: str | None = None
    english_abbr: str | None = None
    moe_code: str | None = None
    founded_year: int | None = None
    historical_names: list[str] = []
    website_official: str | None = None
    website_admissions: str | None = None
    postal_address: str | None = None
    postal_code: str | None = None
    contact_phone: str | None = None
    governing_body: str | None = None
    ownership_type: str | None = None
    city_level: str | None = None
    industry_tags: list[str] = []
    
    # 2. 招生录取限制
    subject_prereq_first: str | None = None
    subject_prereq_second: list[str] = []
    limit_color_blind: list[str] = []
    limit_color_weak: list[str] = []
    limit_sight_single: list[str] = []
    english_min_limit: dict[str, Any] = {}
    math_min_limit: dict[str, Any] = {}
    gender_ratio_limit: str | None = None
    accepted_languages: list[str] = []
    
    # 3. 学科与学术实力
    discipline_eval_grade: dict[str, str] = {}
    phd_first_level_count: int = 0
    master_first_level_cnt: int = 0
    double_first_class_maj: list[str] = []
    national_first_class_m: list[str] = []
    provincial_first_class: list[str] = []
    engineering_accredited: list[str] = []
    national_key_discipl: list[str] = []
    
    # 4. 费用与生活成本
    tuition_liberal_arts: int | None = None
    tuition_science: int | None = None
    tuition_engineering: int | None = None
    tuition_medical: int | None = None
    tuition_art: int | None = None
    tuition_escalations: dict[str, list[int]] = {}
    jv_domestic_fee_yr: int | None = None
    jv_abroad_fee_yr: int | None = None
    accommodation_tiers: dict[str, int] = {}
    city_living_cost_est: int | None = None
    
    # 5. 高质量就业与去向
    baoyan_rate: float | None = None
    overall_employment_rt: float | None = None
    postgrad_domestic_rt: float | None = None
    abroad_study_rate: float | None = None
    selection_officer_tier: str | None = None
    soe_placement_rate: float | None = None
    civil_service_rate: float | None = None
    fortune_500_placement: float | None = None
    top_employers_list: list[str] = []
    
    # 6. 底蕴名片与背景
    cas_cae_members_alumni: int = 0
    key_labs_national: list[str] = []
    famous_alumni_reps: list[str] = []
    engineering_centers_n: list[str] = []
    description: str | None = None

    # 兼容嵌套字典字段
    tuition_rules: dict[str, Any] = {}
    admission_constraints: dict[str, Any] = {}
    career_metrics: dict[str, Any] = {}
    academic_accreditations: dict[str, Any] = {}
    major_tuition_fees: dict[str, int] = {}
    appraisal_ratings: dict[str, float] = {}
    
    # 兼容旧版本平铺字段
    discipline_evaluations: dict[str, str] = {}
    doctorate_points: int = 0
    master_points: int = 0
    accommodation_fee: int | None = None
    overall_employment_rate: float | None = None
    postgraduate_rate: float | None = None
    abroad_rate: float | None = None
    key_employers: list[str] = []
    key_labs: list[str] = []
    famous_alumni: list[str] = []


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
    
    # 身体条件限制（健康指标）
    color_blind: bool = False
    color_weak: bool = False

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
