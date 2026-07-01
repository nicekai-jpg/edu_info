# 🚀 升学规划系统 - 完整运行指南

**最后更新**: 2026-04-11  
**当前状态**: ✅ 所有测试通过，系统功能完整（98%）

---

## 📋 目录

1. [快速开始（5 分钟）](#快速开始 5 分钟)
2. [详细安装步骤](#详细安装步骤)
3. [数据库初始化](#数据库初始化)
4. [数据管理](#数据管理)
5. [启动应用](#启动应用)
6. [运行测试](#运行测试)
7. [常见问题](#常见问题)

---

## 快速开始（5 分钟）

### 前提条件
- Python 3.12+
- 已安装 `uv`（包管理工具）

### 一行命令安装依赖
```bash
uv sync
```

### 一行命令初始化数据库
```bash
uv run python scripts/init_database.py
```

### 一行命令启动应用
```bash
uv run streamlit run src/edu_info/main.py --server.port=8501
```

启动后访问：http://localhost:8501

---

## 详细安装步骤

### 1. 检查 Python 版本

```bash
python --version
# 应该显示 Python 3.12.x 或更高
```

如果版本过低，请升级到 Python 3.12。

### 2. 安装 uv（如果还没有）

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. 安装项目依赖

```bash
cd /Users/limingkai/nas/project/edu_info
uv sync
```

这会安装：
- **运行时依赖**: streamlit, duckdb, pandas, pydantic, pydantic-settings
- **开发依赖**: pytest, pytest-cov, ruff, mypy

### 4. 验证安装

```bash
# 检查依赖是否正确安装
uv run python -c "import streamlit; import duckdb; import pandas; print('✅ 依赖安装成功')"
```

---

## 数据库初始化

### 方式 1: 初始化示例数据库（推荐新手）

```bash
uv run python scripts/init_database.py
```

**包含内容**:
- ✅ 67 所高校（985/211/双一流）
- ✅ 2 个学生档案示例
- ✅ 41 条规划路线示例
- ✅ 6 个数据表

**验证**:
```bash
uv run python -c "
import duckdb
conn = duckdb.connect('data/duckdb/edu_planning.db')
print('高校:', conn.execute('SELECT COUNT(*) FROM universities').fetchone()[0])
print('学生:', conn.execute('SELECT COUNT(*) FROM students').fetchone()[0])
print('路线:', conn.execute('SELECT COUNT(*) FROM planning_routes').fetchone()[0])
"
```

### 方式 2: 完全重新初始化（干净环境）

```bash
# 备份现有数据库（如果需要）
cp data/duckdb/edu_planning.db data/duckdb/edu_planning.db.backup

# 删除旧数据库
rm data/duckdb/edu_planning.db

# 重新初始化
uv run python scripts/init_database.py
```

---

## 数据管理

### 查看当前数据状态

```bash
uv run python -c "
import duckdb
conn = duckdb.connect('data/duckdb/edu_planning.db')

print('=== 数据库统计 ===')
print('高校:', conn.execute('SELECT COUNT(*) FROM universities').fetchone()[0])
print('专业:', conn.execute('SELECT COUNT(*) FROM majors').fetchone()[0])
print('学生:', conn.execute('SELECT COUNT(*) FROM students').fetchone()[0])
print('2025 分数:', conn.execute('SELECT COUNT(*) FROM admission_scores WHERE year=2025').fetchone()[0])
"
```

### 爬取 2025 年数据（27 所重点高校）

```bash
# 爬取数据
uv run python scripts/data_manager.py crawl --year 2025

# 查看爬取结果
ls -lh data/raw/2025/
```

**爬取内容**:
- 27 所重点高校（C9 + 北京重点 + 辽宁周边）
- 173 个专业
- 135 条录取分数

### 导入 2025 年数据

```bash
# 导入数据库
uv run python scripts/data_manager.py import --year 2025
```

⚠️ **注意**: 如果遇到 ID 不匹配问题，参考 [`scripts/IMPORT_ISSUES.md`](scripts/IMPORT_ISSUES.md)

### 完整数据更新流程

```bash
# 1. 爬取新数据
uv run python scripts/data_manager.py crawl --year 2025

# 2. 验证数据文件
cat data/raw/2025/crawl_report_2025.json | jq

# 3. 导入数据库
uv run python scripts/data_manager.py import --year 2025

# 4. 验证导入
uv run python scripts/verify_import.py
```

---

## 启动应用

### 标准启动

```bash
uv run streamlit run src/edu_info/main.py --server.port=8501
```

### 指定端口启动

```bash
# 默认端口 8501
uv run streamlit run src/edu_info/main.py --server.port=8501

# 或其他端口
uv run streamlit run src/edu_info/main.py --server.port=8502
```

### 后台运行（可选）

```bash
# macOS/Linux
nohup uv run streamlit run src/edu_info/main.py --server.port=8501 > streamlit.log 2>&1 &

# 查看日志
tail -f streamlit.log

# 停止应用
pkill -f "streamlit run"
```

### 访问应用

启动后在浏览器访问：
- **主地址**: http://localhost:8501
- **备用地址**: http://127.0.0.1:8501

### 可用页面

1. **🏠 首页** - 系统介绍和功能导航
2. **📝 学生档案** - 学生信息管理（CRUD）
3. **📥 数据导入** - 数据上传和导入（3 个标签页）
4. **📊 规划分析** - 运行规划引擎
5. **📤 结果展示** - 查看和导出规划结果

---

## 运行测试

### 运行全部测试

```bash
uv run pytest tests/ -v
```

**期望结果**: 49 个测试用例全部通过 ✅

### 运行特定测试

```bash
# 数据库测试
uv run pytest tests/test_database.py -v

# 验证器测试
uv run pytest tests/test_validators.py -v

# 匹配引擎测试
uv run pytest tests/test_matching_engine.py -v

# 目标生成器测试
uv run pytest tests/test_target_generator.py -v

# 可行性评估测试
uv run pytest tests/test_feasibility_assessor.py -v
```

### 带覆盖率报告

```bash
uv run pytest tests/ -v --cov=src/edu_info --cov-report=html

# 在浏览器查看报告
open htmlcov/index.html
```

### 代码检查

```bash
# 代码格式化检查
uv run ruff check src/

# 类型检查
uv run mypy src/

# 自动格式化
uv run ruff format src/
```

---

## 常见问题

### Q1: 依赖安装失败

**问题**: `uv sync` 报错

**解决**:
```bash
# 清理缓存
uv cache clean

# 重新安装
uv sync --no-cache

# 使用镜像
# 已配置清华镜像，无需额外设置
```

### Q2: 数据库连接失败

**问题**: `DuckDB connection failed`

**解决**:
```bash
# 检查数据库文件是否存在
ls -lh data/duckdb/edu_planning.db

# 重新初始化数据库
rm data/duckdb/edu_planning.db
uv run python scripts/init_database.py
```

### Q3: Streamlit 启动失败

**问题**: 端口被占用或 CORS 错误

**解决**:
```bash
# 检查端口占用
lsof -i :8501

# 使用其他端口
uv run streamlit run src/edu_info/main.py --server.port=8502

# 检查配置文件
cat .streamlit/config.toml
```

### Q4: 数据导入失败

**问题**: 外键约束失败或 ID 不匹配

**解决**: 参考 [`scripts/IMPORT_ISSUES.md`](scripts/IMPORT_ISSUES.md)

**快速修复**:
```bash
# 重新初始化数据库
rm data/duckdb/edu_planning.db
uv run python scripts/init_database.py

# 立即导入 2025 年数据（在其他数据之前）
uv run python scripts/import_2025_data.py
```

### Q5: 测试失败

**问题**: `test_database.py` 失败

**解决**:
```bash
# 检查测试配置
cat tests/conftest.py

# 确保使用 mktemp() 而不是 NamedTemporaryFile
# 已在 AGENTS.md 中记录解决方案
```

### Q6: 模块导入错误

**问题**: `ModuleNotFoundError: No module named 'xxx'`

**解决**:
```bash
# 确保在项目根目录
cd /Users/limingkai/nas/project/edu_info

# 使用 uv run 运行
uv run python your_script.py

# 或者添加到 PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/Users/limingkai/nas/project/edu_info/src"
```

---

## 开发工作流

### 日常开发

```bash
# 1. 拉取最新代码
git pull

# 2. 同步依赖
uv sync

# 3. 运行测试
uv run pytest tests/ -v

# 4. 开发功能
# ... 编写代码 ...

# 5. 运行测试验证
uv run pytest tests/your_test.py -v

# 6. 代码检查
uv run ruff check src/
uv run mypy src/

# 7. 提交代码
git add .
git commit -m "描述你的改动"
git push
```

### 添加新功能

1. **创建分支**
```bash
git checkout -b feature/your-feature
```

2. **开发功能**
   - 编写代码
   - 编写测试
   - 运行测试

3. **提交前检查**
```bash
uv run pytest tests/ -v
uv run ruff check src/
uv run mypy src/
```

4. **提交代码**
```bash
git add .
git commit -m "feat: 添加 xxx 功能"
git push origin feature/your-feature
```

---

## 性能优化

### 数据库优化

```sql
-- 添加索引（在数据库工具中执行）
CREATE INDEX IF NOT EXISTS idx_scores_year ON admission_scores(year);
CREATE INDEX IF NOT EXISTS idx_scores_uni ON admission_scores(university_id);
CREATE INDEX IF NOT EXISTS idx_majors_uni ON majors(university_id);
```

### 应用优化

```bash
# 使用 SSD 存储数据库
# 数据库路径：data/duckdb/edu_planning.db

# 定期清理缓存
rm -rf .streamlit/cache/*
```

---

## 备份和恢复

### 备份数据库

```bash
# 完整备份
cp data/duckdb/edu_planning.db \
   data/duckdb/edu_planning.db.backup.$(date +%Y%m%d)

# 压缩备份
tar -czf data/duckdb/backup_$(date +%Y%m%d).tar.gz \
    data/duckdb/edu_planning.db
```

### 恢复数据库

```bash
# 从备份恢复
cp data/duckdb/edu_planning.db.backup.20260411 \
   data/duckdb/edu_planning.db

# 从压缩备份恢复
tar -xzf data/duckdb/backup_20260411.tar.gz -C data/duckdb/
```

---

## 系统要求

### 最低配置
- **CPU**: 双核处理器
- **内存**: 4GB RAM
- **存储**: 1GB 可用空间
- **Python**: 3.12+

### 推荐配置
- **CPU**: 四核处理器
- **内存**: 8GB RAM
- **存储**: SSD，5GB 可用空间
- **Python**: 3.12+

---

## 获取帮助

### 文档资源
- [项目总览](AGENTS.md) - 项目状态和功能
- [经验教训](docs/LESSONS_LEARNED.md) - 常见问题和解决方案
- [预防清单](docs/PREVENTION_CHECKLIST.md) - 开发检查清单
- [数据管理](scripts/README_DATA_MANAGEMENT.md) - 数据操作指南

### 技术支持
- 查看 [`AGENTS.md`](AGENTS.md) 了解系统状态
- 查看 [`docs/LESSONS_LEARNED.md`](docs/LESSONS_LEARNED.md) 搜索类似问题
- 运行测试验证系统状态

---

## 快速参考卡片

### 最常用命令

```bash
# 安装依赖
uv sync

# 初始化数据库
uv run python scripts/init_database.py

# 启动应用
uv run streamlit run src/edu_info/main.py --server.port=8501

# 运行测试
uv run pytest tests/ -v

# 爬取数据
uv run python scripts/data_manager.py crawl --year 2025

# 导入数据
uv run python scripts/data_manager.py import --year 2025

# 查看数据库状态
uv run python scripts/verify_import.py
```

---

**祝你使用愉快！** 🎉

如有问题，请先查看 [常见问题](#常见问题) 部分。
