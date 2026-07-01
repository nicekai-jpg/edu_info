# OpenSpec 使用指南

## 什么是 OpenSpec

OpenSpec 是一个规范驱动开发（Spec-Driven Development）框架，帮助团队在写代码前就规范达成一致。

## 核心概念

| 概念 | 说明 |
|------|------|
| **Change** | 一个变更提案，包含完整的需求、设计和任务 |
| **Proposal** | 变更提案，说明为什么做这个变更 |
| **Spec** | 规格文档，定义具体需求 |
| **Design** | 设计方案，规划技术实现 |
| **Tasks** | 任务清单，可执行的具体步骤 |

## 工作流程

### 1. 创建变更 (Propose)

```bash
# 方式 1: 使用 CLI
openspec new change "feature-name"

# 方式 2: 使用斜杠命令（Claude Code/Cursor）
/opsx:propose "描述你的需求"
```

这会创建变更目录：
```
openspec/changes/feature-name/
├── .openspec.yaml      # 变更配置
├── proposal.md         # 变更提案
├── design.md           # 设计方案（可选）
├── tasks.md            # 任务清单
└── specs/              # 规格文档
```

### 2. 编写文档

#### proposal.md 模板
```markdown
# 提案：变更标题

## Why
为什么要做这个变更？解决了什么问题？

## What Changes
具体改了什么？新增/修改/删除了哪些文件？

## 背景
项目当前状态和问题描述。

## 目标
期望达到的结果。

## 成功标准
如何验证变更已完成？
```

#### tasks.md 模板
```markdown
# 任务清单

## Phase 1: 准备
- [ ] 1.1 任务描述
  - 验收: 完成标准

## Phase 2: 实现
- [ ] 2.1 任务描述
  - 验收: 完成标准
```

### 3. 执行任务 (Apply)

```bash
# 使用斜杠命令
/opsx:apply
```

AI 会读取 `tasks.md` 并逐条执行任务。

### 4. 归档变更 (Archive)

```bash
# 方式 1: 使用 CLI
openspec archive "feature-name"

# 方式 2: 使用斜杠命令
/opsx:archive
```

变更会被移动到 `openspec/changes/archive/`

## 常用命令

| 命令 | 说明 |
|------|------|
| `openspec init` | 初始化项目 |
| `openspec new change <name>` | 创建新变更 |
| `openspec list` | 列出所有变更 |
| `openspec list --specs` | 列出所有规格 |
| `openspec show <name>` | 查看变更详情 |
| `openspec view` | 打开交互式仪表板 |
| `openspec archive <name>` | 归档变更 |
| `openspec validate` | 验证变更 |

## 最佳实践

1. **小步快跑** - 每个变更专注于一个功能点
2. **文档先行** - 先写提案和规格，再写代码
3. **验收标准** - 每个任务都有明确的验收标准
4. **及时归档** - 完成后立即归档，保持目录整洁

## 示例

### 示例：添加新功能

```bash
# 1. 创建变更
openspec new change "add-dark-mode"

# 2. 编辑 proposal.md - 说明为什么要添加暗黑模式
# 3. 编辑 specs/core-requirements.md - 定义功能需求
# 4. 编辑 design.md - 规划技术实现
# 5. 编辑 tasks.md - 列出具体任务

# 6. 执行任务
/opsx:apply

# 7. 归档
openspec archive add-dark-mode
```

## 问题排查

### 变更无法归档
- 检查 tasks.md 是否所有任务都已完成
- 检查 proposal.md 是否包含 Why 和 What Changes 章节

### 斜杠命令不可用
- 确保 OpenSpec 已初始化 (`openspec init`)
- 重启 IDE 使斜杠命令生效
