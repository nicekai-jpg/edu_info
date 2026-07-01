# 设计方案：添加数据可视化功能

## 架构设计

```
结果展示页面
    │
    ├─> VisualizationService (新增)
    │       ├─> 准备趋势图数据
    │       ├─> 准备对比图数据
    │       └─> 准备热度图数据
    │
    └─> Chart Components (新增)
            ├─> render_trend_chart()
            ├─> render_comparison_chart()
            └─> render_heatmap()
```

## 技术方案

### 1. 图表库选择
- **Plotly**: 交互性强，支持缩放、hover
- **Streamlit 集成**: `st.plotly_chart()`

### 2. 图表类型

| 图表 | 用途 | 数据 |
|------|------|------|
| 折线图 | 历年分数趋势 | 年份+分数 |
| 雷达图 | 高校多维度对比 | 综合实力、就业、学科等 |
| 柱状图 | 专业录取分数对比 | 专业+分数 |
| 散点图 | 分数vs位次分布 | 分数+位次 |

### 3. 与 Superpowers 结合点

在开发过程中，以下环节可以调用 Superpowers 技能：

1. **编写图表组件时** → 调用 `simplify` 审查代码
2. **实现复杂逻辑时** → 调用 `brainstorming` 探讨方案
3. **写测试时** → 调用 `test-driven-development`
4. **调试时** → 调用 `systematic-debugging`

## 实现步骤

1. 安装 Plotly 依赖
2. 创建可视化服务
3. 创建图表组件
4. 集成到结果展示页
5. 添加导出功能
