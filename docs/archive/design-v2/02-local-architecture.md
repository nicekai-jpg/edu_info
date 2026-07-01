# 02 - 本地程序架构设计（v2.1）

## 1. 架构概述

### 1.1 核心定位

```
运行方式: 本地Python程序（无需服务器，完全离线）
目标用户: 初中生家长（个人使用）
数据视角: 全国高校 + 辽宁录取分数
规划逻辑: 穷举所有路线 → 多维度匹配 → 筛选推荐
技术选型: Python + Streamlit + DuckDB
```

### 1.2 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    用户交互层 (Streamlit UI)                 │
│  ├─ 首页/导航                                               │
│  ├─ 数据管理（导入/查看）                                    │
│  ├─ 学生档案管理                                            │
│  ├─ 规划分析界面                                            │
│  ├─ 结果展示（三档目标）                                     │
│  └─ 报告生成（PDF/Excel）                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   规划分析引擎层                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              路线穷举器 (RouteEnumerator)            │   │
│  │  穷举50-100条可能的规划路线：                          │   │
│  │  • 普通高考（985/211/普通本科）                        │   │
│  │  • 科技特长（信息学/机器人/科创）                      │   │
│  │  • 艺术特长（音乐/美术/舞蹈）                          │   │
│  │  • 体育特长（高水平运动队/单招）                       │   │
│  │  • 拔尖人才（奥赛/强基/综评）                          │   │
│  │  • 特殊类型（港澳/中外合作）                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────▼────────────────────────────┐   │
│  │           多维度匹配器 (MultiDimensionalMatcher)      │   │
│  │  从5个维度评估匹配度：                                 │   │
│  │  • 兴趣匹配（40%）- 兴趣领域重合度                     │   │
│  │  • 能力匹配（25%）- 学科成绩+特长                      │   │
│  │  • 经济匹配（20%）- 路线成本vs家庭收入                 │   │
│  │  • 时间匹配（10%）- 准备周期可行性                     │   │
│  │  • 地域匹配（5%）- 目标地区偏好                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────▼────────────────────────────┐   │
│  │           目标生成器 (TargetGenerator)               │   │
│  │  为Top 10路线生成三档目标：                            │   │
│  │  • 高目标：该路线最好高校                              │   │
│  │  • 中目标：匹配当前水平的高校                          │   │
│  │  • 低目标：保底高校                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────▼────────────────────────────┐   │
│  │           可行性评估器 (FeasibilityAssessor)          │   │
│  │  评估每个目标的达成概率：                              │   │
│  │  • 当前水平分析                                        │   │
│  │  • 目标要求对比                                        │   │
│  │  • 差距识别                                            │   │
│  │  • 达成概率计算                                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│  └────────────────────────┬──────────────────────────────┘   │
│                           │                                  │
└───────────────────────────▼───────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────┐
│                    本地数据层 (DuckDB)                         │
│  ┌───────────────────────────────────────────────────────┐   │
│  │              路线数据库 (Route DB)                     │   │
│  │  • 所有规划路线的定义和属性                             │   │
│  │  • 50-100条规划路线                                     │   │
│  └───────────────────────────────────────────────────────┘   │
│  ┌───────────────────────────────────────────────────────┐   │
│  │         全国高校+辽宁分数库 (Score DB)                  │   │
│  │  • 985高校在辽宁录取分数（39所）                        │   │
│  │  • 211高校在辽宁录取分数（116所）                       │   │
│  │  • 双一流高校在辽宁录取分数（147所）                    │   │
│  │  • 其他重点高校在辽宁录取分数                           │   │
│  │  • 近5年（2021-2025）各专业分数线                       │   │
│  └───────────────────────────────────────────────────────┘   │
│  ┌───────────────────────────────────────────────────────┐   │
│  │              政策数据库 (Policy DB)                    │   │
│  │  • 国家教育政策                                         │   │
│  │  • 辽宁省高考/中考政策                                  │   │
│  │  • 特殊类型招生政策                                     │   │
│  └───────────────────────────────────────────────────────┘   │
│  ┌───────────────────────────────────────────────────────┐   │
│  │              战略数据库 (Strategy DB)                  │   │
│  │  • 国家发展战略                                         │   │
│  │  • 产业趋势数据                                         │   │
│  │  • 人才需求预测                                         │   │
│  └───────────────────────────────────────────────────────┘   │
│  ┌───────────────────────────────────────────────────────┐   │
│  │            学生档案库 (Profile DB)                     │   │
│  │  • 学生基本信息                                         │   │
│  │  • 成绩记录                                             │   │
│  │  • 兴趣特长                                             │   │
│  │  • 规划历史                                             │   │
│  └───────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

## 2. 技术栈选型

### 2.1 为什么选择这套技术栈？

```yaml
Python 3.11+:
  优势:
    - 数据分析生态最成熟（Pandas、NumPy）
    - AI/ML支持完善（Scikit-learn）
    - 开发效率高
    - 跨平台（Windows/macOS/Linux）
  用途: 核心业务逻辑、数据处理、算法实现

Streamlit:
  优势:
    - Python原生，无需前端开发
    - 数据可视化内置
    - 热重载开发体验好
    - 适合数据分析类应用
  用途: 用户界面、图表展示、交互表单

DuckDB:
  优势:
    - 分析型数据库，查询性能强
    - 嵌入式，无需单独服务
    - 支持SQL
    - 与Pandas无缝集成
  用途: 本地数据存储、复杂查询、分析计算

Pandas:
  优势:
    - 数据处理标准库
    - 丰富的数据操作方法
    - 与DuckDB配合良好
  用途: 数据清洗、转换、分析

Plotly/Matplotlib:
  优势:
    - 交互式图表
    - Streamlit原生支持
  用途: 数据可视化、趋势图表
```

### 2.2 对比其他方案

| 方案 | 优势 | 劣势 | 适用性 |
|------|------|------|--------|
| **Python+Streamlit** ✅ | 开发快、数据分析强、免费 | 界面不如专业桌面应用 | ⭐⭐⭐⭐⭐ |
| Python+PyQt | 界面专业、功能强大 | 开发慢、学习曲线陡 | ⭐⭐⭐ |
| Python+Tkinter | 轻量、标准库 | 界面简陋 | ⭐⭐ |
| Electron+JS | 界面美观 | 需要前端技能、体积大 | ⭐⭐ |
| Java+Swing | 跨平台 | 开发慢、过时 | ⭐ |

**最终选择：Python + Streamlit + DuckDB**

## 3. 项目目录结构

```
edu_planning_system/
│
├── app.py                      # Streamlit主应用入口
├── run.py                      # 启动脚本
├── requirements.txt            # Python依赖
├── config.yaml                 # 配置文件
│
├── data/                       # 数据目录
│   ├── raw/                    # 原始数据（CSV/Excel）
│   │   ├── scores/             # 分数线数据
│   │   ├── policies/           # 政策文件
│   │   └── universities/       # 高校信息
│   │
│   ├── processed/              # 处理后数据（DuckDB）
│   │   └── edu_planning.duckdb # 主数据库
│   │
│   └── routes/                 # 路线定义数据
│       └── planning_routes.json # 规划路线定义
│
├── src/                        # 源代码
│   ├── __init__.py
│   │
│   ├── data/                   # 数据模块
│   │   ├── __init__.py
│   │   ├── database.py         # DuckDB连接和操作
│   │   ├── importer.py         # 数据导入（Excel/CSV）
│   │   └── models.py           # 数据模型定义
│   │
│   ├── engine/                 # 规划引擎模块
│   │   ├── __init__.py
│   │   ├── route_enumerator.py # 路线穷举器
│   │   ├── matcher.py          # 多维度匹配器
│   │   ├── target_generator.py # 目标生成器
│   │   ├── feasibility.py      # 可行性评估器
│   │   └── planner.py          # 规划引擎主类
│   │
│   ├── ui/                     # UI模块
│   │   ├── __init__.py
│   │   ├── home.py             # 首页
│   │   ├── data_manager.py     # 数据管理页
│   │   ├── student_profile.py  # 学生档案页
│   │   ├── analysis.py         # 规划分析页
│   │   ├── results.py          # 结果展示页
│   │   └── reports.py          # 报告生成页
│   │
│   └── utils/                  # 工具模块
│       ├── __init__.py
│       ├── config.py           # 配置管理
│       ├── logger.py           # 日志工具
│       └── validators.py       # 数据验证
│
├── docs/                       # 文档
│   ├── README.md
│   ├── user_guide.md           # 用户手册
│   └── data_collection_guide.md # 数据收集指南
│
└── tests/                      # 测试
    ├── __init__.py
    ├── test_engine.py          # 引擎测试
    └── test_data.py            # 数据测试
```

## 4. 数据库设计

### 4.1 DuckDB Schema

```sql
-- 高校基本信息表
CREATE TABLE universities (
    university_id INTEGER PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    code VARCHAR(20),
    province VARCHAR(64),
    city VARCHAR(64),
    level VARCHAR(32),        -- 985/211/双一流/普通
    type VARCHAR(32),         -- 综合/理工/师范/医药等
    is_985 BOOLEAN,
    is_211 BOOLEAN,
    is_double_first_class BOOLEAN,
    tags VARCHAR(256),        -- 标签JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 专业信息表
CREATE TABLE majors (
    major_id INTEGER PRIMARY KEY,
    code VARCHAR(20),
    name VARCHAR(128) NOT NULL,
    category VARCHAR(64),     -- 学科门类
    degree_level VARCHAR(16), -- 本科/专科
    related_industries VARCHAR(512), -- 关联产业JSON
    prospects_rating INTEGER, -- 前景评分1-5
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 录取分数表（核心大表）
CREATE TABLE admission_scores (
    score_id BIGINT PRIMARY KEY,
    university_id INTEGER REFERENCES universities(university_id),
    major_id INTEGER REFERENCES majors(major_id),
    year INTEGER NOT NULL,           -- 年份
    admission_type VARCHAR(32),      -- 招生类型（统招/艺术/体育等）
    subject_type VARCHAR(16),        -- 物理类/历史类/综合
    batch VARCHAR(32),               -- 本科批/提前批等
    min_score INTEGER,               -- 最低分
    avg_score INTEGER,               -- 平均分
    max_score INTEGER,               -- 最高分
    min_rank INTEGER,                -- 最低位次（关键）
    avg_rank INTEGER,                -- 平均位次
    enrollment_plan INTEGER,         -- 招生计划
    source_url VARCHAR(512),
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 规划路线定义表
CREATE TABLE planning_routes (
    route_id VARCHAR(64) PRIMARY KEY,
    category VARCHAR(64),            -- 路线类别
    name VARCHAR(128) NOT NULL,
    description TEXT,
    min_grade VARCHAR(16),           -- 最低年级要求
    max_grade VARCHAR(16),           -- 最高年级要求
    subject_requirements VARCHAR(256), -- 学科要求JSON
    talent_requirements VARCHAR(256),  -- 特长要求JSON
    preparation_period VARCHAR(32),  -- 准备周期
    difficulty VARCHAR(16),          -- 难度
    success_rate VARCHAR(32),        -- 成功率描述
    cost_min INTEGER,                -- 最低费用（万元）
    cost_max INTEGER,                -- 最高费用（万元）
    cost_items VARCHAR(512),         -- 费用明细JSON
    target_university_types VARCHAR(256), -- 目标高校类型
    target_major_types VARCHAR(256), -- 目标专业类型
    related_policies VARCHAR(512),   -- 相关政策JSON
    related_industries VARCHAR(512), -- 关联产业JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 学生档案表
CREATE TABLE student_profiles (
    profile_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(64),
    current_grade VARCHAR(16),
    school VARCHAR(128),
    city VARCHAR(64),
    scores VARCHAR(512),             -- 成绩JSON
    overall_level VARCHAR(8),        -- 综合等级A+/A/B+/B/C
    interests VARCHAR(256),          -- 兴趣JSON
    special_talents VARCHAR(256),    -- 特长JSON
    competitions VARCHAR(512),       -- 竞赛获奖JSON
    family_income INTEGER,           -- 家庭年收入
    preferred_regions VARCHAR(256),  -- 偏好地区JSON
    constraints VARCHAR(512),        -- 约束条件JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 规划结果表
CREATE TABLE planning_results (
    result_id VARCHAR(64) PRIMARY KEY,
    profile_id VARCHAR(64) REFERENCES student_profiles(profile_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    routes_data TEXT,                -- 推荐路线JSON（大字段）
    targets_data TEXT,               -- 目标高校JSON
    feasibility_data TEXT,           -- 可行性评估JSON
    report_path VARCHAR(512)         -- 报告文件路径
);

-- 创建索引优化查询
CREATE INDEX idx_scores_query ON admission_scores(
    year, subject_type, admission_type, min_rank
);

CREATE INDEX idx_universities_level ON universities(level, province);

CREATE INDEX idx_routes_category ON planning_routes(category);
```

### 4.2 数据库初始化

```python
# src/data/database.py

import duckdb
from pathlib import Path

class Database:
    """DuckDB数据库管理"""
    
    def __init__(self, db_path: str = "data/processed/edu_planning.duckdb"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(str(self.db_path))
        self._init_tables()
    
    def _init_tables(self):
        """初始化数据表"""
        # 创建所有表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS universities (...);
            CREATE TABLE IF NOT EXISTS majors (...);
            CREATE TABLE IF NOT EXISTS admission_scores (...);
            CREATE TABLE IF NOT EXISTS planning_routes (...);
            CREATE TABLE IF NOT EXISTS student_profiles (...);
            CREATE TABLE IF NOT EXISTS planning_results (...);
        """)
    
    def query(self, sql: str, params: tuple = None):
        """执行查询"""
        if params:
            return self.conn.execute(sql, params).fetchall()
        return self.conn.execute(sql).fetchall()
    
    def query_df(self, sql: str, params: tuple = None):
        """执行查询返回DataFrame"""
        import pandas as pd
        if params:
            return self.conn.execute(sql, params).fetchdf()
        return self.conn.execute(sql).fetchdf()
    
    def insert(self, table: str, data: dict):
        """插入数据"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.conn.execute(sql, tuple(data.values()))
    
    def close(self):
        """关闭连接"""
        self.conn.close()
```

## 5. 程序启动流程

### 5.1 启动脚本

```python
# run.py

#!/usr/bin/env python3
"""
升学规划系统启动脚本
"""

import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import streamlit
        import duckdb
        import pandas
        print("✓ 所有依赖已安装")
        return True
    except ImportError as e:
        print(f"✗ 缺少依赖: {e}")
        print("正在安装依赖...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True

def init_database():
    """初始化数据库"""
    from src.data.database import Database
    db = Database()
    print("✓ 数据库初始化完成")
    db.close()

def main():
    """主函数"""
    print("=" * 60)
    print("  智能升学规划系统")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 初始化数据库
    init_database()
    
    # 启动Streamlit
    print("\n正在启动系统...")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port=8501",
        "--server.headless=true"
    ])

if __name__ == "__main__":
    main()
```

### 5.2 主应用入口

```python
# app.py

import streamlit as st
from src.ui.home import render_home
from src.ui.data_manager import render_data_manager
from src.ui.student_profile import render_profile_manager
from src.ui.analysis import render_analysis
from src.ui.results import render_results
from src.ui.reports import render_reports

# 页面配置
st.set_page_config(
    page_title="智能升学规划系统",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 侧边栏导航
st.sidebar.title("🎓 升学规划系统")

page = st.sidebar.radio(
    "导航",
    ["🏠 首页", "📊 数据管理", "👤 学生档案", "🎯 规划分析", "📄 规划报告"]
)

# 根据选择渲染页面
if page == "🏠 首页":
    render_home()
elif page == "📊 数据管理":
    render_data_manager()
elif page == "👤 学生档案":
    render_profile_manager()
elif page == "🎯 规划分析":
    render_analysis()
elif page == "📄 规划报告":
    render_reports()
```

## 6. 性能设计

### 6.1 性能目标

| 场景 | 目标 | 策略 |
|------|------|------|
| 路线穷举 | < 100ms | 内存中加载路线定义 |
| 多维度匹配 | < 500ms | 向量计算 + 并行处理 |
| 目标生成 | < 2秒 | 数据库索引优化 |
| 完整分析 | < 5秒 | 全流程优化 |
| 数据导入 | < 30秒 | 批量插入 |

### 6.2 优化策略

```python
# 缓存策略
@st.cache_data
def load_planning_routes():
    """缓存路线定义（不重复加载）"""
    with open('data/routes/planning_routes.json') as f:
        return json.load(f)

# 数据库查询优化
# 使用DuckDB的列式存储和向量化执行
# 合理创建索引

# 并行处理
from concurrent.futures import ThreadPoolExecutor

def parallel_match(routes, profile):
    """并行匹配多条路线"""
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(matcher.match_single, route, profile)
            for route in routes
        ]
        return [f.result() for f in futures]
```

## 7. 部署方式

### 7.1 Windows部署

```bash
# 1. 安装Python 3.11+
# 从python.org下载安装

# 2. 下载程序
# 解压 edu_planning_system.zip

# 3. 运行
双击 run.bat
# 或命令行:
python run.py

# 4. 浏览器访问
# 自动打开 http://localhost:8501
```

### 7.2 macOS/Linux部署

```bash
# 1. 安装Python 3.11+
# macOS: brew install python@3.11
# Linux: sudo apt install python3.11

# 2. 下载程序
git clone https://github.com/xxx/edu_planning_system.git
cd edu_planning_system

# 3. 运行
python3 run.py

# 4. 浏览器访问
# 自动打开 http://localhost:8501
```

### 7.3 数据更新

```bash
# 更新分数线数据
# 1. 将新的Excel/CSV文件放入 data/raw/scores/
# 2. 在系统界面点击"数据管理" → "导入分数线"
# 3. 选择文件并导入

# 更新政策文件
# 1. 将PDF/Word文件放入 data/raw/policies/
# 2. 系统会自动解析关键信息
```

---

*本地程序架构设计 v2.1 - 更新版*

**更新说明**:
- v2.0: 初步版本
- v2.1: 全国高校在辽宁录取数据+穷举匹配模式