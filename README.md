# 升学规划咨询系统

基于国家战略发展方向，整合教育政策与高校录取数据，为初中/高中学生提供个性化升学规划方案的本地运行工具。

**当前状态**: ✅ 所有测试通过，系统功能完整（98%）  
**最后更新**: 2026-04-11

---

## 🚀 快速开始（3 分钟）

### 方式 1: 使用启动脚本（推荐）

```bash
# 一键启动应用
./scripts/start.sh
```

### 方式 2: 手动启动

```bash
# 1. 安装依赖
uv sync

# 2. 初始化数据库（首次运行）
uv run python scripts/init_database.py

# 3. 启动应用
uv run streamlit run src/edu_info/main.py --server.port=8501
```

访问：http://localhost:8501

---

## 📊 当前数据状态

数据库已包含：
- ✅ **84 所**高校（985/211/双一流）
- ✅ **173 个**专业
- ✅ **135 条**2025 年录取分数
- ✅ **2 个**学生档案示例
- ✅ **41 条**规划路线示例

---

## 📚 完整文档

| 文档 | 描述 |
|------|------|
| [📖 完整运行指南](docs/HOW_TO_RUN.md) | 详细的安装、配置、运行说明 |
| [📋 经验教训总结](docs/LESSONS_LEARNED.md) | 常见问题和解决方案 |
| [✅ 预防检查清单](docs/PREVENTION_CHECKLIST.md) | 开发各阶段的预防检查项 |
| [📊 项目状态](AGENTS.md) | 系统功能和修复记录 |
| [🔧 OpenSpec 规范](openspec/) | 项目规格和变更管理 |

---

## 🎯 主要功能

- ✅ **学生档案管理** - 创建、编辑、删除学生档案
- ✅ **数据导入** - 支持 Excel/JSON 格式数据导入
- ✅ **规划分析引擎** - 多维度匹配学生与升学路线
- ✅ **结果展示** - 三档目标高校 + 可行性评估 + 行动建议
- ✅ **数据导出** - 支持 JSON/CSV 格式导出
- ✅ **完整测试套件** - 49 个测试用例全部通过

---

## 💻 技术栈

- **Python**: 3.12+
- **包管理**: uv
- **UI 框架**: Streamlit
- **数据库**: DuckDB
- **数据处理**: Pandas
- **数据验证**: Pydantic v2

---

## 🔧 常用命令

```bash
# 启动应用
./scripts/start.sh

# 运行测试
uv run pytest tests/ -v

# 爬取 2025 年数据
uv run python scripts/data_manager.py crawl --year 2025

# 导入 2025 年数据
uv run python scripts/data_manager.py import --year 2025

# 查看数据库状态
uv run python scripts/verify_import.py

# 代码检查
uv run ruff check src/
uv run mypy src/
```

---

## 🗂️ OpenSpec 规范流程

本项目使用 [OpenSpec](https://github.com/Fission-AI/OpenSpec) 进行规范驱动的项目管理。

### 快速开始

```bash
# 创建新变更
openspec new change "feature-name"
# 或
/opsx:propose "描述你的需求"

# 执行变更任务
/opsx:apply

# 归档完成的变更
openspec archive "feature-name"
# 或
/opsx:archive
```

### 目录结构

```
openspec/
├── changes/              # 活跃变更
│   └── [change-name]/
│       ├── proposal.md   # 变更提案
│       ├── design.md     # 设计方案
│       ├── tasks.md      # 任务清单
│       └── specs/        # 规格文档
├── changes/archive/      # 归档变更
└── specs/                # 项目核心规格
    ├── architecture.md   # 架构规格
    ├── data-model.md     # 数据模型
    └── api-spec.md       # API 规格
```

### 工作流程

1. **Propose** - 创建变更提案，明确为什么做、做什么
2. **Spec** - 编写规格文档，定义需求
3. **Design** - 编写设计方案，规划怎么做
4. **Apply** - 执行任务清单，实现功能
5. **Archive** - 归档变更，更新规格

## 开发计划

- ✅ Phase 1: uv 项目搭建
- ⏳ Phase 2: 数据收集
- ⏳ Phase 3: 核心引擎
- ⏳ Phase 4: UI 完善

## 技术栈

- **Python**: 3.12+
- **包管理**: uv
- **UI 框架**: Streamlit
- **数据库**: DuckDB
- **数据处理**: Pandas

## 项目结构

```
edu_info/
├── src/edu_info/       # 源代码
├── tests/              # 测试
├── data/               # 数据目录
└── docs/               # 文档
```

## 许可证

MIT License
