# 院校专业全量爬虫系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个基于 Playwright 的高稳固性爬虫，抓取 173 所重点院校的完整专业库，并整合辽宁招生计划。

**Architecture:** 采用“调度器-执行引擎-数据处理器”三层架构。调度器负责断点续爬与批次管理，执行引擎负责深度模拟真人行为抓取数据，数据处理器负责清洗并入库 DuckDB。

**Tech Stack:** Python, Playwright, playwright-stealth, DuckDB, Pandas.

---

### Task 1: 环境准备与 Schema 扩展

**Files:**
- Modify: `src/edu_info/database/schema.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: 更新 pyproject.toml 添加依赖**
```toml
[project]
dependencies = [
    "playwright>=1.40.0",
    "playwright-stealth>=1.0.6",
]
```
- [ ] **Step 2: 运行环境安装命令**
Run: `uv sync && uv run playwright install chromium`
Expected: 成功安装 playwright 及其浏览器内核。

- [ ] **Step 3: 扩展数据库 Schema**
在 `src/edu_info/database/schema.py` 中增加 `scraping_checkpoints` 表并扩展 `majors` 表字段。
```python
# 修改 get_schema_sql 函数中的 SQL
# 1. 完善 majors 表
CREATE TABLE IF NOT EXISTS majors (
    id INTEGER PRIMARY KEY,
    university_id INTEGER REFERENCES universities(id),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10),
    category VARCHAR(50),      -- 学科门类
    major_class VARCHAR(50),   -- 专业类
    degree VARCHAR(20),        -- 授予学位
    duration INTEGER DEFAULT 4, -- 学制
    is_ln_recruiting BOOLEAN DEFAULT FALSE, -- 是否在辽宁招生
    ln_code VARCHAR(20),       -- 辽宁招生代码
    discipline_rank VARCHAR(5),
    is_national_key BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(university_id, name)
);

# 2. 新增进度表
CREATE TABLE IF NOT EXISTS scraping_checkpoints (
    university_id INTEGER PRIMARY KEY REFERENCES universities(id),
    status VARCHAR(20) DEFAULT 'pending', -- pending, running, success, failed
    last_tried_at TIMESTAMP,
    error_msg TEXT,
    retry_count INTEGER DEFAULT 0
);
```
- [ ] **Step 4: 初始化数据库变更**
Run: `uv run python scripts/init_database.py`
Expected: 数据库表结构更新成功。

- [ ] **Step 5: Commit**
```bash
git add pyproject.toml src/edu_info/database/schema.py
git commit -m "chore: setup scraper environment and expand schema"
```

---

### Task 2: 调度器与断点续爬系统

**Files:**
- Create: `src/edu_info/services/major_scraper/scheduler.py`
- Create: `src/edu_info/services/major_scraper/__init__.py`

- [ ] **Step 1: 实现调度逻辑**
```python
import duckdb
from datetime import datetime

class ScraperScheduler:
    def __init__(self, db_path):
        self.db_path = db_path
        
    def init_checkpoints(self):
        """将待爬取的院校同步到进度表"""
        conn = duckdb.connect(self.db_path)
        conn.execute("""
            INSERT INTO scraping_checkpoints (university_id)
            SELECT id FROM universities
            ON CONFLICT DO NOTHING
        """)
        conn.close()

    def get_next_batch(self, limit=5):
        """获取下一批待爬取的院校"""
        conn = duckdb.connect(self.db_path)
        batch = conn.execute("""
            SELECT u.id, u.name, u.code 
            FROM universities u
            JOIN scraping_checkpoints c ON u.id = c.university_id
            WHERE c.status IN ('pending', 'failed') AND c.retry_count < 3
            ORDER BY u.is_985 DESC, u.is_211 DESC, u.id ASC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return batch

    def update_status(self, uni_id, status, error_msg=None):
        """更新爬取状态"""
        conn = duckdb.connect(self.db_path)
        conn.execute("""
            UPDATE scraping_checkpoints 
            SET status = ?, error_msg = ?, last_tried_at = CURRENT_TIMESTAMP,
                retry_count = CASE WHEN ? = 'failed' THEN retry_count + 1 ELSE retry_count END
            WHERE university_id = ?
        """, (status, error_msg, status, uni_id))
        conn.commit()
        conn.close()
```
- [ ] **Step 2: 编写测试验证调度器**
Test: `tests/test_scraper_scheduler.py`
Expected: 能够正确读取院校列表并更新状态。

- [ ] **Step 3: Commit**
```bash
git add src/edu_info/services/major_scraper/
git commit -m "feat: implement scraper scheduler with checkpointing"
```

---

### Task 3: 核心爬虫引擎 (Playwright + Stealth)

**Files:**
- Create: `src/edu_info/services/major_scraper/engine.py`

- [ ] **Step 1: 实现 Playwright 基础类与 Stealth 集成**
```python
import asyncio
import random
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

class MajorScraperEngine:
    async def init_browser(self):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(headless=True)
        # 视口随机化
        width = random.randint(1280, 1920)
        height = random.randint(720, 1080)
        self.context = await self.browser.new_context(viewport={'width': width, 'height': height})

    async def scrape_university(self, uni_name):
        page = await self.context.new_page()
        await stealth_async(page)
        
        # 1. 模拟首页搜索逻辑
        await page.goto("https://gaokao.chsi.com.cn/sch/search.do")
        await page.fill("#yxmc", uni_name)
        await asyncio.sleep(random.uniform(1, 3))
        await page.click("input[type='submit']")
        
        # 2. 点击进入详情 -> 查专业
        # TODO: 具体 Selector 需根据阳光高考实时结构微调
        # 这里展示核心行为模拟逻辑
        await asyncio.sleep(random.uniform(2, 5))
        
        # 随机滚动模拟
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
        await asyncio.sleep(random.uniform(1, 2))
        
        # 3. 解析专业表格
        majors = []
        # 解析逻辑...
        
        await page.close()
        return majors
```
- [ ] **Step 2: 实现“礼貌抓取”冷却逻辑**
在引擎中增加 `adaptive_sleep(level)` 方法，根据当前状态（翻页、换校、批次结束）执行不同时长的休眠。

- [ ] **Step 3: 运行原型测试**
针对一所学校进行单点测试，验证 HTML 解析准确性。

- [ ] **Step 4: Commit**
```bash
git add src/edu_info/services/major_scraper/engine.py
git commit -m "feat: core scraper engine with behavioral simulation"
```

---

### Task 4: 数据处理器与入库同步

**Files:**
- Create: `src/edu_info/services/major_scraper/data_processor.py`

- [ ] **Step 1: 实现数据清洗逻辑**
对抓取到的专业名称进行去重、标准化。
- [ ] **Step 2: 实现批量入库**
```python
def sync_to_db(db_path, university_id, majors_list):
    conn = duckdb.connect(db_path)
    for m in majors_list:
        conn.execute("""
            INSERT INTO majors (university_id, name, category, major_class, duration, degree)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (university_id, name) DO UPDATE SET
                category = excluded.category,
                major_class = excluded.major_class
        """, (university_id, m['name'], m['category'], m['major_class'], m['duration'], m['degree']))
    conn.commit()
    conn.close()
```
- [ ] **Step 3: Commit**
```bash
git add src/edu_info/services/major_scraper/data_processor.py
git commit -m "feat: add data processor for cleaning and DB sync"
```

---

### Task 4: CLI 命令行工具与全量运行

**Files:**
- Create: `scripts/run_major_scraper.py`

- [ ] **Step 1: 编写 CLI 入口**
集成调度器、引擎和处理器，支持 `--batch-size` 和 `--limit` 参数。
- [ ] **Step 2: 验证全流程**
运行：`uv run python scripts/run_major_scraper.py --limit 3`
Expected: 能够成功爬取排名前 3 的学校并存入数据库，数据库 `majors` 表数量显著增加。

- [ ] **Step 3: Commit**
```bash
git add scripts/run_major_scraper.py
git commit -m "feat: complete major scraper CLI tool"
```

---

### 验证阶段
1. [ ] 运行 `uv run python scripts/run_major_scraper.py --limit 5`。
2. [ ] 检查数据库：`SELECT u.name, COUNT(m.id) FROM universities u JOIN majors m ON u.id = m.university_id GROUP BY u.name`。
3. [ ] 确认专业数据的真实性（名称、学制是否匹配官方）。
