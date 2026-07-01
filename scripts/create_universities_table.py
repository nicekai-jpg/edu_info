"""
创建 universities 表并导入高校数据

从现有的 JSON 文件或硬编码数据导入全国高校信息
"""

from pathlib import Path

import duckdb


def get_db_path() -> Path:
    """计算数据库路径"""
    current = Path(__file__).resolve()
    for _ in range(2):
        current = current.parent
    return current / "data" / "edu_planning.db"


def create_universities_table(conn: duckdb.DuckDBPyConnection):
    """创建 universities 表"""

    conn.execute("""
        CREATE TABLE IF NOT EXISTS universities (
            university_id INTEGER PRIMARY KEY,
            university_name VARCHAR(100) NOT NULL,
            location VARCHAR(100),
            level VARCHAR(50),
            type VARCHAR(50),
            is_985 BOOLEAN,
            is_211 BOOLEAN,
            is_double_first_class BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ 创建 universities 表")


def insert_sample_universities(conn: duckdb.DuckDBPyConnection):
    """插入示例高校数据"""

    # 示例高校数据（覆盖 985、211、双一流）
    universities = [
        # 985 高校（顶尖）
        (1, '清华大学', '北京', '985|211|双一流', '综合', True, True, True),
        (2, '北京大学', '北京', '985|211|双一流', '综合', True, True, True),
        (3, '浙江大学', '杭州', '985|211|双一流', '综合', True, True, True),
        (4, '上海交通大学', '上海', '985|211|双一流', '综合', True, True, True),
        (5, '复旦大学', '上海', '985|211|双一流', '综合', True, True, True),
        (6, '南京大学', '南京', '985|211|双一流', '综合', True, True, True),
        (7, '中国科学技术大学', '合肥', '985|211|双一流', '理工', True, True, True),
        (8, '哈尔滨工业大学', '哈尔滨', '985|211|双一流', '理工', True, True, True),
        (9, '西安交通大学', '西安', '985|211|双一流', '综合', True, True, True),
        (10, '华中科技大学', '武汉', '985|211|双一流', '理工', True, True, True),

        # 985 高校（优秀）
        (11, '武汉大学', '武汉', '985|211|双一流', '综合', True, True, True),
        (12, '中山大学', '广州', '985|211|双一流', '综合', True, True, True),
        (13, '四川大学', '成都', '985|211|双一流', '综合', True, True, True),
        (14, '南开大学', '天津', '985|211|双一流', '综合', True, True, True),
        (15, '天津大学', '天津', '985|211|双一流', '理工', True, True, True),
        (16, '北京航空航天大学', '北京', '985|211|双一流', '理工', True, True, True),
        (17, '同济大学', '上海', '985|211|双一流', '理工', True, True, True),
        (18, '东南大学', '南京', '985|211|双一流', '综合', True, True, True),
        (19, '北京理工大学', '北京', '985|211|双一流', '理工', True, True, True),
        (20, '电子科技大学', '成都', '985|211|双一流', '理工', True, True, True),

        # 211 高校（行业特色）
        (21, '西安电子科技大学', '西安', '211|双一流', '理工', False, True, True),
        (22, '北京邮电大学', '北京', '211|双一流', '理工', False, True, True),
        (23, '上海财经大学', '上海', '211|双一流', '财经', False, True, True),
        (24, '中央财经大学', '北京', '211|双一流', '财经', False, True, True),
        (25, '对外经济贸易大学', '北京', '211|双一流', '财经', False, True, True),
        (26, '中国政法大学', '北京', '211|双一流', '政法', False, True, True),
        (27, '南京航空航天大学', '南京', '211|双一流', '理工', False, True, True),
        (28, '南京理工大学', '南京', '211|双一流', '理工', False, True, True),
        (29, '武汉理工大学', '武汉', '211|双一流', '理工', False, True, True),
        (30, '西南交通大学', '成都', '211|双一流', '理工', False, True, True),

        # 211 高校（地方重点）
        (31, '上海大学', '上海', '211|双一流', '综合', False, True, True),
        (32, '苏州大学', '苏州', '211|双一流', '综合', False, True, True),
        (33, '暨南大学', '广州', '211|双一流', '综合', False, True, True),
        (34, '华南师范大学', '广州', '211|双一流', '师范', False, True, True),
        (35, '湖南师范大学', '长沙', '211|双一流', '师范', False, True, True),

        # 双一流高校（省属重点）
        (36, '深圳大学', '深圳', '双一流', '综合', False, False, True),
        (37, '南方科技大学', '深圳', '双一流', '理工', False, False, True),
        (38, '首都医科大学', '北京', '双一流', '医药', False, False, True),
        (39, '南京工业大学', '南京', '双一流', '理工', False, False, True),
        (40, '浙江工业大学', '杭州', '省重点', '理工', False, False, False),

        # 辽宁省高校
        (41, '大连理工大学', '大连', '985|211|双一流', '理工', True, True, True),
        (42, '东北大学', '沈阳', '985|211|双一流', '理工', True, True, True),
        (43, '辽宁大学', '沈阳', '211|双一流', '综合', False, True, True),
        (44, '大连海事大学', '大连', '211|双一流', '理工', False, True, True),
        (45, '沈阳工业大学', '沈阳', '省重点', '理工', False, False, False),
        (46, '沈阳建筑大学', '沈阳', '省重点', '理工', False, False, False),
        (47, '沈阳航空航天大学', '沈阳', '省重点', '理工', False, False, False),
        (48, '辽宁师范大学', '大连', '省重点', '师范', False, False, False),
        (49, '沈阳师范大学', '沈阳', '省重点', '师范', False, False, False),
        (50, '沈阳大学', '沈阳', '普通本科', '综合', False, False, False),
    ]

    conn.executemany("""
        INSERT OR REPLACE INTO universities
        (university_id, university_name, location, level, type,
         is_985, is_211, is_double_first_class)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, universities)

    print(f"✅ 插入 {len(universities)} 条高校数据")


def main():
    """主函数"""
    db_path = get_db_path()
    print(f"📦 数据库路径：{db_path}")

    conn = duckdb.connect(str(db_path))

    try:
        create_universities_table(conn)
        insert_sample_universities(conn)

        # 验证
        count = conn.execute("SELECT COUNT(*) FROM universities").fetchone()[0]
        print(f"✅ universities 表共有 {count} 条记录")

    except Exception as e:
        print(f"❌ 错误：{e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
