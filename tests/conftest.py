"""
Pytest 配置文件
包含通用 fixture 和测试工具
"""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录"""
    return Path(__file__).parent / "data"


@pytest.fixture
def temp_db():
    """创建临时数据库用于测试"""
    import duckdb

    # 创建临时文件路径（不预先创建文件）
    db_path = tempfile.mktemp(suffix=".duckdb")

    # 直接连接到新数据库
    conn = duckdb.connect(db_path)
    yield conn
    conn.close()

    # 清理临时文件
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_university_data():
    """示例高校数据"""
    return [
        {
            "university_id": 1,
            "name": "清华大学",
            "code": "10003",
            "province": "北京",
            "city": "北京",
            "level": "985",
            "type": "综合",
            "is_985": True,
            "is_211": True,
            "is_double_first_class": True,
        },
        {
            "university_id": 2,
            "name": "北京大学",
            "code": "10001",
            "province": "北京",
            "city": "北京",
            "level": "985",
            "type": "综合",
            "is_985": True,
            "is_211": True,
            "is_double_first_class": True,
        },
    ]


@pytest.fixture
def sample_score_data():
    """示例分数线数据"""
    return [
        {
            "score_id": 1,
            "university_id": 1,
            "major_id": 1,
            "year": 2024,
            "admission_type": "统招",
            "subject_type": "物理类",
            "batch": "本科批",
            "min_score": 680,
            "min_rank": 100,
        },
        {
            "score_id": 2,
            "university_id": 2,
            "major_id": 2,
            "year": 2024,
            "admission_type": "统招",
            "subject_type": "物理类",
            "batch": "本科批",
            "min_score": 675,
            "min_rank": 150,
        },
    ]


@pytest.fixture
def sample_student_profile():
    """示例学生档案"""
    return {
        "name": "张三",
        "current_grade": "高一",
        "school": "辽宁省实验中学",
        "city": "沈阳",
        "scores": {
            "语文": 120,
            "数学": 135,
            "英语": 130,
            "物理": 85,
            "化学": 80,
            "生物": 75,
        },
        "overall_level": "A",
        "interests": ["计算机", "人工智能", "数学"],
        "special_talents": ["信息学奥赛省级一等奖"],
        "family_income": 300000,
        "preferred_regions": ["北京", "上海", "广东"],
    }
