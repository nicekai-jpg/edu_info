"""
验证模块测试
"""

import pytest
from pydantic import ValidationError

from edu_info.utils.validators import validate_score_data, validate_student_profile


class TestStudentProfileValidation:
    """学生档案验证测试"""

    def test_valid_profile(self, sample_student_profile):
        """测试有效的学生档案"""
        # 应该不抛出异常
        result = validate_student_profile(sample_student_profile)
        assert result is not None
        assert result.name == "张三"
        assert result.current_grade == "高一"

    def test_invalid_grade(self):
        """测试无效年级"""
        profile = {
            "name": "李四",
            "current_grade": "三年级",  # 无效值
            "school": "某中学",
            "city": "沈阳",
        }

        with pytest.raises(ValidationError):
            validate_student_profile(profile)

    def test_missing_required_field(self):
        """测试缺少必填字段"""
        profile = {
            "name": "王五",
            # 缺少 current_grade
            "school": "某中学",
        }

        with pytest.raises(ValidationError):
            validate_student_profile(profile)

    def test_score_range(self, sample_student_profile):
        """测试分数范围验证"""
        # 修改为超出范围的分数
        profile = sample_student_profile.copy()
        profile["scores"]["数学"] = 200  # 超出 150 分

        with pytest.raises(ValidationError):
            validate_student_profile(profile)


class TestScoreDataValidation:
    """分数线数据验证测试"""

    def test_valid_score_data(self):
        """测试有效的分数线数据"""
        score_data = {
            "university_id": 1,
            "major_id": 1,
            "year": 2024,
            "admission_type": "统招",
            "subject_type": "物理类",
            "batch": "本科批",
            "min_score": 650,
            "min_rank": 1000,
        }

        result = validate_score_data(score_data)
        assert result is not None
        assert result.year == 2024
        assert result.min_score == 650

    def test_invalid_year(self):
        """测试无效年份"""
        score_data = {
            "university_id": 1,
            "major_id": 1,
            "year": 2015,  # 超出范围
            "admission_type": "统招",
            "subject_type": "物理类",
            "min_score": 650,
        }

        with pytest.raises(ValidationError):
            validate_score_data(score_data)

    def test_invalid_score(self):
        """测试无效分数"""
        score_data = {
            "university_id": 1,
            "major_id": 1,
            "year": 2024,
            "admission_type": "统招",
            "subject_type": "物理类",
            "min_score": 800,  # 超出 750 分
        }

        with pytest.raises(ValidationError):
            validate_score_data(score_data)

    def test_rank_must_be_positive(self):
        """测试位次必须为正数"""
        score_data = {
            "university_id": 1,
            "major_id": 1,
            "year": 2024,
            "admission_type": "统招",
            "subject_type": "物理类",
            "min_score": 650,
            "min_rank": -100,  # 负数
        }

        with pytest.raises(ValidationError):
            validate_score_data(score_data)
