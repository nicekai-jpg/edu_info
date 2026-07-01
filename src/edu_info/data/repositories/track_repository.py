"""
赛道数据仓库

基于 Code Craft 原则：
- 单一职责：仅负责 CRUD 操作，无业务逻辑
- 封装：隐藏数据库访问细节
"""

from pathlib import Path
from typing import Any

import duckdb

from ...models.track import (
    Domain,
    MajorCategory,
    StudentTrackMatch,
    Track,
    TrackEmploymentInfo,
    TrackRequirements,
)


def get_db_path() -> Path:
    """计算数据库路径"""
    # 从 repositories/ 回到项目根目录
    current = Path(__file__).resolve()
    for _ in range(5):  # repositories/xxx.py → project root
        current = current.parent
    return current / "data" / "edu_planning.db"


class TrackRepository:
    """赛道数据仓库 - 只负责 CRUD"""

    def __init__(self, db_path: Path | None = None):
        """初始化数据库连接"""
        self.db_path = db_path or get_db_path()

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """获取数据库连接"""
        return duckdb.connect(str(self.db_path))

    # ==================== Domain 相关操作 ====================

    def get_all_domains(self) -> list[Domain]:
        """获取所有领域"""
        conn = self._get_connection()
        try:
            result = conn.execute("""
                SELECT domain_id, domain_name, description, lifecycle_stage,
                       strategic_importance, created_at, updated_at
                FROM domains
                ORDER BY strategic_importance DESC
            """).fetchall()

            return [
                Domain(
                    domain_id=row[0],
                    domain_name=row[1],
                    description=row[2],
                    lifecycle_stage=row[3],
                    strategic_importance=float(row[4]) if row[4] else None,
                    created_at=row[5],
                    updated_at=row[6]
                )
                for row in result
            ]
        finally:
            conn.close()

    def get_domain_by_id(self, domain_id: int) -> Domain | None:
        """根据 ID 获取领域"""
        conn = self._get_connection()
        try:
            result = conn.execute("""
                SELECT domain_id, domain_name, description, lifecycle_stage,
                       strategic_importance, created_at, updated_at
                FROM domains
                WHERE domain_id = ?
            """, [domain_id]).fetchone()

            if result:
                return Domain(
                    domain_id=result[0],
                    domain_name=result[1],
                    description=result[2],
                    lifecycle_stage=result[3],
                    strategic_importance=float(result[4]) if result[4] else None,
                    created_at=result[5],
                    updated_at=result[6]
                )
            return None
        finally:
            conn.close()

    # ==================== Track 相关操作 ====================

    def get_all_tracks(self) -> list[Track]:
        """获取所有赛道"""
        conn = self._get_connection()
        try:
            result = conn.execute("""
                SELECT track_id, track_name, description, lifecycle_stage,
                       created_at, updated_at
                FROM tracks
                ORDER BY track_id
            """).fetchall()

            tracks = [
                Track(
                    track_id=row[0],
                    track_name=row[1],
                    description=row[2],
                    lifecycle_stage=row[3],
                    created_at=row[4],
                    updated_at=row[5]
                )
                for row in result
            ]

            # 加载每个赛道的关联领域
            for track in tracks:
                track.domains = self.get_track_domains(track.track_id)
                track.employment_info = self.get_track_employment_info(track.track_id)
                track.requirements = self.get_track_requirements(track.track_id)

            return tracks
        finally:
            conn.close()

    def get_track_by_id(self, track_id: int) -> Track | None:
        """根据 ID 获取赛道"""
        conn = self._get_connection()
        try:
            result = conn.execute("""
                SELECT track_id, track_name, description, lifecycle_stage,
                       created_at, updated_at
                FROM tracks
                WHERE track_id = ?
            """, [track_id]).fetchone()

            if not result:
                return None

            track = Track(
                track_id=result[0],
                track_name=result[1],
                description=result[2],
                lifecycle_stage=result[3],
                created_at=result[4],
                updated_at=result[5]
            )

            # 加载关联数据
            track.domains = self.get_track_domains(track_id)
            track.employment_info = self.get_track_employment_info(track_id)
            track.requirements = self.get_track_requirements(track_id)

            return track
        finally:
            conn.close()

    def get_tracks_by_domain(self, domain_id: int) -> list[Track]:
        """根据领域 ID 获取赛道"""
        conn = self._get_connection()
        try:
            # 先获取赛道 ID 列表
            results = conn.execute("""
                SELECT track_id
                FROM track_domain_mapping
                WHERE domain_id = ?
            """, [domain_id]).fetchall()

            track_ids = [row[0] for row in results]

            if not track_ids:
                return []

            # 批量获取赛道
            placeholders = ','.join(['?' for _ in track_ids])
            tracks_result = conn.execute(f"""
                SELECT track_id, track_name, description, lifecycle_stage,
                       created_at, updated_at
                FROM tracks
                WHERE track_id IN ({placeholders})
            """, track_ids).fetchall()

            tracks = [
                Track(
                    track_id=row[0],
                    track_name=row[1],
                    description=row[2],
                    lifecycle_stage=row[3],
                    created_at=row[4],
                    updated_at=row[5]
                )
                for row in tracks_result
            ]

            # 加载关联数据
            for track in tracks:
                track.domains = self.get_track_domains(track.track_id)
                track.employment_info = self.get_track_employment_info(track.track_id)
                track.requirements = self.get_track_requirements(track.track_id)

            return tracks
        finally:
            conn.close()

    def get_track_domains(self, track_id: int) -> list[Domain]:
        """获取赛道关联的领域"""
        conn = self._get_connection()
        try:
            results = conn.execute("""
                SELECT d.domain_id, d.domain_name, d.description, d.lifecycle_stage,
                       d.strategic_importance, d.created_at, d.updated_at
                FROM domains d
                INNER JOIN track_domain_mapping m ON d.domain_id = m.domain_id
                WHERE m.track_id = ?
                ORDER BY m.is_primary DESC
            """, [track_id]).fetchall()

            return [
                Domain(
                    domain_id=row[0],
                    domain_name=row[1],
                    description=row[2],
                    lifecycle_stage=row[3],
                    strategic_importance=float(row[4]) if row[4] else None,
                    created_at=row[5],
                    updated_at=row[6]
                )
                for row in results
            ]
        finally:
            conn.close()

    def get_track_employment_info(self, track_id: int) -> TrackEmploymentInfo | None:
        """获取赛道就业信息"""
        conn = self._get_connection()
        try:
            import json
            result = conn.execute("""
                SELECT track_id, typical_positions, salary_ranges, typical_companies,
                       company_types, employment_rate, avg_salary, data_source,
                       confidence_level, updated_at
                FROM track_employment_info
                WHERE track_id = ?
            """, [track_id]).fetchone()

            if not result:
                return None

            return TrackEmploymentInfo(
                track_id=result[0],
                typical_positions=json.loads(result[1]) if result[1] else [],
                salary_ranges=json.loads(result[2]) if result[2] else {},
                typical_companies=json.loads(result[3]) if result[3] else [],
                company_types=json.loads(result[4]) if result[4] else [],
                employment_rate=float(result[5]) if result[5] else None,
                avg_salary=float(result[6]) if result[6] else None,
                data_source=result[7],
                confidence_level=result[8],
                updated_at=result[9]
            )
        finally:
            conn.close()

    def get_track_requirements(self, track_id: int) -> TrackRequirements | None:
        """获取赛道能力要求"""
        conn = self._get_connection()
        try:
            import json
            result = conn.execute("""
                SELECT track_id, required_skills, score_requirements, preferred_subjects
                FROM track_requirements
                WHERE track_id = ?
            """, [track_id]).fetchone()

            if not result:
                return None

            return TrackRequirements(
                track_id=result[0],
                required_skills=json.loads(result[1]) if result[1] else [],
                score_requirements=json.loads(result[2]) if result[2] else {},
                preferred_subjects=json.loads(result[3]) if result[3] else []
            )
        finally:
            conn.close()

    # ==================== MajorCategory 相关操作 ====================

    def get_all_major_categories(self) -> list[MajorCategory]:
        """获取所有专业类别"""
        conn = self._get_connection()
        try:
            import json
            result = conn.execute("""
                SELECT category_id, category_name, domain_id, education_code,
                       description, core_courses, created_at, updated_at
                FROM major_categories
                ORDER BY category_id
            """).fetchall()

            return [
                MajorCategory(
                    category_id=row[0],
                    category_name=row[1],
                    domain_id=row[2],
                    education_code=row[3],
                    description=row[4],
                    core_courses=json.loads(row[5]) if row[5] else [],
                    created_at=row[6],
                    updated_at=row[7]
                )
                for row in result
            ]
        finally:
            conn.close()

    def get_track_categories(self, track_id: int) -> list[MajorCategory]:
        """获取赛道关联的专业类别"""
        conn = self._get_connection()
        try:
            import json
            results = conn.execute("""
                SELECT c.category_id, c.category_name, c.domain_id, c.education_code,
                       c.description, c.core_courses, c.created_at, c.updated_at,
                       m.mapping_type, m.shared_courses_ratio, m.conversion_cost, m.skill_gap
                FROM major_categories c
                INNER JOIN track_category_mapping m ON c.category_id = m.category_id
                WHERE m.track_id = ?
                ORDER BY
                    CASE m.mapping_type
                        WHEN '核心' THEN 1
                        WHEN '相关' THEN 2
                        ELSE 3
                    END
            """, [track_id]).fetchall()

            return [
                MajorCategory(
                    category_id=row[0],
                    category_name=row[1],
                    domain_id=row[2],
                    education_code=row[3],
                    description=row[4],
                    core_courses=json.loads(row[5]) if row[5] else [],
                    created_at=row[6],
                    updated_at=row[7]
                )
                for row in results
            ]
        finally:
            conn.close()

    # ==================== TrackCategoryMapping 相关操作 ====================

    def get_track_category_mapping(self, track_id: int, category_id: int) -> dict[str, Any] | None:
        """获取赛道 - 专业类别映射详情"""
        conn = self._get_connection()
        try:
            import json
            result = conn.execute("""
                SELECT track_id, category_id, mapping_type, shared_courses_ratio,
                       conversion_cost, skill_gap, created_at
                FROM track_category_mapping
                WHERE track_id = ? AND category_id = ?
            """, [track_id, category_id]).fetchone()

            if not result:
                return None

            return {
                'track_id': result[0],
                'category_id': result[1],
                'mapping_type': result[2],
                'shared_courses_ratio': float(result[3]) if result[3] else None,
                'conversion_cost': result[4],
                'skill_gap': json.loads(result[5]) if result[5] else [],
                'created_at': result[6]
            }
        finally:
            conn.close()

    # ==================== 匹配结果相关操作 ====================

    def save_student_track_match(self, match: StudentTrackMatch) -> None:
        """保存学生 - 赛道匹配结果"""
        conn = self._get_connection()
        try:
            import json
            conn.execute("""
                INSERT OR REPLACE INTO student_track_matches
                (match_id, student_id, track_id, match_score,
                 interest_score, ability_score, economic_score,
                 time_score, regional_score, match_reasons,
                 gaps, action_items, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                match.match_id,
                match.student_id,
                match.track_id,
                match.match_score,
                match.interest_score,
                match.ability_score,
                match.economic_score,
                match.time_score,
                match.regional_score,
                json.dumps(match.match_reasons) if match.match_reasons else None,
                json.dumps(match.gaps) if match.gaps else None,
                json.dumps(match.action_items) if match.action_items else None,
                match.generated_at
            ])
        finally:
            conn.close()

    def get_student_matches(self, student_id: int) -> list[StudentTrackMatch]:
        """获取学生的所有匹配结果"""
        conn = self._get_connection()
        try:
            import json
            results = conn.execute("""
                SELECT match_id, student_id, track_id, match_score,
                       interest_score, ability_score, economic_score,
                       time_score, regional_score, match_reasons,
                       gaps, action_items, generated_at
                FROM student_track_matches
                WHERE student_id = ?
                ORDER BY match_score DESC
            """, [student_id]).fetchall()

            return [
                StudentTrackMatch(
                    match_id=row[0],
                    student_id=row[1],
                    track_id=row[2],
                    match_score=float(row[3]),
                    interest_score=float(row[4]) if row[4] else None,
                    ability_score=float(row[5]) if row[5] else None,
                    economic_score=float(row[6]) if row[6] else None,
                    time_score=float(row[7]) if row[7] else None,
                    regional_score=float(row[8]) if row[8] else None,
                    match_reasons=json.loads(row[9]) if row[9] else {},
                    gaps=json.loads(row[10]) if row[10] else [],
                    action_items=json.loads(row[11]) if row[11] else [],
                    generated_at=row[12]
                )
                for row in results
            ]
        finally:
            conn.close()
