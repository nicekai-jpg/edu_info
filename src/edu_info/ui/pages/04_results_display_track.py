"""
结果展示页面 - 赛道体系版

展示完整的升学规划结果（赛道导向），包括：
1. 学生画像总览
2. 赛道匹配总览（按领域分组）
3. 赛道详情（匹配理由、行动建议、差距分析）
4. 可视化图表
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from edu_info.data.repositories.track_repository import TrackRepository
from edu_info.ui.components.common import (
    render_empty_state,
    render_header,
)
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


def render_student_profile(student: dict[str, Any]):
    """渲染学生画像总览"""
    st.markdown("### 👤 学生画像")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "📊 成绩水平",
            f"{student.get('total_score', 0):.1f}分",
            f"排名{student.get('ranking', 0)}"
        )

    with col2:
        interests = student.get('interests', [])
        interest_text = ', '.join(interests[:2]) if interests else "未填写"
        st.metric("❤️ 兴趣方向", interest_text)

    with col3:
        specialities = student.get('specialities', [])
        spec_text = ', '.join(specialities[:2]) if specialities else "未填写"
        st.metric("🏆 特长奖项", spec_text)

    with col4:
        budget = student.get('family_budget', 0)
        st.metric("💰 家庭预算", f"{budget}万/年")

    with col5:
        locations = student.get('preferred_locations', [])
        loc_text = ', '.join(locations[:2]) if locations else "无偏好"
        st.metric("📍 地域偏好", loc_text)


def render_domain_tabs(domains_data: dict[str, list[dict]]):
    """渲染领域标签页"""
    if not domains_data:
        return

    # 创建领域标签页
    domain_names = list(domains_data.keys())
    tabs = st.tabs(domain_names)

    for i, domain_name in enumerate(domain_names):
        with tabs[i]:
            st.markdown(f"#### {domain_name} 领域赛道")

            # 获取该领域赛道数据
            domain_tracks = domains_data.get(domain_name, [])

            # 按匹配度排序
            tracks_sorted: list[dict[str, Any]] = sorted(domain_tracks, key=lambda x: x.get('match_score', 0), reverse=True)

            for track in tracks_sorted:
                render_track_card(track)


def render_track_card(track: dict[str, Any]):
    """渲染赛道卡片"""
    track_name = track.get('track_name', '未知赛道')
    match_score = track.get('match_score', 0)

    with st.container():
        # 赛道名称和匹配度
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"##### 🎯 {track_name}")

        with col2:
            st.metric("匹配度", f"{match_score:.1f}")
            st.progress(match_score / 100)

        # 五维分析
        dimensions = track.get('dimensions', {})

        col_d1, col_d2, col_d3, col_d4, col_d5 = st.columns(5)

        with col_d1:
            st.write(f"❤️ 兴趣：{dimensions.get('interest', 0):.1f}")

        with col_d2:
            st.write(f"📚 能力：{dimensions.get('ability', 0):.1f}")

        with col_d3:
            st.write(f"💰 经济：{dimensions.get('economic', 0):.1f}")

        with col_d4:
            st.write(f"⏰ 时间：{dimensions.get('time', 0):.1f}")

        with col_d5:
            st.write(f"📍 地域：{dimensions.get('region', 0):.1f}")

        # 匹配理由
        matching_reasons = track.get('matching_reasons', {})
        if matching_reasons:
            with st.expander("📝 匹配理由"):
                for _dim_name, dim_data in matching_reasons.items():
                    if isinstance(dim_data, dict):
                        comment = dim_data.get('comment', '')
                        if comment:
                            st.write(f"- {comment}")

        # 行动建议
        action_items = track.get('action_items', [])
        if action_items:
            with st.expander("📋 行动建议"):
                for item in action_items:
                    st.write(f"- {item}")

        # 差距分析
        gaps = track.get('gaps', [])
        if gaps:
            with st.expander("⚠️ 差距分析"):
                for gap in gaps:
                    priority = gap.get('priority', 'medium')
                    icon = "🔴" if priority == 'high' else "🟡"
                    st.write(f"{icon} {gap.get('description', '')}")

        st.divider()


def render_track_details(track: dict[str, Any]):
    """渲染赛道详情"""
    track_name = track.get('track_name', '未知赛道')
    track_id = track.get('track_id')

    st.markdown(f"### 🎯 {track_name}")

    # 赛道基本信息
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 匹配分析")

        dimensions = track.get('dimensions', {})

        # 雷达图数据
        radar_data = {
            "兴趣": dimensions.get('interest', 0),
            "能力": dimensions.get('ability', 0),
            "经济": dimensions.get('economic', 0),
            "时间": dimensions.get('time', 0),
            "地域": dimensions.get('region', 0),
        }

        # 显示雷达图数据（文本形式）
        for dim_name, score in radar_data.items():
            st.write(f"{dim_name}: {score:.1f}")
            st.progress(score / 100)

    with col2:
        st.markdown("#### 💡 匹配理由")

        matching_reasons = track.get('matching_reasons', {})
        for dim_name, dim_data in matching_reasons.items():
            if isinstance(dim_data, dict):
                score = dim_data.get('score', 0)
                comment = dim_data.get('comment', '')
                st.write(f"**{dim_name}** ({score:.1f}分): {comment}")

    st.divider()

    # 核心链路：赛道→专业类别→院校
    st.markdown("### 🎓 赛道支撑体系")

    if track_id:
        from edu_info.data.repositories.track_repository import TrackRepository
        track_repo = TrackRepository()

        # 获取赛道的专业类别
        categories = track_repo.get_track_categories(track_id)

        if categories:
            st.markdown("#### 专业类别映射")

            for i, category in enumerate(categories, 1):
                with st.expander(f"**{i}. {category.category_name}** - {category.description or ''}", expanded=(i==1)):
                    # 映射类型
                    mapping_info = track_repo.get_track_category_mapping(track_id, category.category_id)
                    if mapping_info:
                        mapping_type = mapping_info.get('mapping_type', '未知')
                        shared_ratio = mapping_info.get('shared_courses_ratio', 0)
                        conversion_cost = mapping_info.get('conversion_cost', '未知')
                        skill_gap = mapping_info.get('skill_gap', [])

                        col_m1, col_m2 = st.columns(2)
                        with col_m1:
                            st.metric("映射类型", mapping_type)
                            st.metric("课程共享度", f"{shared_ratio*100:.0f}%")
                        with col_m2:
                            st.metric("转换成本", conversion_cost)

                        if skill_gap:
                            st.write("**需补充技能**:")
                            st.write(", ".join(skill_gap))

                    # 核心课程
                    if category.core_courses:
                        st.write("**核心课程**:")
                        st.write(", ".join(category.core_courses))

                    # 推荐院校
                    st.markdown("**🏫 推荐院校**:")

                    conn = track_repo._get_connection()
                    try:
                        results = conn.execute("""
                            SELECT u.university_name, tuc.competitiveness_level,
                                   tuc.overall_score, tuc.track_ranking,
                                   tuc.discipline_grade, tuc.employment_rate, tuc.avg_salary
                            FROM track_university_competitiveness tuc
                            JOIN universities u ON tuc.university_id = u.university_id
                            WHERE tuc.track_id = ? AND tuc.category_id = ?
                            ORDER BY tuc.overall_score DESC
                            LIMIT 20
                        """, [track_id, category.category_id]).fetchall()

                        if results:
                            # 按竞争力分组
                            tier_a_plus = [r for r in results if r[1] == 'A+']
                            tier_a = [r for r in results if r[1] == 'A']
                            tier_b_plus = [r for r in results if r[1] == 'B+']

                            if tier_a_plus:
                                st.write("**🏆 第一梯队（A+ 院校）**:")
                                for j, (uni_name, level, score, _ranking, disc_grade, emp_rate, salary) in enumerate(tier_a_plus[:5], 1):
                                    st.write(f"{j}. **{uni_name}** - {level} (综合：{score:.1f}, 学科：{disc_grade})")
                                    if emp_rate:
                                        st.write(f"   - 就业率：{emp_rate:.1f}%, 平均薪资：{salary/10000:.1f}万/年")

                            if tier_a:
                                st.write("**🥇 第二梯队（A 院校）**:")
                                for j, (uni_name, level, score, _ranking, disc_grade, emp_rate, salary) in enumerate(tier_a[:5], 1):
                                    st.write(f"{j}. **{uni_name}** - {level} (综合：{score:.1f}, 学科：{disc_grade})")
                                    if emp_rate:
                                        st.write(f"   - 就业率：{emp_rate:.1f}%, 平均薪资：{salary/10000:.1f}万/年")

                            if tier_b_plus:
                                st.write("**🥈 第三梯队（B+ 院校）**:")
                                for j, (uni_name, level, score, _ranking, disc_grade, emp_rate, salary) in enumerate(tier_b_plus[:5], 1):
                                    st.write(f"{j}. **{uni_name}** - {level} (综合：{score:.1f}, 学科：{disc_grade})")
                                    if emp_rate:
                                        st.write(f"   - 就业率：{emp_rate:.1f}%, 平均薪资：{salary/10000:.1f}万/年")
                        else:
                            st.info("暂无院校竞争力数据，后续会补充")
                    finally:
                        conn.close()
        else:
            st.info("暂无专业类别映射数据")

    st.divider()

    # 行动建议
    action_items = track.get('action_items', [])
    if action_items:
        st.markdown("#### 📋 行动建议")
        for i, item in enumerate(action_items, 1):
            st.write(f"{i}. {item}")

    # 差距分析
    gaps = track.get('gaps', [])
    if gaps:
        st.markdown("#### ⚠️ 差距分析")
        for gap in gaps:
            priority = gap.get('priority', 'medium')
            icon = "🔴" if priority == 'high' else "🟡"
            st.write(f"{icon} {gap.get('description', '')}")


def main():
    """主函数"""
    render_header("结果展示", "查看完整的升学规划结果")

    # 初始化 session state
    if "planning_result" not in st.session_state:
        st.session_state.planning_result = None

    # 检查是否有规划结果
    if not st.session_state.planning_result:
        render_empty_state(
            "暂无规划结果",
            '请先在"规划分析"页面运行规划分析',
            icon="📭"
        )

        if st.button("前往规划分析", type="primary"):
            st.session_state.current_page = "规划分析"
            st.rerun()

        return

    # 获取规划结果
    result = st.session_state.planning_result

    # 检查是否使用赛道模式
    if not result.get("is_track_mode", False):
        st.warning("当前使用的是旧版路线模式，请重新运行规划分析以使用赛道模式")
        return

    # 1. 学生画像总览
    student = result.get('student', {})
    render_student_profile(student)

    st.divider()

    # 2. 赛道匹配总览（按领域分组）
    st.markdown("### 🎯 赛道匹配总览")

    # 获取赛道数据
    top_tracks = result.get('top_tracks', [])

    if not top_tracks:
        st.info("暂无赛道推荐数据")
        return

    # 按领域分组（这里简化处理，实际应从 Track 对象获取领域信息）
    track_repo = TrackRepository()
    all_tracks = track_repo.get_all_tracks()

    # 构建 track_id 到 track 对象的映射
    track_map = {t.track_id: t for t in all_tracks}

    # 按领域分组
    domains_data = {}
    for track_data in top_tracks:
        track_id = track_data.get('track_id')
        track_obj = track_map.get(track_id)

        if track_obj and track_obj.domains:
            # 使用主属领域
            domain_name = track_obj.domains[0].domain_name
        else:
            domain_name = "其他"

        if domain_name not in domains_data:
            domains_data[domain_name] = []
        domains_data[domain_name].append(track_data)

    # 渲染领域标签页
    render_domain_tabs(domains_data)

    st.divider()

    # 3. 赛道详情（用户选择查看）
    st.markdown("### 📊 赛道详情")

    track_options = {
        f"{t['track_name']} (匹配度{t['match_score']:.1f})": t
        for t in top_tracks
    }

    selected_track_name = st.selectbox(
        "选择要查看的赛道",
        list(track_options.keys())
    )

    if selected_track_name:
        selected_track = track_options[selected_track_name]
        render_track_details(selected_track)

    # 4. 导出功能
    st.divider()

    st.markdown("### 💾 导出结果")

    col1, col2, col3 = st.columns(3)

    with col1:
        # JSON 导出
        json_data = json.dumps(result, ensure_ascii=False, indent=2, default=str)
        st.download_button(
            label="📄 下载 JSON",
            data=json_data,
            file_name=f"planning_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

    with col2:
        # 简单文本报告
        report_text = generate_text_report(result)
        st.download_button(
            label="📝 下载文本报告",
            data=report_text,
            file_name=f"planning_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )

    with col3:
        st.button(
            "🔄 重新分析",
            use_container_width=True,
            on_click=lambda: setattr(st.session_state, 'planning_result', None)
        )


def generate_text_report(result: dict[str, Any]) -> str:
    """生成文本报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("升学规划报告（赛道体系）")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")

    # 学生信息
    student = result.get('student', {})
    lines.append("👤 学生信息")
    lines.append(f"姓名：{student.get('name', '未知')}")
    lines.append(f"年级：{student.get('grade', '未知')}")
    lines.append(f"学校：{student.get('school', '未知')}")
    lines.append(f"总分：{student.get('total_score', 0):.1f}分")
    lines.append(f"排名：{student.get('ranking', 0)}")
    lines.append("")

    # 赛道推荐
    lines.append("🎯 推荐赛道")
    lines.append("-" * 60)

    top_tracks = result.get('top_tracks', [])
    for i, track in enumerate(top_tracks[:10], 1):
        lines.append(f"\nTop {i}: {track.get('track_name', '未知')}")
        lines.append(f"匹配度：{track.get('match_score', 0):.1f}分")

        # 五维分析
        dimensions = track.get('dimensions', {})
        lines.append(f"兴趣：{dimensions.get('interest', 0):.1f} | ")
        lines.append(f"能力：{dimensions.get('ability', 0):.1f} | ")
        lines.append(f"经济：{dimensions.get('economic', 0):.1f} | ")
        lines.append(f"时间：{dimensions.get('time', 0):.1f} | ")
        lines.append(f"地域：{dimensions.get('region', 0):.1f}")

        # 行动建议
        action_items = track.get('action_items', [])
        if action_items:
            lines.append("行动建议:")
            for item in action_items:
                lines.append(f"  - {item}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


if __name__ == "__main__":
    main()
