"""
数据库模块测试
"""

import tempfile
from pathlib import Path


class TestDatabase:
    """数据库操作测试"""

    def test_database_creation(self, temp_db):
        """测试数据库创建"""
        # 验证数据库连接成功
        result = temp_db.execute("SELECT 1").fetchone()
        assert result[0] == 1

    def test_create_tables(self):
        """测试数据表创建"""
        from edu_info.database.database import Database

        # 创建临时数据库路径
        db_path = tempfile.mktemp(suffix=".duckdb")

        try:
            db = Database(db_path)

            # 验证表已创建
            tables = db.conn.execute(
                "SHOW TABLES"
            ).fetchall()

            # 应该创建所有必要的表
            table_names = [t[0] for t in tables]
            assert "universities" in table_names
            assert "majors" in table_names
            assert "admission_scores" in table_names
            assert "planning_routes" in table_names
            assert "student_profiles" in table_names

            db.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_insert_university(self, sample_university_data):
        """测试插入高校数据"""
        from edu_info.database.database import Database

        # 创建临时数据库路径
        db_path = tempfile.mktemp(suffix=".duckdb")

        try:
            db = Database(db_path)

            # 插入测试数据
            db.insert("universities", sample_university_data[0])

            # 验证数据已插入
            result = db.query(
                "SELECT * FROM universities WHERE university_id = ?",
                (1,)
            )
            assert len(result) == 1
            assert result[0][1] == "清华大学"

            db.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_query_as_dataframe(self, sample_university_data):
        """测试 DataFrame 查询"""
        from edu_info.database.database import Database

        # 创建临时数据库路径
        db_path = tempfile.mktemp(suffix=".duckdb")

        try:
            db = Database(db_path)
            db.insert("universities", sample_university_data[0])

            # 查询为 DataFrame
            df = db.query_df("SELECT * FROM universities")

            assert len(df) == 1
            assert df.iloc[0]["name"] == "清华大学"

            db.close()
        finally:
            Path(db_path).unlink(missing_ok=True)
