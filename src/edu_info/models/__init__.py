"""数据模型模块"""

from .schemas import (
    Major,
    PlanningRoute,
    RouteMatch,
    Student,
    TargetUniversity,
    University,
)
from .schemas import (
    PlanningResult as SchemaPlanningResult,
)
from .track import (
    Domain,
    MajorCategory,
    Policy,
    StudentTrackMatch,
    Track,
    TrackCategoryMapping,
    TrackDomainMapping,
    TrackEmploymentInfo,
    TrackPolicyMapping,
    TrackRequirements,
    TrackUniversityCompetitiveness,
)
from .track import (
    PlanningResult as TrackPlanningResult,
)

__all__ = [
    # 原有模型
    'Student',
    'University',
    'Major',
    'PlanningRoute',
    'RouteMatch',
    'TargetUniversity',
    'SchemaPlanningResult',

    # 赛道模型
    'Domain',
    'Track',
    'MajorCategory',
    'TrackDomainMapping',
    'TrackCategoryMapping',
    'TrackEmploymentInfo',
    'TrackRequirements',
    'TrackPolicyMapping',
    'TrackUniversityCompetitiveness',
    'StudentTrackMatch',
    'Policy',
    'TrackPlanningResult',
]
