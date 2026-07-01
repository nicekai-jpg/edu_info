"""
数据库模块

DuckDB 数据库连接和管理
"""

from pathlib import Path

import duckdb
import pandas as pd

from edu_info.utils.errors import DatabaseError, handle_errors
from edu_info.utils.logger import get_logger

logger = get_logger(__name__)


class Database:
    """DuckDB 数据库管理类"""

    # 数据库表 Schema
    TABLE_SCHEMAS = {
        "universities": """
            CREATE TABLE IF NOT EXISTS universities (
                university_id INTEGER PRIMARY KEY,
                name VARCHAR(128) NOT NULL,
                code VARCHAR(20),
                province VARCHAR(64),
                city VARCHAR(64),
                level VARCHAR(32),
                type VARCHAR(32),
                is_985 BOOLEAN,
                is_211 BOOLEAN,
                is_double_first_class BOOLEAN,
                tags VARCHAR(256),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,

        "majors": """
            CREATE TABLE IF NOT EXISTS majors (
                major_id INTEGER PRIMARY KEY,
                code VARCHAR(20),
                name VARCHAR(128) NOT NULL,
                category VARCHAR(64),
                degree_level VARCHAR(16),
                related_industries VARCHAR(512),
                prospects_rating INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,

        "admission_scores": """
            CREATE TABLE IF NOT EXISTS admission_scores (
                score_id BIGINT PRIMARY KEY,
                university_id INTEGER REFERENCES universities(university_id),
                major_id INTEGER REFERENCES majors(major_id),
                year INTEGER NOT NULL,
                admission_type VARCHAR(32),
                subject_type VARCHAR(16),
                batch VARCHAR(32),
                min_score INTEGER,
                avg_score INTEGER,
                max_score INTEGER,
                min_rank INTEGER,
                avg_rank INTEGER,
                enrollment_plan INTEGER,
                source_url VARCHAR(512),
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,

        "planning_routes": """
            CREATE TABLE IF NOT EXISTS planning_routes (
                route_id VARCHAR(64) PRIMARY KEY,
                category VARCHAR(64),
                name VARCHAR(128) NOT NULL,
                description TEXT,
                min_grade VARCHAR(16),
                max_grade VARCHAR(16),
                subject_requirements VARCHAR(256),
                talent_requirements VARCHAR(256),
                preparation_period VARCHAR(32),
                difficulty VARCHAR(16),
                success_rate VARCHAR(32),
                cost_min INTEGER,
                cost_max INTEGER,
                cost_items VARCHAR(512),
                target_university_types VARCHAR(256),
                target_major_types VARCHAR(256),
                related_policies VARCHAR(512),
                related_industries VARCHAR(512),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,

        "student_profiles": """
            CREATE TABLE IF NOT EXISTS student_profiles (
                profile_id VARCHAR(64) PRIMARY KEY,
                name VARCHAR(64),
                current_grade VARCHAR(16),
                school VARCHAR(128),
                city VARCHAR(64),
                scores VARCHAR(512),
                overall_level VARCHAR(8),
                interests VARCHAR(256),
                special_talents VARCHAR(256),
                competitions VARCHAR(512),
                family_income INTEGER,
                preferred_regions VARCHAR(256),
                constraints VARCHAR(512),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,

        "planning_results": """
            CREATE TABLE IF NOT EXISTS planning_results (
                result_id VARCHAR(64) PRIMARY KEY,
                profile_id VARCHAR(64) REFERENCES student_profiles(profile_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                routes_data TEXT,
                targets_data TEXT,
                feasibility_data TEXT,
                report_path VARCHAR(512)
            )
        """,
    }

    # 索引定义
    INDEX_SCHEMAS = [
        "CREATE INDEX IF NOT EXISTS idx_scores_query ON admission_scores(year, subject_type, admission_type, min_rank)",
        "CREATE INDEX IF NOT EXISTS idx_universities_level ON universities(level, province)",
        "CREATE INDEX IF NOT EXISTS idx_routes_category ON planning_routes(category)",
        "CREATE INDEX IF NOT EXISTS idx_profiles_city ON student_profiles(city)",
    ]

    def __init__(self, db_path: str | None = None):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径，默认 data/processed/edu_planning.duckdb
        """
        if db_path is None:
            # 使用默认路径
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = str(project_root / "data" / "processed" / "edu_planning.duckdb")

        self.db_path = Path(db_path)

        # 确保目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 连接数据库
        try:
            self.conn = duckdb.connect(str(self.db_path))
            logger.info(f"数据库连接成功：{self.db_path}")
        except Exception as e:
            logger.error(f"数据库连接失败：{e}")
            raise DatabaseError(
                message=f"无法连接数据库：{e}",
                operation="connect",
            ) from e

        # 初始化数据表
        self._init_tables()

    @handle_errors(DatabaseError)
    def _init_tables(self):
        """初始化所有数据表和索引"""
        logger.info("正在初始化数据表...")

        # 创建表
        for table_name, schema in self.TABLE_SCHEMAS.items():
            self.conn.execute(schema)
            logger.debug(f"表 {table_name} 创建成功")

        # 创建索引
        for index_schema in self.INDEX_SCHEMAS:
            self.conn.execute(index_schema)

        logger.info("数据表初始化完成")

    @handle_errors(DatabaseError)
    def query(self, sql: str, params: tuple | None = None) -> list:
        """
        执行 SQL 查询

        Args:
            sql: SQL 查询语句
            params: 参数元组

        Returns:
            查询结果列表
        """
        if params:
            result = self.conn.execute(sql, params).fetchall()
        else:
            result = self.conn.execute(sql).fetchall()

        logger.debug(f"SQL 查询执行成功：{sql[:50]}...")
        return result

    @handle_errors(DatabaseError)
    def query_df(self, sql: str, params: tuple | None = None) -> pd.DataFrame:
        """
        执行 SQL 查询并返回 DataFrame

        Args:
            sql: SQL 查询语句
            params: 参数元组

        Returns:
            pandas DataFrame
        """
        if params:
            df = self.conn.execute(sql, params).fetchdf()
        else:
            df = self.conn.execute(sql).fetchdf()

        logger.debug(f"SQL 查询执行成功（DataFrame）：{sql[:50]}...")
        return df

    @handle_errors(DatabaseError)
    def insert(self, table: str, data: dict) -> None:
        """
        插入数据

        Args:
            table: 表名
            data: 数据字典
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        self.conn.execute(sql, tuple(data.values()))
        logger.debug(f"数据插入成功：{table}")

    @handle_errors(DatabaseError)
    def insert_many(self, table: str, data_list: list[dict]) -> int:
        """
        批量插入数据

        Args:
            table: 表名
            data_list: 数据字典列表

        Returns:
            插入的记录数
        """
        if not data_list:
            return 0

        columns = ", ".join(data_list[0].keys())
        placeholders = ", ".join(["?" for _ in data_list[0]])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        # 批量插入
        values = [tuple(item.values()) for item in data_list]
        self.conn.executemany(sql, values)

        logger.info(f"批量插入完成：{table}, {len(data_list)} 条记录")
        return len(data_list)

    @handle_errors(DatabaseError)
    def update(self, table: str, data: dict, where: str, params: tuple) -> int:
        """
        更新数据

        Args:
            table: 表名
            data: 要更新的数据字典
            where: WHERE 子句
            params: WHERE 参数

        Returns:
            更新的记录数
        """
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values()) + list(params)

        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        result = self.conn.execute(sql, values)

        logger.debug(f"数据更新成功：{table}, {result.rowcount} 条记录")
        return result.rowcount

    @handle_errors(DatabaseError)
    def delete(self, table: str, where: str, params: tuple) -> int:
        """
        删除数据

        Args:
            table: 表名
            where: WHERE 子句
            params: WHERE 参数

        Returns:
            删除的记录数
        """
        sql = f"DELETE FROM {table} WHERE {where}"
        result = self.conn.execute(sql, params)

        logger.debug(f"数据删除成功：{table}, {result.rowcount} 条记录")
        return result.rowcount

    @handle_errors(DatabaseError)
    def execute(self, sql: str, params: tuple | None = None):
        """
        执行任意 SQL 语句

        Args:
            sql: SQL 语句
            params: 参数
        """
        if params:
            self.conn.execute(sql, params)
        else:
            self.conn.execute(sql)

        logger.debug(f"SQL 执行成功：{sql[:50]}...")

    def close(self):
        """关闭数据库连接"""
        if hasattr(self, "conn"):
            self.conn.close()
            logger.info("数据库连接已关闭")

    def __enter__(self):
        """上下文管理器进入"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
