# 设计方案：OpenSpec 规范化流程

## 架构设计

```
edu_info/
├── openspec/                    # OpenSpec 根目录
│   ├── changes/                 # 活跃变更目录
│   │   ├── establish-openspec-workflow/  # 当前变更
│   │   │   ├── .openspec.yaml   # 变更配置
│   │   │   ├── proposal.md      # 变更提案
│   │   │   ├── design.md        # 设计方案
│   │   │   ├── tasks.md         # 任务清单
│   │   │   └── specs/           # 规格子目录
│   │   └── archive/             # 归档变更
│   └── specs/                   # 项目核心规格
│       ├── architecture.md      # 架构规格
│       ├── data-model.md        # 数据模型
│       └── api-spec.md          # API 规格
```

## 工作流程

### 1. 创建变更 (propose)
```bash
openspec new change "变更名称"
# 或
/opsx:propose "变更描述"
```

### 2. 完善文档
- 编辑 `proposal.md` - 说明为什么做
- 编辑 `specs/*.md` - 定义做什么
- 编辑 `design.md` - 规划怎么做
- 编辑 `tasks.md` - 列出具体任务

### 3. 执行任务 (apply)
```bash
/opsx:apply
```
AI 根据 tasks.md 执行任务

### 4. 归档 (archive)
```bash
openspec archive "变更名称"
# 或
/opsx:archive
```

## 与 Claude Code 集成

OpenSpec 已在 `.claude/` 目录下配置 skills 和 commands：

| 斜杠命令 | 功能 |
|----------|------|
| `/opsx:propose` | 创建新变更提案 |
| `/opsx:apply` | 执行当前变更任务 |
| `/opsx:archive` | 归档已完成变更 |

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 团队成员不熟悉流程 | 中 | 提供模板和示例 |
| 文档维护成本 | 低 | 与开发流程结合 |
| 流程过于繁琐 | 低 | 小变更可简化流程 |

## 备选方案

- **方案A**: 完整 OpenSpec 流程（推荐）
- **方案B**: 简化的 GitHub Issues + PR 流程
- **方案C**: 仅使用 AGENTS.md 记录

选择方案A因为：项目需要结构化管理，OpenSpec 提供了完整的变更生命周期管理。
