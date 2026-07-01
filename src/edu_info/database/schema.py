"""DuckDB 数据库 Schema 定义"""
from pathlib import Path

import duckdb


def get_schema_sql() -> str:
    """
    返回完整的数据库 Schema SQL

    Returns:
        包含所有表创建语句的 SQL 字符串
    """
    return """
    -- 高校数据表
    CREATE TABLE IF NOT EXISTS universities (
        id INTEGER PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        code VARCHAR(10) UNIQUE,
        location VARCHAR(50),
        type VARCHAR(20),
        is_985 BOOLEAN DEFAULT FALSE,
        is_211 BOOLEAN DEFAULT FALSE,
        is_double_first_class BOOLEAN DEFAULT FALSE,
        project_type VARCHAR(20),
        website VARCHAR(200),
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 专业数据表
    CREATE TABLE IF NOT EXISTS majors (
        id INTEGER PRIMARY KEY,
        university_id INTEGER REFERENCES universities(id),
        name VARCHAR(100) NOT NULL,
        code VARCHAR(10),
        category VARCHAR(50),
        major_class VARCHAR(50),
        degree VARCHAR(20),
        duration INTEGER DEFAULT 4,
        is_ln_recruiting BOOLEAN DEFAULT FALSE,
        ln_code VARCHAR(20),
        discipline_rank VARCHAR(5),
        is_national_key BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(university_id, name)
    );

    -- 爬取检查点表
    CREATE TABLE IF NOT EXISTS scraping_checkpoints (
        university_id INTEGER PRIMARY KEY REFERENCES universities(id),
        status VARCHAR(20) DEFAULT 'pending',
        last_tried_at TIMESTAMP,
        error_msg TEXT,
        retry_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 录取分数线表
    CREATE TABLE IF NOT EXISTS admission_scores (
        id INTEGER PRIMARY KEY,
        university_id INTEGER REFERENCES universities(id),
        major_id INTEGER REFERENCES majors(id),
        year INTEGER NOT NULL,
        province VARCHAR(50) NOT NULL,
        category VARCHAR(20) NOT NULL,
        min_score INTEGER,
        max_score INTEGER,
        avg_score INTEGER,
        min_rank INTEGER,
        max_rank INTEGER,
        plan_count INTEGER,
        actual_count INTEGER,
        batch VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(university_id, major_id, year, province, category)
    );

    -- 学生档案表
    CREATE SEQUENCE IF NOT EXISTS students_id_seq;

    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY DEFAULT nextval('students_id_seq'),
        name VARCHAR(50) NOT NULL,
        student_code VARCHAR(20) UNIQUE,
        gender VARCHAR(10),
        birth_date DATE,
        grade VARCHAR(20),
        school VARCHAR(100),
        city VARCHAR(50),
        category VARCHAR(20),
        total_score DECIMAL(5,2),
        ranking INTEGER,
        chinese_score DECIMAL(5,2),
        math_score DECIMAL(5,2),
        english_score DECIMAL(5,2),
        other_scores JSON,
        interests JSON,
        specialities JSON,
        awards JSON,
        family_budget DECIMAL(10,2),
        preferred_locations JSON,
        constraints JSON,
        planning_status VARCHAR(20) DEFAULT '未开始',
        last_plan_date TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 创建序列
    CREATE SEQUENCE IF NOT EXISTS planning_routes_id_seq;

    -- 规划路线表
    CREATE TABLE IF NOT EXISTS planning_routes (
        id INTEGER PRIMARY KEY DEFAULT nextval('planning_routes_id_seq'),
        route_id VARCHAR(50) UNIQUE,
        student_id INTEGER REFERENCES students(id),
        route_name VARCHAR(100),
        route_type VARCHAR(50),
        category VARCHAR(50),
        description TEXT,
        stages JSON,
        requirements JSON,
        timeline JSON,
        target_university_types JSON,
        target_major_types JSON,
        cost_min DECIMAL(10,2),
        cost_max DECIMAL(10,2),
        difficulty VARCHAR(20),
        success_rate VARCHAR(50),
        match_score DECIMAL(5,2),
        match_details JSON,
        target_universities JSON,
        feasibility_score DECIMAL(5,2),
        success_probability DECIMAL(5,2),
        risk_level VARCHAR(20),
        is_primary BOOLEAN DEFAULT FALSE,
        status VARCHAR(20) DEFAULT '草稿',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 政策文件表
    CREATE TABLE IF NOT EXISTS policies (
        id INTEGER PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        doc_number VARCHAR(50),
        issuer VARCHAR(100),
        issue_date DATE,
        effective_date DATE,
        level VARCHAR(20),
        category VARCHAR(50),
        region VARCHAR(50),
        file_path VARCHAR(300),
        content TEXT,
        summary TEXT,
        keywords JSON,
        related_routes JSON,
        related_majors JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 创建索引
    CREATE INDEX IF NOT EXISTS idx_univ_type ON universities(is_985, is_211);
    CREATE INDEX IF NOT EXISTS idx_univ_location ON universities(location);
    CREATE INDEX IF NOT EXISTS idx_major_univ ON majors(university_id);
    CREATE INDEX IF NOT EXISTS idx_major_category ON majors(category);
    CREATE INDEX IF NOT EXISTS idx_score_year ON admission_scores(year);
    CREATE INDEX IF NOT EXISTS idx_score_univ ON admission_scores(university_id);
    CREATE INDEX IF NOT EXISTS idx_score_rank ON admission_scores(min_rank);
    CREATE INDEX IF NOT EXISTS idx_policy_category ON policies(category);
    CREATE INDEX IF NOT EXISTS idx_policy_level ON policies(level);
    """


def init_database(conn: duckdb.DuckDBPyConnection) -> None:
    """
    初始化数据库，创建所有表

    Args:
        conn: DuckDB 连接对象
    """
    schema_sql = get_schema_sql()
    conn.execute(schema_sql)


def create_database(db_path: str) -> duckdb.DuckDBPyConnection:
    """
    创建数据库连接并初始化

    Args:
        db_path: 数据库文件路径

    Returns:
        DuckDB 连接对象
    """
    # 确保目录存在
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    # 创建连接
    conn = duckdb.connect(str(db_file))

    # 初始化 Schema
    init_database(conn)

    return conn


def get_connection(db_path: str) -> duckdb.DuckDBPyConnection:
    """
    获取数据库连接

    Args:
        db_path: 数据库文件路径

    Returns:
        DuckDB 连接对象
    """
    db_file = Path(db_path)

    if not db_file.exists():
        return create_database(db_path)

    return duckdb.connect(str(db_file))
