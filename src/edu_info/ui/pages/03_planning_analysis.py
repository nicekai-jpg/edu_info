"""
规划分析页面

连接后台规划引擎，生成个性化升学方案
基于赛道体系的规划分析
"""
import sys
import time
from pathlib import Path
from typing import Any

import streamlit as st

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from edu_info.models.schemas import Student
from edu_info.services.track_matching_service import TrackMatchingService
from edu_info.ui.components.common import (
    render_empty_state,
    render_header,
    render_progress_step,
    render_route_card,
    render_student_card,
    render_target_card,
)
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


def render_category_section(track_repo, track_id: int, category, index: int):
    """渲染专业类别部分"""

    mapping_info = track_repo.get_track_category_mapping(track_id, category.category_id)

    with st.expander(f"**{index}. {category.category_name}** - {category.description or ''}", expanded=(index==1)):
        # 映射信息
        if mapping_info:
            mapping_type = mapping_info.get('mapping_type', '未知')
            shared_ratio = mapping_info.get('shared_courses_ratio', 0)
            conversion_cost = mapping_info.get('conversion_cost', '未知')
            skill_gap = mapping_info.get('skill_gap', [])

            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                type_icon = "🎯" if mapping_type == '核心' else "📚" if mapping_type == '相关' else "🔗"
                st.metric("映射类型", f"{type_icon} {mapping_type}")
            with col_m2:
                st.metric("课程共享度", f"{shared_ratio*100:.0f}%")
            with col_m3:
                cost_icon = "✅" if conversion_cost == '低' else "⚠️" if conversion_cost == '中' else "🔴"
                st.metric("转换成本", f"{cost_icon} {conversion_cost}")

            if skill_gap:
                st.write("**💡 需补充技能**:")
                st.write(", ".join(skill_gap))

        # 核心课程
        if category.core_courses:
            st.write("**📖 核心课程**:")
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
                LIMIT 15
            """, [track_id, category.category_id]).fetchall()

            if results:
                # 按竞争力分组
                tier_a_plus = [r for r in results if r[1] == 'A+']
                tier_a = [r for r in results if r[1] == 'A']
                tier_b_plus = [r for r in results if r[1] == 'B+']
                tier_b = [r for r in results if r[1] in ['B', 'B-']]

                if tier_a_plus:
                    st.write("**🏆 第一梯队（A+ 院校）**:")
                    for j, (uni_name, level, score, _ranking, disc_grade, emp_rate, salary) in enumerate(tier_a_plus[:5], 1):
                        st.write(f"{j}. **{uni_name}** - {level} (综合：{score:.1f}, 学科：{disc_grade})")
                        if emp_rate and salary:
                            st.write(f"   - 就业率：{emp_rate:.1f}%, 平均薪资：{salary/10000:.1f}万/年")

                if tier_a:
                    st.write("**🥇 第二梯队（A 院校）**:")
                    for j, (uni_name, level, score, _ranking, disc_grade, emp_rate, salary) in enumerate(tier_a[:5], 1):
                        st.write(f"{j}. **{uni_name}** - {level} (综合：{score:.1f}, 学科：{disc_grade})")
                        if emp_rate and salary:
                            st.write(f"   - 就业率：{emp_rate:.1f}%, 平均薪资：{salary/10000:.1f}万/年")

                if tier_b_plus:
                    st.write("**🥈 第三梯队（B+ 院校）**:")
                    for j, (uni_name, level, score, _ranking, disc_grade, emp_rate, salary) in enumerate(tier_b_plus[:5], 1):
                        st.write(f"{j}. **{uni_name}** - {level} (综合：{score:.1f}, 学科：{disc_grade})")
                        if emp_rate and salary:
                            st.write(f"   - 就业率：{emp_rate:.1f}%, 平均薪资：{salary/10000:.1f}万/年")

                if tier_b:
                    st.write("**🥉 第四梯队（B 类院校）**:")
                    for j, (uni_name, level, score, _ranking, _disc_grade, emp_rate, salary) in enumerate(tier_b[:3], 1):
                        st.write(f"{j}. **{uni_name}** - {level} (综合：{score:.1f})")
                        if emp_rate and salary:
                            st.write(f"   - 就业率：{emp_rate:.1f}%, 平均薪资：{salary/10000:.1f}万/年")
            else:
                st.info("暂无院校竞争力数据，后续会补充")
        finally:
            conn.close()


def generate_evaluation_summary(track: dict[str, Any]) -> str:
    """生成综合评价"""
    track_name = track.get('track_name', '该赛道')
    match_score = track.get('match_score', 0)
    dimensions = track.get('dimensions', {})
    gaps = track.get('gaps', [])

    # 根据匹配度生成总体评价
    if match_score >= 85:
        overall_eval = f"🌟 **强烈推荐**：{track_name}与你高度匹配，建议作为首选目标。"
    elif match_score >= 70:
        overall_eval = f"✅ **重点考虑**：{track_name}与你较为匹配，建议重点准备。"
    elif match_score >= 55:
        overall_eval = f"📊 **可以考虑**：{track_name}与你有一定匹配度，建议作为备选。"
    else:
        overall_eval = f"⚠️ **慎重考虑**：{track_name}与你匹配度一般，建议充分了解后再决定。"

    # 优势分析
    strengths = []
    if dimensions.get('interest', 0) >= 80:
        strengths.append("兴趣契合度高")
    if dimensions.get('ability', 0) >= 80:
        strengths.append("能力基础扎实")
    if dimensions.get('economic', 0) >= 80:
        strengths.append("经济条件支持")
    if dimensions.get('time', 0) >= 80:
        strengths.append("准备时间充足")

    if strengths:
        strengths_text = "你的优势：" + "、".join(strengths)
    else:
        strengths_text = ""

    # 风险提示
    high_gaps = [g for g in gaps if g.get('priority') == 'high']
    if high_gaps:
        risk_text = f"⚠️ 需要重点关注：{high_gaps[0]['description']}。建议制定专项提升计划。"
    else:
        risk_text = "目前未发现明显短板，保持当前状态即可。"

    # 最终建议
    if match_score >= 85:
        suggestion = "💡 **建议**：立即开始针对性准备，重点关注目标院校的专业课程和招生要求。"
    elif match_score >= 70:
        suggestion = "💡 **建议**：在保持优势的同时，重点弥补存在的差距，提升竞争力。"
    else:
        suggestion = "💡 **建议**：充分了解赛道要求，评估自身情况，可以考虑作为备选方案。"

    summary = f"""
{overall_eval}

**优势分析**
{strengths_text if strengths_text else '暂无明显优势'}

**风险提示**
{risk_text}

{suggestion}
"""

    return summary


def run_planning_analysis(student_data: dict):
    """
    运行规划分析（基于赛道体系）

    Args:
        student_data: 学生数据字典

    Returns:
        规划结果字典
    """
    logger.info("开始运行赛道规划分析")

    # 1. 创建学生对象
    student = Student(
        student_code=student_data.get("student_code", "S001"),
        name=student_data.get("name", "学生"),
        grade=student_data.get("grade", "初三"),
        school=student_data.get("school", ""),
        city=student_data.get("city", "沈阳"),
        category=student_data.get("category", "物理类"),
        total_score=float(student_data.get("total_score", 680)),
        ranking=int(student_data.get("ranking", 1000)),
        chinese_score=float(student_data.get("chinese_score", 120)),
        math_score=float(student_data.get("math_score", 120)),
        english_score=float(student_data.get("english_score", 120)),
        interests=student_data.get("interests", []),
        specialities=student_data.get("specialities", []),
        family_budget=float(student_data.get("family_budget", 10)),
        preferred_locations=student_data.get("preferred_locations", []),
    )

    # 2. 赛道匹配
    logger.info("运行赛道匹配引擎...")
    track_service = TrackMatchingService()
    matches = track_service.match_all_tracks(student)

    # 3. 保存匹配结果
    for match in matches[:10]:
        track_service.save_match_result(match)

    # 4. 组织赛道结果
    logger.info("组织赛道结果...")
    top_tracks = []
    for i, match in enumerate(matches[:10]):
        # 从匹配结果中提取数据
        track_data = {
            "track_id": match.track_id,
            "track_name": f"赛道 {match.track_id}",  # 实际应从 Track 对象获取
            "match_score": match.match_score,
            "rank": i + 1,
            "dimensions": {
                "interest": match.interest_score,
                "ability": match.ability_score,
                "economic": match.economic_score,
                "time": match.time_score,
                "region": match.regional_score,
            },
            "matching_reasons": match.match_reasons or {},
            "action_items": match.action_items or [],
            "gaps": match.gaps or [],
        }
        top_tracks.append(track_data)

    # 5. 组织结果
    result = {
        "student": student.__dict__ if hasattr(student, '__dict__') else student,
        "top_tracks": top_tracks,
        "all_matches": matches,
        "is_track_mode": True,  # 标记使用赛道模式
    }

    logger.info(f"赛道规划分析完成，推荐 {len(top_tracks)} 个赛道")
    return result


def main():
    """主函数"""
    render_header("规划分析", "运行智能规划引擎，生成个性化升学方案")

    # 初始化 session state
    if "planning_result" not in st.session_state:
        st.session_state.planning_result = None
    if "is_analyzing" not in st.session_state:
        st.session_state.is_analyzing = False

    # 侧边栏
    with st.sidebar:
        st.markdown("### 操作")

        if st.button("🔄 重新分析", use_container_width=True):
            st.session_state.planning_result = None

        st.markdown("---")

        # 显示分析进度
        st.markdown("### 分析步骤")
        render_progress_step("路线穷举", completed=st.session_state.planning_result is not None)
        render_progress_step("匹配引擎", completed=st.session_state.planning_result is not None)
        render_progress_step("目标生成", completed=st.session_state.planning_result is not None)
        render_progress_step("可行性评估", completed=st.session_state.planning_result is not None)

    # 主内容区
    if st.session_state.planning_result:
        # 显示结果
        result = st.session_state.planning_result

        # 检查是否使用赛道模式
        if result.get("is_track_mode", False):
            # ========== 第一部分：赛道总览 ==========
            st.markdown("## 🎯 赛道推荐总览")

            top_tracks = result.get("top_tracks", [])

            if not top_tracks:
                st.info("暂无赛道推荐数据")
                return

            # 赛道概览卡片（只显示关键信息）
            st.markdown(f"**共推荐 {len(top_tracks)} 个赛道**，按匹配度排序：")

            # 用表格展示所有赛道概览
            overview_data = []
            for i, track in enumerate(top_tracks[:10], 1):
                track_name = track.get('track_name', '未知赛道')
                match_score = track.get('match_score', 0)
                dimensions = track.get('dimensions', {})

                # 提取关键信息
                interest = dimensions.get('interest', 0)
                ability = dimensions.get('ability', 0)

                overview_data.append({
                    "排名": f"Top {i}",
                    "赛道": track_name,
                    "匹配度": float(match_score),
                    "兴趣": float(interest),
                    "能力": float(ability),
                    "操作": "查看详情"
                })

            st.dataframe(
                overview_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "匹配度": st.column_config.ProgressColumn(
                        "匹配度",
                        min_value=0,
                        max_value=100,
                        format="%.1f",
                    ),
                    "兴趣": st.column_config.ProgressColumn(
                        "兴趣",
                        min_value=0,
                        max_value=100,
                        format="%.0f",
                    ),
                    "能力": st.column_config.ProgressColumn(
                        "能力",
                        min_value=0,
                        max_value=100,
                        format="%.0f",
                    ),
                }
            )

            st.divider()

            # ========== 第二部分：选择赛道查看详情 ==========
            st.markdown("## 📌 选择赛道查看详情")

            # 赛道选择器
            track_options = {
                f"Top {i} - {t['track_name']} (匹配度{t['match_score']:.1f})": t
                for i, t in enumerate(top_tracks[:10], 1)
            }

            selected_track_name = st.selectbox(
                "选择一个赛道，查看详细的院校与专业推荐",
                list(track_options.keys()),
                help="选择后要查看的赛道"
            )

            if selected_track_name:
                selected_track = track_options[selected_track_name]

                # ========== 第三部分：赛道详情 ==========
                st.markdown(f"### 🎯 {selected_track['track_name']}")

                # 赛道基本信息
                col_info1, col_info2 = st.columns(2)

                with col_info1:
                    st.metric("匹配度", f"{selected_track['match_score']:.1f}分")
                    st.progress(selected_track['match_score'] / 100)

                with col_info2:
                    # 获取赛道详细信息
                    track_id = selected_track.get('track_id')
                    if track_id:
                        from edu_info.data.repositories.track_repository import TrackRepository
                        track_repo = TrackRepository()
                        track_detail = track_repo.get_track_by_id(track_id)

                        if track_detail:
                            if track_detail.description:
                                st.write(f"**赛道定义**: {track_detail.description}")

                            if track_detail.domains:
                                domain_names = [d.domain_name for d in track_detail.domains]
                                st.write(f"**所属领域**: {'、'.join(domain_names)}")

                st.divider()

                # 匹配理由
                st.markdown("### ❤️ 匹配理由")

                dimensions = selected_track.get('dimensions', {})

                dim_cols = st.columns(5)
                dim_names = ["兴趣", "能力", "经济", "时间", "地域"]
                dim_keys = ["interest", "ability", "economic", "time", "region"]
                dim_icons = ["❤️", "📚", "💰", "⏰", "📍"]
                dim_weights = ["40%", "25%", "20%", "10%", "5%"]

                for col, dim_name, dim_key, dim_icon, dim_weight in zip(
                    dim_cols, dim_names, dim_keys, dim_icons, dim_weights, strict=False
                ):
                    with col:
                        score = dimensions.get(dim_key, 0)
                        st.metric(
                            f"{dim_icon} {dim_name}",
                            f"{score:.1f}",
                            f"权重{dim_weight}"
                        )
                        st.progress(score / 100)

                # 详细理由
                if selected_track.get('matching_reasons'):
                    reasons = selected_track['matching_reasons']

                    reason_cols = st.columns(2)

                    with reason_cols[0]:
                        if 'interest' in reasons:
                            r = reasons['interest']
                            st.info(f"**❤️ 兴趣匹配**\n\n{r.get('comment', '')}")

                        if 'ability' in reasons:
                            r = reasons['ability']
                            st.success(f"**📚 能力匹配**\n\n{r.get('comment', '')}")

                        if 'economic' in reasons:
                            r = reasons['economic']
                            st.warning(f"**💰 经济匹配**\n\n{r.get('comment', '')}")

                    with reason_cols[1]:
                        if 'time' in reasons:
                            r = reasons['time']
                            st.info(f"**⏰ 时间匹配**\n\n{r.get('comment', '')}")

                        if 'region' in reasons:
                            r = reasons['region']
                            st.success(f"**📍 地域匹配**\n\n{r.get('comment', '')}")

                # 差距与行动建议
                st.divider()
                st.markdown("### 📋 提升计划")

                gap_col1, gap_col2 = st.columns(2)

                with gap_col1:
                    if selected_track.get('gaps'):
                        st.markdown("**⚠️ 当前差距**:")
                        for gap in selected_track['gaps']:
                            priority = gap.get('priority', 'medium')
                            icon = "🔴" if priority == 'high' else "🟡"
                            st.write(f"{icon} {gap['description']}")

                with gap_col2:
                    if selected_track.get('action_items'):
                        st.markdown("**✅ 行动建议**:")
                        for idx, item in enumerate(selected_track['action_items'], 1):
                            st.write(f"{idx}. {item}")

                st.divider()

                # ========== 第四部分：院校与专业推荐（分 3 档） ==========
                st.markdown("### 🎓 院校与专业推荐")

                st.write("**推荐逻辑**: 根据赛道竞争力、学科实力、就业质量，为你推荐以下三档院校。")

                if track_id:
                    from edu_info.data.repositories.track_repository import TrackRepository
                    track_repo = TrackRepository()

                    # 获取赛道的专业类别
                    categories = track_repo.get_track_categories(track_id)

                    if categories:
                        # 只显示核心专业类别
                        core_categories: list[tuple[Any, dict[str, Any] | None]] = []
                        for cat in categories:
                            mapping_info = track_repo.get_track_category_mapping(track_id, cat.category_id)
                            if mapping_info and mapping_info.get('mapping_type') == '核心':
                                core_categories.append((cat, mapping_info))

                        if not core_categories and categories:
                            # 如果没有核心专业，取前 2 个相关专业
                            for cat in categories[:2]:
                                mapping_info = track_repo.get_track_category_mapping(track_id, cat.category_id)
                                core_categories.append((cat, mapping_info))

                        # 对每个专业类别，展示三档院校
                        for cat_idx, (category, mapping_info) in enumerate(core_categories[:3], 1):
                            st.markdown(f"#### 🎓 {category.category_name}")

                            if category.description:
                                st.write(f"*{category.description}*")

                            if mapping_info:
                                shared_ratio = mapping_info.get('shared_courses_ratio', 0)
                                st.write(f"**课程共享度**: {shared_ratio*100:.0f}%")

                            # 核心课程
                            if category.core_courses:
                                st.write(f"**核心课程**: {', '.join(category.core_courses[:5])}")

                            # 获取院校数据
                            conn = track_repo._get_connection()
                            try:
                                results = conn.execute("""
                                    SELECT u.university_name, tuc.competitiveness_level,
                                           tuc.overall_score, tuc.discipline_grade,
                                           tuc.employment_rate, tuc.avg_salary
                                    FROM track_university_competitiveness tuc
                                    JOIN universities u ON tuc.university_id = u.university_id
                                    WHERE tuc.track_id = ? AND tuc.category_id = ?
                                    ORDER BY tuc.overall_score DESC
                                    LIMIT 15
                                """, [track_id, category.category_id]).fetchall()

                                if results:
                                    # 按竞争力分三档
                                    tier1 = [r for r in results if r[1] in ['A+', 'A']]  # 冲刺
                                    tier2 = [r for r in results if r[1] == 'B+']  # 稳妥
                                    tier3 = [r for r in results if r[1] in ['B', 'B-']]  # 保底

                                    # 如果某一档为空，按分数重新分配
                                    if not tier1 and results:
                                        tier1 = results[:5]
                                        tier2 = results[5:10]
                                        tier3 = results[10:]
                                    elif not tier2 and len(results) > 5:
                                        tier2 = results[5:10]
                                    elif not tier3 and len(results) > 10:
                                        tier3 = results[10:]

                                    # 展示三档院校
                                    t1_cols = st.columns([1, 2, 1])
                                    t2_cols = st.columns([1, 2, 1])
                                    t3_cols = st.columns([1, 2, 1])

                                    with t1_cols[0]:
                                        st.markdown("**🎯 第一档（冲刺）**")
                                        st.caption("综合得分 85+，竞争力 A/A+")

                                    with t2_cols[0]:
                                        st.markdown("**✅ 第二档（稳妥）**")
                                        st.caption("综合得分 70-85，竞争力 B+")

                                    with t3_cols[0]:
                                        st.markdown("**📌 第三档（保底）**")
                                        st.caption("综合得分 70 以下，竞争力 B/B-")

                                    # 第一档
                                    with t1_cols[1]:
                                        if tier1:
                                            for i, (uni_name, level, score, disc_grade, _emp_rate, _salary) in enumerate(tier1[:5], 1):
                                                st.write(f"{i}. **{uni_name}** - {level}")
                                                st.caption(f"综合：{score:.1f} | 学科：{disc_grade or 'N/A'}")
                                        else:
                                            st.write("暂无数据")

                                    # 第二档
                                    with t2_cols[1]:
                                        if tier2:
                                            for i, (uni_name, level, score, disc_grade, _emp_rate, _salary) in enumerate(tier2[:5], 1):
                                                st.write(f"{i}. **{uni_name}** - {level}")
                                                st.caption(f"综合：{score:.1f} | 学科：{disc_grade or 'N/A'}")
                                        else:
                                            st.write("暂无数据")

                                    # 第三档
                                    with t3_cols[1]:
                                        if tier3:
                                            for i, (uni_name, level, score, disc_grade, _emp_rate, _salary) in enumerate(tier3[:5], 1):
                                                st.write(f"{i}. **{uni_name}** - {level}")
                                                st.caption(f"综合：{score:.1f} | 学科：{disc_grade or 'N/A'}")
                                        else:
                                            st.write("暂无数据")

                                    # 详细说明
                                    with t1_cols[2]:
                                        st.button("查看\n详情", key=f"t1_detail_{cat_idx}")

                                    with t2_cols[2]:
                                        st.button("查看\n详情", key=f"t2_detail_{cat_idx}")

                                    with t3_cols[2]:
                                        st.button("查看\n详情", key=f"t3_detail_{cat_idx}")

                                else:
                                    st.info("暂无院校竞争力数据，后续会补充")
                            finally:
                                conn.close()

                            st.divider()

                # 综合评价
                st.markdown("### 💎 综合评价")
                eval_summary = generate_evaluation_summary(selected_track)
                st.write(eval_summary)

            st.divider()
        else:
            # 原有路线模式展示（向后兼容）
            st.markdown("### 🎯 推荐路线 Top 10")

            for i, match in enumerate(result["top_routes"], 1):
                render_route_card({
                    "route_name": match.route.route_name,
                    "match_score": match.match_score,
                    "interest_score": match.interest_score,
                    "ability_score": match.ability_score,
                    "economic_score": match.economic_score,
                    "recommendations": match.recommendations,
                }, i)

        # 三档目标（仅旧版模式显示）
        if not result.get("is_track_mode", False):
            st.markdown("### 🎓 三档目标高校")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("#### 🎯 高目标（冲刺）")
                for target in result.get("high_targets", []):
                    render_target_card({
                        "university": target.university.model_dump() if hasattr(target, 'university') else target,
                        "probability": target.probability if hasattr(target, 'probability') else target.get('probability', 0),
                        "major": target.major if hasattr(target, 'major') else target.get('major', ''),
                        "min_score": target.min_score if hasattr(target, 'min_score') else target.get('min_score', 0),
                        "min_rank": target.min_rank if hasattr(target, 'min_rank') else target.get('min_rank', 0),
                        "analysis": target.analysis if hasattr(target, 'analysis') else target.get('analysis', ''),
                        "recommendations": target.recommendations if hasattr(target, 'recommendations') else target.get('recommendations', []),
                    }, "高目标")

            with col2:
                st.markdown("#### ✅ 中目标（稳妥）")
                for target in result.get("medium_targets", []):
                    render_target_card({
                        "university": target.university.model_dump() if hasattr(target, 'university') else target,
                        "probability": target.probability if hasattr(target, 'probability') else target.get('probability', 0),
                        "major": target.major if hasattr(target, 'major') else target.get('major', ''),
                        "min_score": target.min_score if hasattr(target, 'min_score') else target.get('min_score', 0),
                        "min_rank": target.min_rank if hasattr(target, 'min_rank') else target.get('min_rank', 0),
                        "analysis": target.analysis if hasattr(target, 'analysis') else target.get('analysis', ''),
                        "recommendations": target.recommendations if hasattr(target, 'recommendations') else target.get('recommendations', []),
                    }, "中目标")

            with col3:
                st.markdown("#### 📌 低目标（保底）")
                for target in result.get("low_targets", []):
                    render_target_card({
                        "university": target.university.model_dump() if hasattr(target, 'university') else target,
                        "probability": target.probability if hasattr(target, 'probability') else target.get('probability', 0),
                        "major": target.major if hasattr(target, 'major') else target.get('major', ''),
                        "min_score": target.min_score if hasattr(target, 'min_score') else target.get('min_score', 0),
                        "min_rank": target.min_rank if hasattr(target, 'min_rank') else target.get('min_rank', 0),
                        "analysis": target.analysis if hasattr(target, 'analysis') else target.get('analysis', ''),
                        "recommendations": target.recommendations if hasattr(target, 'recommendations') else target.get('recommendations', []),
                    }, "低目标")

    else:
        # 选择学生并运行分析
        st.markdown("### 选择学生")

        # 从 session state 获取学生列表
        students = st.session_state.get("students", [])

        if not students:
            render_empty_state(
                "暂无学生档案",
                '请先在"学生档案管理"页面创建学生档案',
                icon="📭"
            )

            if st.button("前往学生档案管理", type="primary"):
                st.session_state.current_page = "学生档案"
                st.rerun()
        else:
            # 学生选择下拉框
            student_options = {f"{s['name']} ({s['grade']} - {s['school']})": s for s in students}
            selected_name = st.selectbox(
                "选择要分析的学生",
                list(student_options.keys()),
                help="选择要进行规划分析的学生"
            )

            selected_student = student_options[selected_name]

            # 显示学生信息
            render_student_card(selected_student)

            # 运行分析按钮
            if st.button("🚀 开始规划分析", type="primary", use_container_width=True):
                st.session_state.is_analyzing = True
                st.rerun()

            # 分析中
            if st.session_state.is_analyzing:
                with st.spinner("正在运行规划引擎..."):
                    # 模拟进度
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # 步骤 1: 路线穷举
                    status_text.text("步骤 1/4: 路线穷举中...")
                    progress_bar.progress(25)
                    time.sleep(0.5)

                    # 步骤 2: 匹配引擎
                    status_text.text("步骤 2/4: 匹配引擎计算中...")
                    progress_bar.progress(50)
                    time.sleep(0.5)

                    # 步骤 3: 目标生成
                    status_text.text("步骤 3/4: 生成目标高校...")
                    progress_bar.progress(75)
                    time.sleep(0.5)

                    # 步骤 4: 可行性评估
                    status_text.text("步骤 4/4: 可行性评估中...")
                    progress_bar.progress(100)
                    time.sleep(0.5)

                    # 运行分析
                    result = run_planning_analysis(selected_student)

                    st.session_state.planning_result = result
                    st.session_state.is_analyzing = False
                    status_text.text("✅ 分析完成！")

                    st.rerun()


if __name__ == "__main__":
    main()
