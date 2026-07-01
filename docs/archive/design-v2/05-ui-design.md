# 05 - 用户交互设计

## 1. 界面结构

### 1.1 页面导航

```
升学规划系统
│
├── 🏠 首页
│   ├─ 系统概览
│   ├─ 快速入口
│   └─ 最近使用
│
├── 📊 数据管理
│   ├─ 分数线导入
│   ├─ 政策文件导入
│   ├─ 数据查看
│   └─ 数据更新
│
├── 👤 学生管理
│   ├─ 学生列表
│   ├─ 新建学生档案
│   └─ 学生画像编辑
│
├── 🎯 规划分析
│   ├─ 选择学生
│   ├─ 运行分析
│   └─ 查看结果
│
├── 📄 规划报告
│   ├─ 报告列表
│   ├─ 查看报告
│   └─ 导出报告
│
└── ⚙️ 系统设置
    ├─ 参数配置
    └─ 关于系统
```

## 2. 核心页面设计

### 2.1 首页

```python
# ui/home.py
import streamlit as st

def render_home():
    """渲染首页"""
    
    # 标题区域
    st.title("🎓 智能升学规划系统")
    st.markdown("---")
    
    # 系统介绍
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        ### 系统功能
        - 🔍 **突破口识别**: 基于国家战略识别未来发展方向
        - 📋 **政策匹配**: 找到适合的升学途径
        - 🎓 **专业推荐**: 推荐与突破口相关的专业
        - 🏫 **高校筛选**: 生成高/中/低三档目标
        - 📊 **可行性评估**: 评估达成目标的可能性
        - 📝 **备选方案**: 提供调整建议
        """)
    
    with col2:
        # 快捷统计
        st.metric("已录入学生", len(get_students()))
        st.metric("已生成方案", len(get_plans()))
        st.metric("数据库高校", get_university_count())
    
    st.markdown("---")
    
    # 快速入口
    st.subheader("快速入口")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ 新建学生档案", use_container_width=True):
            st.session_state.page = 'profile_create'
            st.rerun()
    
    with col2:
        if st.button("🎯 运行规划分析", use_container_width=True):
            st.session_state.page = 'analysis'
            st.rerun()
    
    with col3:
        if st.button("📊 导入分数线", use_container_width=True):
            st.session_state.page = 'data_import'
            st.rerun()
    
    with col4:
        if st.button("📄 查看报告", use_container_width=True):
            st.session_state.page = 'reports'
            st.rerun()
    
    st.markdown("---")
    
    # 最近使用
    st.subheader("最近使用")
    recent_students = get_recent_students(limit=5)
    if recent_students:
        for student in recent_students:
            with st.container():
                cols = st.columns([3, 2, 1])
                with cols[0]:
                    st.write(f"**{student['name']}** - {student['grade']}")
                with cols[1]:
                    st.write(f"最近分析: {student['last_analysis']}")
                with cols[2]:
                    if st.button("查看", key=f"view_{student['id']}"):
                        st.session_state.selected_student = student['id']
                        st.session_state.page = 'results'
                        st.rerun()
    else:
        st.info("暂无最近记录")
```

### 2.2 学生档案创建页

```python
# ui/profile_edit.py
import streamlit as st

def render_profile_create():
    """渲染学生档案创建页"""
    
    st.title("👤 新建学生档案")
    st.markdown("---")
    
    # 基本信息
    st.subheader("基本信息")
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("学生姓名", placeholder="请输入姓名")
        grade = st.selectbox(
            "当前年级",
            ["初一", "初二", "初三", "高一", "高二", "高三"]
        )
    
    with col2:
        school = st.text_input("所在学校", placeholder="请输入学校名称")
        city = st.selectbox(
            "所在城市",
            ["沈阳市", "大连市", "鞍山市", "抚顺市", "本溪市", "丹东市", "锦州市", "营口市", "阜新市", "辽阳市", "盘锦市", "铁岭市", "朝阳市", "葫芦岛市"]
        )
    
    st.markdown("---")
    
    # 学业情况
    st.subheader("学业情况")
    
    # 成绩输入（根据年级显示不同）
    if grade in ["初一", "初二", "初三"]:
        st.write("初中成绩（百分制）")
        cols = st.columns(4)
        scores = {}
        with cols[0]:
            scores['语文'] = st.number_input("语文", 0, 100, 80)
        with cols[1]:
            scores['数学'] = st.number_input("数学", 0, 100, 80)
        with cols[2]:
            scores['英语'] = st.number_input("英语", 0, 100, 80)
        with cols[3]:
            scores['物理'] = st.number_input("物理", 0, 100, 80)
    else:
        st.write("高中成绩（满分750）")
        total_score = st.number_input("总分", 0, 750, 550)
        rank = st.number_input("全省位次（如知道）", 0, 300000, 50000)
    
    overall_level = st.select_slider(
        "综合学业水平",
        options=["C", "B", "B+", "A", "A+"],
        value="B+"
    )
    
    st.markdown("---")
    
    # 兴趣特长
    st.subheader("兴趣与特长")
    
    interests = st.multiselect(
        "兴趣领域",
        ["计算机/编程", "数学", "物理", "化学", "生物", 
         "文学/写作", "历史", "地理", "政治",
         "音乐", "美术", "舞蹈", "体育",
         "机械/工程", "医学", "经济/金融", "法律"]
    )
    
    special_talents = st.multiselect(
        "特长（可多选）",
        ["信息学竞赛", "数学竞赛", "物理竞赛", "化学竞赛", "生物竞赛",
         "科技创新", "机器人", "音乐演奏", "声乐", "绘画", "书法",
         "舞蹈", "体育专项", "写作", "演讲"]
    )
    
    # 竞赛获奖
    has_competition = st.checkbox("有竞赛获奖")
    if has_competition:
        st.write("竞赛获奖情况")
        comp_cols = st.columns(3)
        with comp_cols[0]:
            comp_name = st.text_input("竞赛名称")
        with comp_cols[1]:
            comp_level = st.selectbox("获奖级别", ["国家级", "省级", "市级", "校级"])
        with comp_cols[2]:
            comp_rank = st.selectbox("奖项等级", ["一等奖", "二等奖", "三等奖", "优秀奖"])
    
    st.markdown("---")
    
    # 家庭条件与期望
    st.subheader("家庭条件与期望")
    
    col1, col2 = st.columns(2)
    with col1:
        preferred_regions = st.multiselect(
            "期望就读地区",
            ["辽宁省内", "北京", "上海", "天津", "江苏", "浙江", "广东", 
             "其他省份", "不限"],
            default=["辽宁省内", "北京", "天津"]
        )
    
    with col2:
        target_preference = st.radio(
            "目标偏好",
            ["稳妥为主（优先确保录取）", "平衡选择（兼顾理想与现实）", "冲刺为主（追求更好学校）"]
        )
    
    st.markdown("---")
    
    # 保存按钮
    if st.button("💾 保存学生档案", type="primary"):
        # 保存逻辑
        profile = {
            'name': name,
            'grade': grade,
            'school': school,
            'city': city,
            'scores': scores if grade in ["初一", "初二", "初三"] else {'total': total_score, 'rank': rank},
            'overall_level': overall_level,
            'interests': interests,
            'special_talents': special_talents,
            'preferred_regions': preferred_regions,
            'target_preference': target_preference
        }
        
        save_student_profile(profile)
        st.success("✅ 学生档案保存成功！")
        
        # 跳转到分析页面
        if st.button("🎯 立即进行规划分析"):
            st.session_state.page = 'analysis'
            st.rerun()
```

### 2.3 规划分析页

```python
# ui/analysis.py
import streamlit as st
import time

def render_analysis():
    """渲染规划分析页"""
    
    st.title("🎯 规划分析")
    st.markdown("---")
    
    # 选择学生
    students = get_students()
    if not students:
        st.warning("⚠️ 还没有学生档案，请先创建学生档案")
        if st.button("➕ 新建学生档案"):
            st.session_state.page = 'profile_create'
            st.rerun()
        return
    
    selected_student = st.selectbox(
        "选择学生",
        options=students,
        format_func=lambda x: f"{x['name']} - {x['grade']} - {x['school']}"
    )
    
    if not selected_student:
        return
    
    st.markdown("---")
    
    # 显示学生概览
    st.subheader("学生概览")
    
    cols = st.columns(4)
    with cols[0]:
        st.metric("姓名", selected_student['name'])
    with cols[1]:
        st.metric("年级", selected_student['grade'])
    with cols[2]:
        st.metric("学业水平", selected_student['overall_level'])
    with cols[3]:
        st.metric("兴趣领域", len(selected_student['interests']))
    
    # 显示详情
    with st.expander("查看学生详细信息"):
        st.json(selected_student)
    
    st.markdown("---")
    
    # 分析选项
    st.subheader("分析选项")
    
    analysis_depth = st.radio(
        "分析深度",
        ["快速分析（2分钟）", "标准分析（5分钟）", "深度分析（10分钟）"],
        index=1
    )
    
    include_reasoning = st.checkbox("生成详细的推荐理由", value=True)
    generate_alternatives = st.checkbox("生成备选方案", value=True)
    
    st.markdown("---")
    
    # 运行分析按钮
    if st.button("🚀 开始规划分析", type="primary", use_container_width=True):
        # 显示进度
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 模拟分析过程
        steps = [
            "正在识别突破口...",
            "正在匹配政策...",
            "正在推荐专业...",
            "正在筛选高校...",
            "正在评估可行性...",
            "正在生成备选方案...",
            "正在生成报告..."
        ]
        
        for i, step in enumerate(steps):
            status_text.text(step)
            progress_bar.progress((i + 1) / len(steps))
            time.sleep(0.5)  # 模拟耗时
        
        # 实际运行分析
        try:
            result = run_planning_analysis(
                selected_student,
                depth=analysis_depth,
                include_reasoning=include_reasoning,
                generate_alternatives=generate_alternatives
            )
            
            # 保存结果
            save_plan_result(selected_student['id'], result)
            
            progress_bar.empty()
            status_text.empty()
            
            st.success("✅ 分析完成！")
            
            # 显示结果摘要
            st.subheader("分析结果摘要")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("识别的突破口", len(result['breakthroughs']))
            with col2:
                st.metric("适用的升学途径", len(result['admission_paths']))
            with col3:
                st.metric("推荐目标高校", len(result['high_targets']) + len(result['medium_targets']) + len(result['low_targets']))
            
            # 显示突破口
            st.subheader("🎯 识别的突破口")
            for i, bt in enumerate(result['breakthroughs'][:3]):
                with st.container():
                    cols = st.columns([4, 1])
                    with cols[0]:
                        st.write(f"**{i+1}. {bt['name']}**")
                        st.caption(bt['description'])
                    with cols[1]:
                        st.progress(bt['overall_score'] / 100)
                        st.caption(f"匹配度: {bt['overall_score']:.0f}%")
            
            # 查看完整报告按钮
            if st.button("📄 查看完整规划报告"):
                st.session_state.plan_result = result
                st.session_state.page = 'results'
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ 分析失败: {str(e)}")
            st.info("请检查数据是否完整，或联系技术支持")
```

### 2.4 结果展示页

```python
# ui/results.py
import streamlit as st
import plotly.graph_objects as go

def render_results():
    """渲染结果展示页"""
    
    result = st.session_state.get('plan_result')
    if not result:
        st.warning("请先运行规划分析")
        return
    
    st.title("📊 规划分析报告")
    st.markdown("---")
    
    # 导出按钮
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("📥 导出PDF"):
            export_pdf(result)
            st.success("报告已导出")
    
    # 总体概览
    st.header("📋 总体概览")
    
    # 突破口
    st.subheader("🎯 识别的突破口方向")
    for bt in result['breakthroughs']:
        with st.expander(f"{bt['name']} (匹配度: {bt['overall_score']:.0f}%)"):
            st.write(bt['description'])
            st.write(f"**支持政策**: {', '.join(bt['supporting_policies'])}")
            st.write(f"**相关产业**: {', '.join(bt['related_industries'])}")
    
    st.markdown("---")
    
    # 升学途径
    st.subheader("🎓 适用的升学途径")
    for path in result['admission_paths']:
        with st.container():
            cols = st.columns([1, 3])
            with cols[0]:
                st.write(f"**{path['name']}**")
            with cols[1]:
                st.write(path['description'])
                st.caption(f"要求: {path['requirements']}")
    
    st.markdown("---")
    
    # 三档目标
    st.header("🏫 目标高校（三档）")
    
    tabs = st.tabs(["🎯 冲刺档 (高目标)", "⚖️ 稳妥档 (中目标)", "🛡️ 保底档 (低目标)"])
    
    # 冲刺档
    with tabs[0]:
        st.info("录取概率: 20-40% | 需要付出较大努力，但值得尝试")
        for i, target in enumerate(result['high_targets'][:5]):
            with st.container():
                cols = st.columns([4, 2, 2, 2])
                with cols[0]:
                    st.write(f"**{i+1}. {target['university_name']}**")
                    st.caption(f"{target['major_name']}")
                with cols[1]:
                    st.metric("录取概率", f"{target['probability']*100:.0f}%")
                with cols[2]:
                    st.metric("近年最低分", target['min_score'])
                with cols[3]:
                    st.write(f"位次: {target['min_rank']}")
    
    # 稳妥档
    with tabs[1]:
        st.success("录取概率: 50-70% | 平衡理想与现实，推荐重点考虑")
        for i, target in enumerate(result['medium_targets'][:5]):
            with st.container():
                cols = st.columns([4, 2, 2, 2])
                with cols[0]:
                    st.write(f"**{i+1}. {target['university_name']}**")
                    st.caption(f"{target['major_name']}")
                with cols[1]:
                    st.metric("录取概率", f"{target['probability']*100:.0f}%")
                with cols[2]:
                    st.metric("近年最低分", target['min_score'])
                with cols[3]:
                    st.write(f"位次: {target['min_rank']}")
    
    # 保底档
    with tabs[2]:
        st.warning("录取概率: 80%+ | 确保有学上，作为安全网")
        for i, target in enumerate(result['low_targets'][:5]):
            with st.container():
                cols = st.columns([4, 2, 2, 2])
                with cols[0]:
                    st.write(f"**{i+1}. {target['university_name']}**")
                    st.caption(f"{target['major_name']}")
                with cols[1]:
                    st.metric("录取概率", f"{target['probability']*100:.0f}%")
                with cols[2]:
                    st.metric("近年最低分", target['min_score'])
                with cols[3]:
                    st.write(f"位次: {target['min_rank']}")
    
    st.markdown("---")
    
    # 可行性评估
    st.header("📊 可行性评估")
    
    feasibility = result['feasibility']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("高目标可行性", 
                 "✅ 可行" if feasibility['high']['feasible'] else "❌ 需调整",
                 f"{feasibility['high']['feasibility_score']:.0f}分")
    with col2:
        st.metric("中目标可行性", 
                 "✅ 可行" if feasibility['medium']['feasible'] else "⚠️ 需努力",
                 f"feasibility['medium']['feasibility_score']:.0f}分")
    with col3:
        st.metric("低目标可行性", 
                 "✅ 可行" if feasibility['low']['feasible'] else "✅ 稳妥",
                 f"{feasibility['low']['feasibility_score']:.0f}分")
    
    # 详细评估
    with st.expander("查看详细评估"):
        st.write("**需要提升的方面**:")
        for improvement in feasibility['high'].get('required_improvements', []):
            st.write(f"- {improvement}")
    
    st.markdown("---")
    
    # 备选方案
    if result.get('alternatives'):
        st.header("🔄 备选方案")
        for alt in result['alternatives']:
            with st.expander(f"{alt['description']}"):
                st.write(f"**调整策略**: {alt['type']}")
                st.write(f"**可行性提升**: {alt['feasibility_improvement']}")
                st.write("**权衡因素**:")
                for trade in alt['trade_offs']:
                    st.write(f"- {trade}")
    
    st.markdown("---")
    
    # 行动建议
    st.header("📝 行动建议")
    
    action_plan = result['action_plan']
    
    # 近期行动
    st.subheader("近期行动（本学期）")
    for action in action_plan.get('short_term', []):
        st.checkbox(action, key=f"short_{action}")
    
    # 中期行动
    st.subheader("中期行动（本学年）")
    for action in action_plan.get('medium_term', []):
        st.checkbox(action, key=f"medium_{action}")
    
    # 长期行动
    st.subheader("长期行动（初中/高中阶段）")
    for action in action_plan.get('long_term', []):
        st.checkbox(action, key=f"long_{action}")
```

## 3. 交互设计原则

### 3.1 用户体验设计

```
设计原则:
1. 简洁明了: 每页只有一个核心任务
2. 逐步引导: 复杂操作分步进行
3. 即时反馈: 操作后立即显示结果
4. 数据可视化: 用图表代替纯文字
5. 容错设计: 提供撤销和修改功能
```

### 3.2 视觉设计

```python
# 统一的主题配置
theme_config = {
    "primaryColor": "#1890ff",  # 主色：蓝色
    "backgroundColor": "#ffffff",
    "secondaryBackgroundColor": "#f0f2f5",
    "textColor": "#262730",
    "font": "sans-serif"
}

# 颜色语义
colors = {
    "success": "#52c41a",      # 绿色 - 可行/成功
    "warning": "#faad14",      # 橙色 - 警告/注意
    "error": "#f5222d",        # 红色 - 错误/高风险
    "info": "#1890ff",         # 蓝色 - 信息
    "high_target": "#ff4d4f",  # 红色 - 冲刺档
    "medium_target": "#52c41a", # 绿色 - 稳妥档
    "low_target": "#1890ff",   # 蓝色 - 保底档
}
```

---

*用户交互设计 v2.0*
