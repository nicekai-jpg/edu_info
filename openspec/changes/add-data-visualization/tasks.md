# 任务清单：添加数据可视化功能

## OpenSpec + Superpowers 结合使用示例

本变更演示如何在 OpenSpec 框架中集成 Superpowers 技能。

---

## 任务列表

### Phase 1: 需求澄清（调用 Brainstorming）
- [ ] 1.1 探索可视化需求
  - **Superpowers 技能**: `brainstorming`
  - **操作**: 运行 `Skill({"skill": "brainstorming"})`
  - **目标**: 澄清用户需要哪些图表、展示什么数据
  - **产出**: 写入 `docs/superpowers/specs/2026-05-07-data-viz-design.md`

### Phase 2: 技术方案设计
- [ ] 2.1 选择图表库
  - 对比 Plotly、Altair、Matplotlib
  - 确定使用 Plotly

- [ ] 2.2 设计图表组件接口
  - 定义 `ChartComponent` 基类
  - 设计各图表的输入输出

### Phase 3: 开发实现（结合 Superpowers）

#### 任务 3.1: 创建可视化服务
- [ ] **步骤**:
  1. 创建 `src/edu_info/services/visualization_service.py`
  2. 实现数据准备方法
  3. 使用 **TDD** 开发（调用 Superpowers）
     ```
     Skill({"skill": "test-driven-development"})
     ```

#### 任务 3.2: 创建图表组件
- [ ] **步骤**:
  1. 创建 `src/edu_info/ui/components/charts.py`
  2. 实现折线图组件
  3. 实现雷达图组件
  4. 实现柱状图组件
  5. **代码审查**: 完成后调用 `simplify` 优化代码
     ```
     Skill({"skill": "simplify"})
     ```

#### 任务 3.3: 集成到结果展示页
- [ ] **步骤**:
  1. 修改 `04_results_display.py`
  2. 添加图表展示区域
  3. **调试**: 如遇问题调用 `systematic-debugging`
     ```
     Skill({"skill": "systematic-debugging"})
     ```

### Phase 4: 测试验证（调用 TDD）
- [ ] 4.1 编写单元测试
  - **Superpowers 技能**: `test-driven-development`
  - **操作**: 运行测试，确保覆盖核心逻辑

- [ ] 4.2 端到端测试
  - 测试图表渲染
  - 测试交互功能
  - 测试导出功能

### Phase 5: 代码审查（调用 Code Review）
- [ ] 5.1 请求代码审查
  - **Superpowers 技能**: `requesting-code-review`
  - **操作**: 
    ```
    Skill({"skill": "requesting-code-review"})
    ```

- [ ] 5.2 处理审查意见
  - 根据审查反馈修改代码

### Phase 6: 完成验证
- [ ] 6.1 最终验证
  - **Superpowers 技能**: `verification-before-completion`
  - **操作**:
    ```
    Skill({"skill": "verification-before-completion"})
    ```

---

## 结合使用指南

### 何时调用 Superpowers

| OpenSpec 阶段 | 可调用 Superpowers | 目的 |
|--------------|-------------------|------|
| Proposal | brainstorming | 澄清需求 |
| Design | brainstorming | 技术方案探讨 |
| Tasks - 开发 | test-driven-development | 测试驱动开发 |
| Tasks - 开发 | systematic-debugging | 调试问题 |
| Tasks - 开发 | subagent-driven-development | 复杂功能分治 |
| Tasks - 审查 | requesting-code-review | 代码审查 |
| Tasks - 完成 | verification-before-completion | 最终验证 |

### 调用方式

在 OpenSpec 执行过程中，随时可以：

```bash
# 方式1: 直接使用 Skill 工具
Skill({"skill": "brainstorming"})

# 方式2: 使用斜杠命令（部分支持）
/opsx:apply
# 在执行中遇到需要 skill 的场景，直接调用
```

### 最佳实践

1. **不要过度使用**: 简单任务直接用 OpenSpec，复杂任务才调用 Superpowers
2. **保持上下文**: 调用 Skill 时传递足够的上下文
3. **记录调用**: 在 tasks.md 中记录何时调用了哪个 skill
4. **结果同步**: Skill 的输出要同步到 OpenSpec 文档中

---

## 执行命令

要开始执行本变更：
```bash
/opsx:apply
```

或在执行过程中随时调用 Superpowers:
```bash
Skill({"skill": "test-driven-development"})
```
