# 升学规划咨询系统 / Further Education Planning & Consultation System

基于国家战略发展方向，整合教育政策与高校录取数据，为初中/高中学生提供个性化升学规划方案的本地运行工具。

A local running tool that integrates educational policies and university admission data based on national strategic development directions to provide personalized further education planning schemes for middle and high school students.

**当前状态 / Current Status**: ✅ 所有测试通过，系统功能完整（98%） / All tests passed, system features complete (98%)  
**最后更新 / Last Updated**: 2026-04-11

---

## 🚀 快速开始 / Quick Start

### 方式 1: 使用启动脚本（推荐） / Option 1: Use Startup Script (Recommended)

```bash
# 一键启动应用 / One-click start the application
./scripts/start.sh
```

### 方式 2: 手动启动 / Option 2: Manual Start

```bash
# 1. 安装依赖 / Install dependencies
uv sync

# 2. 初始化数据库（首次运行） / Initialize the database (first run)
uv run python scripts/init_database.py

# 3. 启动应用 / Start the application
uv run streamlit run src/edu_info/main.py --server.port=8501
```

访问 / Access: http://localhost:8501

---

## 📊 当前数据状态 / Current Data Status

数据库已包含 / The database already contains:
- ✅ **84 所 / 84** 高校（985/211/双一流）/ Universities (985/211/Double First-Class)
- ✅ **173 个 / 173** 专业 / Majors
- ✅ **135 条 / 135** 2025 年录取分数 / 2025 Admission scores
- ✅ **2 个 / 2** 学生档案示例 / Sample student profiles
- ✅ **41 条 / 41** 规划路线示例 / Sample planning routes

---

## 📚 完整文档 / Complete Documentation

| 文档 / Document | 描述 / Description |
|------|------|
| [📖 How-to-run Guide / 完整运行指南](docs/HOW_TO_RUN.md) | Detailed installation, configuration, and execution instructions / 详细的安装、配置、运行说明 |
| [📋 Lessons Learned / 经验教训总结](docs/LESSONS_LEARNED.md) | Common issues and solutions / 常见问题和解决方案 |
| [✅ Prevention Checklist / 预防检查清单](docs/PREVENTION_CHECKLIST.md) | Prevention check items during development phases / 开发各阶段的预防检查项 |
| [📊 Project Status / 项目状态](AGENTS.md) | System features and fix records / 系统功能 and 修复记录 |
| [🔧 OpenSpec Specification / OpenSpec 规范](openspec/) | Project specs and change management / 项目规格和变更管理 |

---

## 🎯 主要功能 / Main Features

- ✅ **学生档案管理 / Student Profile Management** - 创建、编辑、删除学生档案 / Create, edit, and delete student profiles
- ✅ **数据导入 / Data Import** - 支持 Excel/JSON 格式数据导入 / Support importing data in Excel/JSON formats
- ✅ **规划分析引擎 / Planning & Analysis Engine** - 多维度匹配学生与升学路线 / Multi-dimensionally match students with education planning routes
- ✅ **结果展示 / Results Display** - 三档目标高校 + 可行性评估 + 行动建议 / Three tiers of target universities + feasibility assessment + action recommendations
- ✅ **数据导出 / Data Export** - 支持 JSON/CSV 格式导出 / Support exporting in JSON/CSV formats
- ✅ **完整测试套件 / Full Test Suite** - 49 个测试用例全部通过 / 49 test cases all passed

---

## 💻 技术栈 / Tech Stack

- **Python**: 3.12+
- **包管理 / Package Management**: uv
- **UI 框架 / UI Framework**: Streamlit
- **数据库 / Database**: DuckDB
- **数据处理 / Data Processing**: Pandas
- **数据验证 / Data Validation**: Pydantic v2

---

## 🔧 常用命令 / Common Commands

```bash
# 启动应用 / Start the application
./scripts/start.sh

# 运行测试 / Run tests
uv run pytest tests/ -v

# 爬取 2025 年数据 / Crawl 2025 data
uv run python scripts/data_manager.py crawl --year 2025

# 导入 2025 年数据 / Import 2025 data
uv run python scripts/data_manager.py import --year 2025

# 查看数据库状态 / Check database status
uv run python scripts/verify_import.py

# 代码检查 / Code checking (lint & type checks)
uv run ruff check src/
uv run mypy src/
```

---

## 🗂️ OpenSpec 规范流程 / OpenSpec Workflow

本项目使用 [OpenSpec](https://github.com/Fission-AI/OpenSpec) 进行规范驱动的项目管理。  
This project uses [OpenSpec](https://github.com/Fission-AI/OpenSpec) for specification-driven project management.

### 快速开始 / Quick Start

```bash
# 创建新变更 / Create new change
openspec new change "feature-name"
# 或 / or
/opsx:propose "描述你的需求 / Describe your requirements"

# 执行变更任务 / Apply change tasks
/opsx:apply

# 归档完成的变更 / Archive completed change
openspec archive "feature-name"
# 或 / or
/opsx:archive
```

### 目录结构 / Directory Structure

```
openspec/
├── changes/              # 活跃变更 / Active changes
│   └── [change-name]/
│       ├── proposal.md   # 变更提案 / Change proposal
│       ├── design.md     # 设计方案 / Design specification
│       ├── tasks.md      # 任务清单 / Tasks checklist
│       └── specs/        # 规格文档 / Spec documents
├── changes/archive/      # 归档变更 / Archived changes
└── specs/                # 项目核心规格 / Core project specs
    ├── architecture.md   # 架构规格 / Architectural spec
    ├── data-model.md     # 数据模型 / Data model
    └── api-spec.md       # API 规格 / API spec
```

### 工作流程 / Workflow

1. **Propose** - 创建变更提案，明确为什么做、做什么 / Create change proposal, clarify why and what to do
2. **Spec** - 编写规格文档，定义需求 / Write specification documents to define requirements
3. **Design** - 编写设计方案，规划怎么做 / Write design document to plan how to do it
4. **Apply** - 执行任务清单，实现功能 / Execute task checklist to implement features
5. **Archive** - 归档变更，更新规格 / Archive change and update core specs

---

## 📅 开发计划 / Development Roadmap

- ✅ Phase 1: uv 项目搭建 / uv Project Setup
- ⏳ Phase 2: 数据收集 / Data Collection
- ⏳ Phase 3: 核心引擎 / Core Engine
- ⏳ Phase 4: UI 完善 / UI Refinement

---

## 📂 项目结构 / Project Structure

```
edu_info/
├── src/edu_info/       # 源代码 / Source code
├── tests/              # Tests / 测试
├── data/               # Data directory / 数据目录
└── docs/               # 文档 / Documentation
```

---

## 📄 许可证 / License

MIT License
