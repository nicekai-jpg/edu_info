"""
赛道模型定义

基于 Code Craft 原则：
- 封装：私有字段 + 只读属性 + 验证方法
- 单一职责：仅定义数据结构，不包含业务逻辑
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class Domain(BaseModel):
    """领域实体"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    domain_id: int
    domain_name: str
    description: str | None = None
    lifecycle_stage: str | None = None  # 新兴/成长/成熟/转型
    strategic_importance: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MajorCategory(BaseModel):
    """专业类别实体"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    category_id: int
    category_name: str
    domain_id: int
    education_code: str | None = None
    description: str | None = None
    core_courses: list[str] | None = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Track(BaseModel):
    """赛道实体 - 封装状态"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    track_id: int
    track_name: str
    description: str | None = None
    lifecycle_stage: str | None = None  # 新兴/成长/成熟
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # 关联数据（延迟加载）
    domains: list[Domain] = Field(default_factory=list)
    employment_info: Optional['TrackEmploymentInfo'] = None
    requirements: Optional['TrackRequirements'] = None


class TrackDomainMapping(BaseModel):
    """赛道 - 领域映射"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    track_id: int
    domain_id: int
    is_primary: bool = False
    created_at: datetime | None = None


class TrackCategoryMapping(BaseModel):
    """赛道 - 专业类别映射"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    track_id: int
    category_id: int
    mapping_type: str  # 核心/相关/边缘
    shared_courses_ratio: float | None = None
    conversion_cost: str | None = None  # 低/中/高
    skill_gap: list[str] | None = Field(default_factory=list)
    created_at: datetime | None = None


class TrackEmploymentInfo(BaseModel):
    """赛道就业信息"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    track_id: int
    typical_positions: list[str] = Field(default_factory=list)
    salary_ranges: dict[str, str] = Field(default_factory=dict)
    typical_companies: list[str] | None = Field(default_factory=list)
    company_types: list[str] | None = Field(default_factory=list)
    employment_rate: float | None = None
    avg_salary: float | None = None
    data_source: str | None = None
    confidence_level: str | None = None  # 高/中/低
    updated_at: datetime | None = None

    def get_salary_range(self, years: int) -> str:
        """根据年限获取薪资范围 - 封装行为"""
        if not self.salary_ranges:
            return "暂无数据"

        if years <= 3:
            return self.salary_ranges.get("1-3 年", "暂无数据")
        elif years <= 5:
            return self.salary_ranges.get("3-5 年", "暂无数据")
        else:
            return self.salary_ranges.get("5 年以上", "暂无数据")


class TrackRequirements(BaseModel):
    """赛道能力要求"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    track_id: int
    required_skills: list[str] = Field(default_factory=list)
    score_requirements: dict[str, int] = Field(default_factory=dict)
    preferred_subjects: list[str] | None = Field(default_factory=list)


class TrackPolicyMapping(BaseModel):
    """赛道 - 政策映射"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    track_id: int
    policy_id: int
    policy_name: str
    policy_level: str | None = None  # 国家/省级
    support_type: str | None = None  # 资金/人才/平台
    impact_score: float | None = None
    document_url: str | None = None
    created_at: datetime | None = None


class TrackUniversityCompetitiveness(BaseModel):
    """赛道 - 院校竞争力"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    track_id: int
    university_id: int
    category_id: int
    competitiveness_level: str | None = None  # A+/A/B+/B
    track_ranking: int | None = None

    discipline_grade: str | None = None  # 学科评估
    research_score: float | None = None
    industry_score: float | None = None
    employment_score: float | None = None
    alumni_score: float | None = None
    overall_score: float | None = None

    employment_rate: float | None = None
    avg_salary: float | None = None
    typical_employers: list[str] | None = Field(default_factory=list)

    data_year: int = 2025
    created_at: datetime | None = None


class StudentTrackMatch(BaseModel):
    """学生 - 赛道匹配结果"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    match_id: int
    student_id: int
    track_id: int
    match_score: float

    interest_score: float | None = None
    ability_score: float | None = None
    economic_score: float | None = None
    time_score: float | None = None
    regional_score: float | None = None

    match_reasons: dict[str, Any] | None = Field(default_factory=dict)
    gaps: list[dict[str, Any]] | None = Field(default_factory=list)
    action_items: list[str] | None = Field(default_factory=list)

    generated_at: datetime | None = None


class Policy(BaseModel):
    """政策文件"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    policy_id: int
    title: str
    doc_number: str | None = None
    issuer: str | None = None
    issue_date: datetime | None = None
    category: str | None = None  # 高考改革/特长生/强基计划等
    level: str | None = None  # 国家级/省级/市级
    content: str | None = None
    summary: str | None = None
    keywords: list[str] | None = Field(default_factory=list)
    related_routes: list[str] | None = Field(default_factory=list)
    created_at: datetime | None = None


class PlanningResult(BaseModel):
    """规划结果存储"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    result_id: int
    student_id: int
    version_id: str
    generated_at: datetime | None = None
    data_version: str | None = None

    top_routes: list[dict[str, Any]] | None = Field(default_factory=list)
    targets_data: dict[str, Any] | None = Field(default_factory=dict)
    feasibility_data: dict[str, Any] | None = Field(default_factory=dict)
    match_details: dict[str, Any] | None = Field(default_factory=dict)

    change_summary: str | None = None
    is_latest: bool = True
