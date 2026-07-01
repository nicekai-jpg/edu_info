"""
UI 组件库

常用的 Streamlit 组件
"""
from typing import Any

import streamlit as st


def render_header(title: str, subtitle: str | None = None, icon: str = "🎓"):
    """
    渲染页面标题

    Args:
        title: 主标题
        subtitle: 副标题（可选）
        icon: 图标 emoji
    """
    st.markdown(f"# {icon} {title}")
    if subtitle:
        st.markdown(f"_{subtitle}_")
    st.markdown("---")


def render_sidebar_navigation(pages: list[dict[str, str]], default_index: int = 0) -> str:
    """
    渲染侧边栏导航

    Args:
        pages: 页面列表 [{"name": "首页", "icon": "🏠"}, ...]
        default_index: 默认选中索引

    Returns:
        选中的页面名称
    """
    st.sidebar.title("🎓 升学规划")
    st.sidebar.markdown("---")

    page_names = [f"{p['icon']} {p['name']}" for p in pages]
    selected = st.sidebar.radio("导航", page_names, index=default_index)

    st.sidebar.markdown("---")
    st.sidebar.info("版本：v0.1.0")

    return selected


def render_student_card(student_data: dict[str, Any]):
    """
    渲染学生信息卡片

    Args:
        student_data: 学生信息字典
    """
    with st.expander(f"👤 {student_data.get('name', '学生')} - {student_data.get('grade', '未知年级')}"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**基本信息**")
            st.write(f"学校：{student_data.get('school', '未知')}")
            st.write(f"城市：{student_data.get('city', '未知')}")
            st.write(f"选科：{student_data.get('category', '未知')}")

        with col2:
            st.markdown("**成绩信息**")
            st.write(f"总分：{student_data.get('total_score', 0):.1f}")
            st.write(f"位次：{student_data.get('ranking', 0)}")

        if student_data.get('interests'):
            st.markdown("**兴趣特长**")
            st.write(", ".join(student_data.get('interests', [])))


def render_route_card(route_match: dict[str, Any], rank: int = 1):
    """
    渲染路线卡片

    Args:
        route_match: 路线匹配数据
        rank: 排名
    """
    emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")

    with st.container():
        st.markdown(f"### {emoji} {route_match.get('route_name', '未知路线')}")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("匹配度", f"{route_match.get('match_score', 0):.1f}")

        with col2:
            st.metric("兴趣", f"{route_match.get('interest_score', 0):.1f}")

        with col3:
            st.metric("能力", f"{route_match.get('ability_score', 0):.1f}")

        if route_match.get('recommendations'):
            st.info(f"💡 {route_match['recommendations'][0]}")

        st.markdown("---")


def render_target_card(target: dict[str, Any], target_type: str):
    """
    渲染目标高校卡片

    Args:
        target: 目标高校数据
        target_type: 目标类型（高/中/低）
    """
    icons = {
        "高目标": "🎯",
        "中目标": "✅",
        "低目标": "📌"
    }

    colors = {
        "高目标": "red",
        "中目标": "green",
        "低目标": "blue"
    }

    icon = icons.get(target_type, "📍")
    colors.get(target_type, "gray")

    university_name = target.get('university', {}).get('name', '未知高校')
    probability = target.get('probability', 0)

    st.markdown(f"### {icon} {university_name}")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("录取概率", f"{probability:.1f}%")
        st.write(f"专业：{target.get('major', '未指定')}")

    with col2:
        if target.get('min_score'):
            st.write(f"最低分：{target['min_score']}")
        if target.get('min_rank'):
            st.write(f"最低位次：{target['min_rank']}")

    if target.get('analysis'):
        st.info(f"📊 {target['analysis']}")

    if target.get('recommendations'):
        with st.expander("💡 建议"):
            for rec in target['recommendations']:
                st.write(f"- {rec}")

    st.markdown("---")


def render_progress_step(step_name: str, completed: bool = False, current: bool = False):
    """
    渲染进度步骤

    Args:
        step_name: 步骤名称
        completed: 是否已完成
        current: 是否当前步骤
    """
    if completed:
        st.success(f"✅ {step_name}")
    elif current:
        st.info(f"🔄 {step_name}")
    else:
        st.write(f"⏳ {step_name}")


def render_empty_state(title: str, message: str, icon: str = "📭"):
    """
    渲染空状态

    Args:
        title: 标题
        message: 消息
        icon: 图标
    """
    st.markdown(f"### {icon} {title}")
    st.info(message)


def render_error_state(title: str, message: str, suggestion: str | None = None):
    """
    渲染错误状态

    Args:
        title: 标题
        message: 消息
        suggestion: 建议
    """
    st.error(f"❌ {title}")
    st.warning(message)
    if suggestion:
        st.info(f"💡 {suggestion}")


def render_loading_state(message: str = "加载中..."):
    """
    渲染加载状态

    Args:
        message: 加载消息
    """
    with st.spinner(message):
        yield


def render_data_table(data: list[dict[str, Any]], columns: list[str] | None = None):
    """
    渲染数据表格

    Args:
        data: 数据列表
        columns: 列名（可选）
    """
    if not data:
        render_empty_state("暂无数据", "暂无数据可显示")
        return

    st.dataframe(
        data,
        column_config={
            col: st.column_config.TextColumn(col)
            for col in (columns or data[0].keys())
        },
        use_container_width=True,
    )
