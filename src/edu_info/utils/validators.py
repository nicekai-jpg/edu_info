"""
验证模块

使用 pydantic 进行严格的数据验证，确保输入数据质量
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StudentProfile(BaseModel):
    """学生档案数据模型"""

    model_config = ConfigDict(extra="forbid")  # 禁止额外字段

    name: str = Field(..., min_length=1, max_length=64, description="学生姓名")
    current_grade: str = Field(
        ...,
        pattern=r"^(初一|初二|初三|高一|高二|高三)$",
        description="当前年级"
    )
    school: str | None = Field(None, max_length=128, description="学校名称")
    city: str = Field(..., description="城市")

    # 成绩字典，每科 0-150 分
    scores: dict[str, float] | None = Field(
        default=None,
        description="各科成绩"
    )
    overall_level: str | None = Field(
        None,
        pattern=r"^(A\+|A|B\+|B|C)$",
        description="综合等级"
    )

    # 兴趣列表
    interests: list[str] | None = Field(default=None, description="兴趣领域")

    # 特长列表
    special_talents: list[str] | None = Field(default=None, description="特长")

    # 竞赛获奖
    competitions: list[str] | None = Field(default=None, description="竞赛获奖")

    # 家庭年收入（万元）
    family_income: float | None = Field(
        default=None,
        gt=0,
        description="家庭年收入（万元）"
    )

    # 偏好地区
    preferred_regions: list[str] | None = Field(default=None, description="偏好地区")

    # 约束条件
    constraints: dict | None = Field(default=None, description="约束条件")

    @field_validator("scores")
    @classmethod
    def validate_scores(cls, v):
        """验证分数范围"""
        if v is None:
            return v

        for subject, score in v.items():
            if not (0 <= score <= 150):
                raise ValueError(f"科目 {subject} 的分数 {score} 超出范围 (0-150)")

        return v


class AdmissionScoreData(BaseModel):
    """高校录取分数数据模型"""

    model_config = ConfigDict(extra="forbid")

    university_id: int = Field(..., gt=0, description="高校 ID")
    major_id: int = Field(..., gt=0, description="专业 ID")
    year: int = Field(
        ...,
        ge=2020,
        le=datetime.now().year + 1,
        description="年份（2020-当前年份 +1）"
    )
    admission_type: str = Field(
        default="统招",
        pattern=r"^(统招|艺术|体育|强基|综评|专项计划)$",
        description="招生类型"
    )
    subject_type: str = Field(
        ...,
        pattern=r"^(物理类|历史类|综合)$",
        description="科目类型"
    )
    batch: str | None = Field(
        default="本科批",
        description="录取批次"
    )

    # 分数（0-750）
    min_score: int | None = Field(
        default=None,
        ge=0,
        le=750,
        description="最低分"
    )
    avg_score: int | None = Field(
        default=None,
        ge=0,
        le=750,
        description="平均分"
    )
    max_score: int | None = Field(
        default=None,
        ge=0,
        le=750,
        description="最高分"
    )

    # 位次（必须为正整数）
    min_rank: int | None = Field(
        default=None,
        gt=0,
        description="最低位次"
    )
    avg_rank: int | None = Field(
        default=None,
        gt=0,
        description="平均位次"
    )

    # 招生计划
    enrollment_plan: int | None = Field(
        default=None,
        ge=0,
        description="招生计划人数"
    )

    # 数据来源
    source_url: str | None = Field(default=None, description="数据来源 URL")


class UniversityData(BaseModel):
    """高校信息数据模型"""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=2, max_length=128, description="高校名称")
    code: str | None = Field(default=None, max_length=20, description="高校代码")
    province: str = Field(..., description="所在省份")
    city: str = Field(..., description="所在城市")
    level: str = Field(
        default="普通",
        pattern=r"^(985|211|双一流|普通)$",
        description="高校层次"
    )
    type: str = Field(
        default="综合",
        pattern=r"^(综合|理工|师范|医药|财经|农林|林业|军事)$",
        description="高校类型"
    )
    is_985: bool = Field(default=False, description="是否 985 高校")
    is_211: bool = Field(default=False, description="是否 211 高校")
    is_double_first_class: bool = Field(default=False, description="是否双一流高校")


# ========== 验证函数 ==========

def validate_student_profile(data: dict) -> StudentProfile:
    """
    验证学生档案数据

    Args:
        data: 学生档案字典数据

    Returns:
        验证通过的 StudentProfile 对象

    Raises:
        pydantic.ValidationError: 验证失败时抛出
    """
    return StudentProfile.model_validate(data)


def validate_score_data(data: dict) -> AdmissionScoreData:
    """
    验证分数线数据

    Args:
        data: 分数线字典数据

    Returns:
        验证通过的 AdmissionScoreData 对象

    Raises:
        pydantic.ValidationError: 验证失败时抛出
    """
    return AdmissionScoreData.model_validate(data)


def validate_university_data(data: dict) -> UniversityData:
    """
    验证高校信息数据

    Args:
        data: 高校信息字典数据

    Returns:
        验证通过的 UniversityData 对象

    Raises:
        pydantic.ValidationError: 验证失败时抛出
    """
    return UniversityData.model_validate(data)
