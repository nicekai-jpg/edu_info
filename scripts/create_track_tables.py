"""
创建赛道体系的数据库表

基于 Code Craft 原则设计：
- 单一职责：每张表只有一个修改理由
- 关注点分离：数据层/逻辑层/展示层
- 封装：私有字段 + 验证方法
- 组合优于继承：匹配器由维度组件组合
"""

from pathlib import Path

import duckdb


def get_db_path() -> Path:
    """计算数据库路径"""
    # 从 scripts/ 回到项目根目录
    current = Path(__file__).resolve()
    for _ in range(2):  # scripts/xxx.py → project root
        current = current.parent
    return current / "data" / "edu_planning.db"


def create_tables(conn: duckdb.DuckDBPyConnection):
    """创建所有赛道相关表"""

    # ═══════════════════════════════════════════════════════════
    # 第一层：领域层（独立）
    # ═══════════════════════════════════════════════════════════

    conn.execute("""
        CREATE TABLE IF NOT EXISTS domains (
            domain_id INTEGER PRIMARY KEY,
            domain_name VARCHAR(100) NOT NULL,      -- AI、低空经济、机器人、非遗、文化传播
            description TEXT,
            lifecycle_stage VARCHAR(20),            -- 新兴/成长/成熟/转型
            strategic_importance DECIMAL(3,2),      -- 战略重要性 0.00-1.00
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ 创建 domains 表")

    # ═══════════════════════════════════════════════════════════
    # 第二层：专业类别层（连接领域和赛道）
    # ═══════════════════════════════════════════════════════════

    conn.execute("""
        CREATE TABLE IF NOT EXISTS major_categories (
            category_id INTEGER PRIMARY KEY,
            category_name VARCHAR(100) NOT NULL,    -- 计算机类、机械类
            domain_id INTEGER NOT NULL,
            education_code VARCHAR(20),             -- 教育部专业类代码
            description TEXT,
            core_courses JSON,                      -- 核心课程列表
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ 创建 major_categories 表")

    # ═══════════════════════════════════════════════════════════
    # 第三层：赛道层（按 SRP 拆分为多个表）
    # ═══════════════════════════════════════════════════════════

    # 3. 赛道定义表（仅核心信息）
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            track_id INTEGER PRIMARY KEY,
            track_name VARCHAR(100) NOT NULL,       -- AI 算法工程师
            description TEXT,                       -- 赛道定义
            lifecycle_stage VARCHAR(20),            -- 新兴/成长/成熟
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ 创建 tracks 表")

    # 4. 赛道 - 领域关联表（分离多对多关系）
    conn.execute("""
        CREATE TABLE IF NOT EXISTS track_domain_mapping (
            track_id INTEGER NOT NULL,
            domain_id INTEGER NOT NULL,
            is_primary BOOLEAN DEFAULT FALSE,       -- 是否主属领域
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (track_id, domain_id)
        )
    """)
    print("✅ 创建 track_domain_mapping 表")

    # 5. 赛道 - 专业类别映射表（分离映射关系）
    conn.execute("""
        CREATE TABLE IF NOT EXISTS track_category_mapping (
            track_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            mapping_type VARCHAR(20),               -- 核心/相关/边缘
            shared_courses_ratio DECIMAL(3,2),      -- 课程共享比例 0.00-1.00
            conversion_cost VARCHAR(20),            -- 低/中/高
            skill_gap JSON,                         -- 需补充的技能
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (track_id, category_id)
        )
    """)
    print("✅ 创建 track_category_mapping 表")

    # 6. 赛道就业信息表（分离就业数据）
    conn.execute("""
        CREATE TABLE IF NOT EXISTS track_employment_info (
            track_id INTEGER PRIMARY KEY,
            typical_positions JSON NOT NULL,        -- 典型岗位
            salary_ranges JSON NOT NULL,            -- 薪资范围
            typical_companies JSON,                 -- 典型企业
            company_types JSON,                     -- 企业类型
            employment_rate DECIMAL(5,2),           -- 就业率
            avg_salary DECIMAL(10,2),               -- 平均薪资
            data_source VARCHAR(100),               -- 数据来源
            confidence_level VARCHAR(20),           -- 高/中/低置信度
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ 创建 track_employment_info 表")

    # 7. 赛道能力要求表（分离能力模型）
    conn.execute("""
        CREATE TABLE IF NOT EXISTS track_requirements (
            track_id INTEGER PRIMARY KEY,
            required_skills JSON NOT NULL,          -- 所需技能
            score_requirements JSON,                -- 分数要求
            preferred_subjects JSON,                -- 优选科目
        )
    """)
    print("✅ 创建 track_requirements 表")

    # 8. 赛道政策关联表（分离政策数据）
    conn.execute("""
        CREATE TABLE IF NOT EXISTS track_policy_mapping (
            track_id INTEGER NOT NULL,
            policy_id INTEGER NOT NULL,
            policy_name VARCHAR(200) NOT NULL,
            policy_level VARCHAR(20),               -- 国家/省级
            support_type VARCHAR(50),               -- 资金/人才/平台
            impact_score DECIMAL(3,2),              -- 影响程度 0.00-1.00
            document_url VARCHAR(500),              -- 政策文件链接
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (track_id, policy_id)
        )
    """)
    print("✅ 创建 track_policy_mapping 表")

    # 9. 赛道 - 院校竞争力表（分离竞争力评估）
    conn.execute("""
        CREATE TABLE IF NOT EXISTS track_university_competitiveness (
            track_id INTEGER NOT NULL,
            university_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,           -- 基于哪个专业类别
            competitiveness_level VARCHAR(10),      -- A+/A/B+/B
            track_ranking INTEGER,                  -- 赛道排名

            -- 评估维度（分离原始数据）
            discipline_grade VARCHAR(5),            -- 学科评估
            research_score DECIMAL(5,2),            -- 科研实力 0.00-100.00
            industry_score DECIMAL(5,2),            -- 产业合作 0.00-100.00
            employment_score DECIMAL(5,2),          -- 就业质量 0.00-100.00
            alumni_score DECIMAL(5,2),              -- 校友资源 0.00-100.00
            overall_score DECIMAL(5,2),             -- 综合得分 0.00-100.00

            -- 就业数据
            employment_rate DECIMAL(5,2),
            avg_salary DECIMAL(10,2),
            typical_employers JSON,

            data_year INTEGER DEFAULT 2025,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (track_id, university_id, category_id)
        )
    """)
    print("✅ 创建 track_university_competitiveness 表")

    # 10. 学生 - 赛道匹配结果表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS student_track_matches (
            match_id BIGINT PRIMARY KEY,
            student_id INTEGER NOT NULL,
            track_id INTEGER NOT NULL,
            match_score DECIMAL(5,2) NOT NULL,      -- 匹配总分 0.00-100.00
            interest_score DECIMAL(5,2),            -- 兴趣匹配
            ability_score DECIMAL(5,2),             -- 能力匹配
            economic_score DECIMAL(5,2),            -- 经济匹配
            time_score DECIMAL(5,2),                -- 时间匹配
            regional_score DECIMAL(5,2),            -- 地域匹配
            match_reasons JSON,                     -- 匹配理由
            gaps JSON,                              -- 差距分析
            action_items JSON,                      -- 行动建议
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ 创建 student_track_matches 表")

    # 11. 政策文件表（补充）
    conn.execute("""
        CREATE TABLE IF NOT EXISTS policies (
            policy_id INTEGER PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            doc_number VARCHAR(50),
            issuer VARCHAR(100),                    -- 发布机构
            issue_date DATE,                        -- 发布日期
            category VARCHAR(50),                   -- 高考改革/特长生/强基计划等
            level VARCHAR(20),                      -- 国家级/省级/市级
            content TEXT,
            summary TEXT,
            keywords JSON,
            related_routes JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ 创建 policies 表")

    # 12. 规划结果存储表（支持版本管理）
    conn.execute("""
        CREATE TABLE IF NOT EXISTS planning_results (
            result_id INTEGER PRIMARY KEY,
            student_id INTEGER NOT NULL,
            version_id VARCHAR(64) UNIQUE,          -- 版本 ID（时间戳）
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_version VARCHAR(32),               -- 数据版本（如 2025-03-07）
            top_routes JSON,                        -- Top 10 路线
            targets_data JSON,                      -- 三档目标
            feasibility_data JSON,                  -- 可行性评估
            match_details JSON,                     -- 匹配详情
            change_summary TEXT,                    -- 与上一版本的变更摘要
            is_latest BOOLEAN DEFAULT TRUE
        )
    """)
    print("✅ 创建 planning_results 表")

    # 创建索引以提升查询性能
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_track_domain ON track_domain_mapping(domain_id);
        CREATE INDEX IF NOT EXISTS idx_track_category ON track_category_mapping(category_id);
        CREATE INDEX IF NOT EXISTS idx_student_match ON student_track_matches(student_id);
        CREATE INDEX IF NOT EXISTS idx_track_university ON track_university_competitiveness(university_id);
    """)
    print("✅ 创建索引")


def insert_sample_data(conn: duckdb.DuckDBPyConnection):
    """插入示例数据"""

    # 插入领域数据
    domains = [
        (1, 'AI', '人工智能领域，包括算法研发、应用开发、大模型等方向', '成长', 0.95),
        (2, '低空经济', '低空经济领域，包括飞行器设计、飞控算法、运营管理等方向', '新兴', 0.85),
        (3, '机器人', '机器人领域，包括机械结构、控制算法、视觉系统等方向', '成长', 0.90),
        (4, '非遗', '非物质文化遗产保护与传承领域，包括数字化保护、传承策划等方向', '新兴', 0.75),
        (5, '文化传播', '文化传播领域，包括新媒体运营、品牌传播、国际传播等方向', '成熟', 0.80),
    ]

    conn.executemany("""
        INSERT OR REPLACE INTO domains
        (domain_id, domain_name, description, lifecycle_stage, strategic_importance)
        VALUES (?, ?, ?, ?, ?)
    """, domains)
    print(f"✅ 插入 {len(domains)} 个领域数据")

    # 插入专业类别数据
    major_categories = [
        # AI 领域
        (1, '计算机类', 1, '0809', '包括计算机科学与技术、软件工程等专业',
         '["数据结构", "算法设计", "计算机组成原理", "操作系统"]'),
        (2, '人工智能类', 1, '0809T', '包括人工智能、智能科学与技术等专业',
         '["机器学习", "深度学习", "计算机视觉", "自然语言处理"]'),
        (3, '数据科学类', 1, '0711', '包括数据科学、统计学等专业',
         '["概率论", "数理统计", "数据分析", "机器学习"]'),

        # 低空经济领域
        (4, '航空航天类', 2, '0820', '包括飞行器设计与工程、航空宇航科学与技术等专业',
         '["空气动力学", "飞行器设计", "航空发动机原理"]'),
        (5, '控制类', 2, '0811', '包括导航制导与控制、自动化等专业',
         '["自动控制原理", "现代控制理论", "导航原理"]'),
        (6, '运营管理类', 2, '1206', '包括交通运输、航空服务与管理等专业',
         '["交通运输规划", "航空管理", "运营管理"]'),

        # 机器人领域
        (7, '机械类', 3, '0802', '包括机械工程、机械设计制造及其自动化等专业',
         '["机械原理", "机械设计", "材料力学", "理论力学"]'),
        (8, '自动化类', 3, '0808', '包括自动化、机器人工程等专业',
         '["自动控制原理", "机器人学", "运动控制"]'),
        (9, '电子类', 3, '0803', '包括电子信息工程、测控技术与仪器等专业',
         '["电路原理", "模拟电子技术", "数字电子技术"]'),

        # 非遗领域
        (10, '文化遗产类', 4, '0601', '包括文物与博物馆学、非物质文化遗产保护等专业',
         '["文化遗产概论", "非遗保护原理", "文化人类学"]'),
        (11, '数字媒体类', 4, '1305', '包括数字媒体技术、数字媒体艺术等专业',
         '["数字媒体技术", "计算机图形学", "虚拟现实技术"]'),

        # 文化传播领域
        (12, '新闻传播类', 5, '0503', '包括新闻学、传播学、广告学等专业',
         '["传播学概论", "新闻学原理", "媒体研究"]'),
        (13, '文化产业类', 5, '1202', '包括文化产业管理、艺术管理等专业',
         '["文化产业概论", "文化市场营销", "文化政策"]'),
    ]

    conn.executemany("""
        INSERT OR REPLACE INTO major_categories
        (category_id, category_name, domain_id, education_code, description, core_courses)
        VALUES (?, ?, ?, ?, ?, ?)
    """, major_categories)
    print(f"✅ 插入 {len(major_categories)} 个专业类别数据")

    # 插入赛道数据
    tracks = [
        # AI 领域赛道
        (1, 'AI 算法工程师', '从事人工智能算法研发、模型训练与优化的专业人才', '成长'),
        (2, 'AI 应用开发工程师', '从事 AI 技术应用开发、系统集成的人才', '成长'),
        (3, '大模型训练师', '从事大语言模型训练、微调、优化的专业人才', '新兴'),
        (4, '计算机视觉工程师', '从事图像识别、视频分析等视觉算法研发的人才', '成长'),
        (5, '数据分析师', '从事数据挖掘、数据分析、商业智能的人才', '成熟'),

        # 低空经济领域赛道
        (6, '飞行器设计工程师', '从事无人机、eVTOL 等飞行器设计的专业人才', '新兴'),
        (7, '飞控算法工程师', '从事飞行控制算法研发、导航制导的专业人才', '新兴'),
        (8, '低空交通规划师', '从事低空交通管理、航线规划的专业人才', '新兴'),

        # 机器人领域赛道
        (9, '机械结构工程师', '从事机器人本体结构设计、优化的专业人才', '成长'),
        (10, '机器人控制算法工程师', '从事机器人运动控制、路径规划算法研发的人才', '成长'),
        (11, '嵌入式硬件工程师', '从事机器人嵌入式系统、传感器硬件设计的人才', '成长'),
        (12, '机器人视觉算法工程师', '从事机器人视觉感知、SLAM 算法研发的人才', '成长'),

        # 非遗领域赛道
        (13, '非遗数字化工程师', '从事非遗数字化保护、虚拟展示的专业人才', '新兴'),
        (14, '非遗传承策划师', '从事非遗传承活动策划、推广的专业人才', '新兴'),

        # 文化传播领域赛道
        (15, '新媒体运营师', '从事新媒体内容创作、运营推广的专业人才', '成熟'),
        (16, '品牌传播师', '从事品牌策划、传播推广的专业人才', '成熟'),
        (17, '国际传播师', '从事国际文化交流、对外传播的专业人才', '成长'),
    ]

    conn.executemany("""
        INSERT OR REPLACE INTO tracks
        (track_id, track_name, description, lifecycle_stage)
        VALUES (?, ?, ?, ?)
    """, tracks)
    print(f"✅ 插入 {len(tracks)} 个赛道数据")

    # 插入赛道 - 领域映射
    track_domain_mappings = [
        # AI 赛道映射到 AI 领域
        (1, 1, True), (2, 1, True), (3, 1, True), (4, 1, True), (5, 1, False),
        # 低空经济赛道
        (6, 2, True), (7, 2, True), (8, 2, True),
        # 机器人赛道
        (9, 3, True), (10, 3, True), (11, 3, True), (12, 3, False),
        # 非遗赛道
        (13, 4, True), (14, 4, True),
        # 文化传播赛道
        (15, 5, True), (16, 5, True), (17, 5, True),
    ]

    conn.executemany("""
        INSERT OR REPLACE INTO track_domain_mapping
        (track_id, domain_id, is_primary)
        VALUES (?, ?, ?)
    """, track_domain_mappings)
    print(f"✅ 插入 {len(track_domain_mappings)} 条赛道 - 领域映射")

    # 插入赛道 - 专业类别映射（示例）
    track_category_mappings = [
        # AI 算法工程师 - 核心专业类别
        (1, 1, '核心', 0.80, '低', '["机器学习", "深度学习"]'),
        (1, 2, '核心', 0.85, '低', '["算法优化"]'),
        (1, 3, '相关', 0.50, '中', '["计算机科学基础", "编程能力"]'),

        # AI 应用开发工程师
        (2, 1, '核心', 0.75, '低', '["应用开发框架"]'),
        (2, 2, '相关', 0.60, '中', '["AI 接口调用"]'),

        # 数据分析师
        (5, 3, '核心', 0.80, '低', '[]'),
        (5, 1, '相关', 0.50, '中', '["数据库", "编程基础"]'),
    ]

    conn.executemany("""
        INSERT OR REPLACE INTO track_category_mapping
        (track_id, category_id, mapping_type, shared_courses_ratio, conversion_cost, skill_gap)
        VALUES (?, ?, ?, ?, ?, ?)
    """, track_category_mappings)
    print(f"✅ 插入 {len(track_category_mappings)} 条赛道 - 专业类别映射")

    # 插入赛道就业信息（示例）
    track_employment_info = [
        (1,
         '["AI 算法工程师", "深度学习工程师", "机器学习工程师"]',
         '{"1-3 年": "25-45 万", "3-5 年": "40-80 万", "5 年以上": "60-150 万"}',
         '["百度", "阿里", "腾讯", "字节", "华为", "商汤", "旷视"]',
         '["互联网大厂", "AI 独角兽", "央企研究院"]',
         0.92, 550000.00, '网络爬取 + 高校就业报告', '高'),

        (2,
         '["AI 应用开发工程师", "AI 系统集成工程师"]',
         '{"1-3 年": "20-35 万", "3-5 年": "30-60 万", "5 年以上": "50-100 万"}',
         '["互联网企业", "软件公司", "AI 创业公司"]',
         '["互联网", "软件", "创业公司"]',
         0.90, 450000.00, '网络爬取', '高'),

        (3,
         '["大模型训练师", "大模型优化工程师"]',
         '{"1-3 年": "30-50 万", "3-5 年": "50-100 万", "5 年以上": "80-200 万"}',
         '["百度", "阿里", "腾讯", "字节", "智谱 AI", "MiniMax"]',
         '["大模型公司", "互联网大厂"]',
         0.88, 650000.00, '网络爬取', '中'),
    ]

    conn.executemany("""
        INSERT OR REPLACE INTO track_employment_info
        (track_id, typical_positions, salary_ranges, typical_companies,
         company_types, employment_rate, avg_salary, data_source, confidence_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, track_employment_info)
    print(f"✅ 插入 {len(track_employment_info)} 条赛道就业信息")

    # 插入赛道能力要求（示例）
    track_requirements = [
        (1,
         '["Python", "PyTorch/TensorFlow", "深度学习", "算法设计", "数学基础"]',
         '{"数学": 135, "物理": 130, "总分": 650}',
         '["物理", "技术"]'),

        (2,
         '["Python/Java", "应用开发框架", "AI 接口调用", "系统设计"]',
         '{"数学": 125, "物理": 120, "总分": 620}',
         '["物理", "技术"]'),

        (3,
         '["Python", "深度学习", "大模型原理", "分布式训练", "GPU 优化"]',
         '{"数学": 140, "物理": 135, "总分": 670}',
         '["物理", "技术"]'),
    ]

    conn.executemany("""
        INSERT OR REPLACE INTO track_requirements
        (track_id, required_skills, score_requirements, preferred_subjects)
        VALUES (?, ?, ?, ?)
    """, track_requirements)
    print(f"✅ 插入 {len(track_requirements)} 条赛道能力要求")


def main():
    """主函数"""
    db_path = get_db_path()
    print(f"📦 数据库路径：{db_path}")

    # 确保数据目录存在
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # 连接数据库
    conn = duckdb.connect(str(db_path))

    try:
        print("\n🔨 开始创建数据库表...")
        create_tables(conn)

        print("\n📊 开始插入示例数据...")
        insert_sample_data(conn)

        # 验证创建结果
        print("\n✅ 验证创建结果...")
        result = conn.execute("SELECT COUNT(*) FROM domains").fetchone()[0]
        print(f"   - 领域数量：{result}")

        result = conn.execute("SELECT COUNT(*) FROM major_categories").fetchone()[0]
        print(f"   - 专业类别数量：{result}")

        result = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        print(f"   - 赛道数量：{result}")

        result = conn.execute("SELECT COUNT(*) FROM track_domain_mapping").fetchone()[0]
        print(f"   - 赛道 - 领域映射数量：{result}")

        result = conn.execute("SELECT COUNT(*) FROM track_category_mapping").fetchone()[0]
        print(f"   - 赛道 - 专业类别映射数量：{result}")

        result = conn.execute("SELECT COUNT(*) FROM track_employment_info").fetchone()[0]
        print(f"   - 赛道就业信息数量：{result}")

        print("\n✨ 数据库表创建完成！")

    except Exception as e:
        print(f"\n❌ 错误：{e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
