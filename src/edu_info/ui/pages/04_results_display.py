"""
结果展示页面 - 重构版

展示完整的升学规划结果，包括：
1. 学生画像总览
2. 赛道匹配总览（Top 3-5）
3. 赛道详情（三档目标、匹配理由、行动建议）
4. 可视化图表
"""
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from edu_info.ui.components.common import (
    render_empty_state,
    render_header,
)


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
        st.metric("💰 家庭预算", f"{budget:.0f}元/年")

    with col5:
        locations = student.get('preferred_locations', [])
        loc_text = ', '.join(locations[:2]) if locations else "未填写"
        st.metric("📍 地域偏好", loc_text)


def render_track_summary_card(track: dict[str, Any], rank: int):
    """渲染赛道摘要卡片"""
    match_score = track.get('match_score', 0)
    route_name = track.get('route_name', '未知赛道')
    route_type = track.get('route_type', '')

    # 创建卡片
    with st.container():
        st.markdown(f"""
        <div style="
            padding: 20px;
            margin: 10px 0;
            border-radius: 10px;
            border: 2px solid {'#28a745' if rank <= 3 else '#dee2e6'};
            background-color: {'#f8fff9' if rank <= 3 else '#ffffff'};
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="margin: 0; color: {'#28a745' if rank <= 3 else '#333'};">
                        {rank}. {route_name}
                    </h3>
                    <p style="margin: 5px 0; color: #666;">{route_type}</p>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 24px; font-weight: bold; color: {'#28a745' if rank <= 3 else '#333'};">
                        {match_score:.1f}分
                    </div>
                    <div style="font-size: 12px; color: #666;">匹配度</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_match_reasons(reasons: dict[str, Any]):
    """渲染匹配理由"""
    st.markdown("#### 🔍 匹配理由深度解析")

    # 五维分析
    dimensions = [
        ("兴趣匹配", reasons.get("interest", {}), "❤️"),
        ("能力匹配", reasons.get("ability", {}), "📚"),
        ("经济匹配", reasons.get("economic", {}), "💰"),
        ("时间匹配", reasons.get("time", {}), "⏰"),
        ("地域匹配", reasons.get("region", {}), "📍"),
    ]

    for dim_name, dim_data, icon in dimensions:
        if not dim_data:
            continue

        score = dim_data.get("score", 0)
        weight = dim_data.get("weight", 0)
        evaluation = dim_data.get("evaluation", "")
        suggestion = dim_data.get("suggestion", "")

        # 确定颜色
        if score >= 80:
            level = "优秀"
        elif score >= 60:
            level = "良好"
        else:
            level = "待提升"

        with st.expander(f"{icon} {dim_name}（{score:.0f}分，权重{weight*100:.0f}%） - {level}"):
            st.markdown(f"**评价：** {evaluation}")
            st.markdown(f"**建议：** {suggestion}")

    # 综合评价
    st.markdown("#### 📊 综合评价")
    st.info(reasons.get("summary", ""))


def render_action_items(action_items: list[str]):
    """渲染行动建议"""
    st.markdown("#### ✅ 行动建议")

    for i, item in enumerate(action_items, 1):
        st.markdown(f"{i}. {item}")


def render_university_targets(targets: dict[str, list[dict[str, Any]]]):
    """渲染三档目标高校"""
    st.markdown("#### 🎓 三档目标高校")

    col1, col2, col3 = st.columns(3)

    target_types = [
        ("high", "🎯 高目标（冲刺）", "#dc3545"),
        ("medium", "✅ 中目标（稳妥）", "#28a745"),
        ("low", "📌 低目标（保底）", "#17a2b8"),
    ]

    for target_key, target_name, color in target_types:
        universities = targets.get(target_key, [])

        with col1 if target_key == "high" else (col2 if target_key == "medium" else col3):
            st.markdown(f"##### {target_name}")

            if universities:
                for uni in universities[:3]:  # 最多显示 3 所
                    uni_name = uni.get('university_name', '未知高校')
                    major = uni.get('major', '未指定专业')
                    score = uni.get('score', 0)
                    ranking = uni.get('ranking', 0)

                    st.markdown(f"""
                    <div style="
                        padding: 10px;
                        margin: 5px 0;
                        border-radius: 5px;
                        border-left: 3px solid {color};
                        background-color: #f8f9fa;
                    ">
                        <div style="font-weight: bold;">{uni_name}</div>
                        <div style="font-size: 12px; color: #666;">{major}</div>
                        <div style="font-size: 12px; color: #999;">{score:.0f}分 / {ranking}名</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("暂无数据")


def main():
    """主函数"""
    render_header("结果展示", "查看完整的升学规划方案")

    # 检查是否有规划结果
    if "planning_result" not in st.session_state or not st.session_state.planning_result:
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

    # 1. 学生画像总览
    render_student_profile(result.get("student", {}))

    st.markdown("---")

    # 2. 赛道匹配总览
    st.markdown("### 🎯 赛道匹配总览")

    top_tracks = result.get("top_tracks", [])

    if top_tracks:
        # 显示 Top 3-5 条赛道
        display_count = min(5, len(top_tracks))

        for i in range(display_count):
            track = top_tracks[i]
            render_track_summary_card(track, i + 1)

        # 赛道选择器
        st.markdown("##### 选择赛道查看详情")
        track_options = {
            f"{i+1}. {track.get('route_name', '未知赛道')} ({track.get('match_score', 0):.1f}分)": track
            for i, track in enumerate(top_tracks)
        }
        selected_track_name = st.selectbox(
            "选择赛道",
            list(track_options.keys()),
            index=0
        )
        selected_track = track_options[selected_track_name]

        st.markdown("---")

        # 3. 赛道详情
        st.markdown(f"### 📋 {selected_track_name} 详情")

        # 三档目标高校
        render_university_targets(selected_track.get("universities", {}))

        st.markdown("---")

        # 匹配理由
        if "matching_reasons" in selected_track:
            render_match_reasons(selected_track["matching_reasons"])

        # 行动建议
        if "action_items" in selected_track:
            render_action_items(selected_track["action_items"])

    else:
        st.info("暂无推荐赛道")

    st.markdown("---")

    # 4. 导出功能
    st.markdown("### 📤 导出与分享")

    # 准备导出数据
    def prepare_export_data(result):
        """准备导出数据"""
        export_data = []
        result.get("student", {})
        top_tracks = result.get("top_tracks", [])

        for i, track in enumerate(top_tracks[:5], 1):
            row = {
                "排名": i,
                "赛道名称": track.get("track_name", "未知"),
                "匹配度": track.get("match_score", 0),
                "兴趣匹配": track.get("dimensions", {}).get("interest", 0),
                "能力匹配": track.get("dimensions", {}).get("ability", 0),
                "经济匹配": track.get("dimensions", {}).get("economic", 0),
                "时间匹配": track.get("dimensions", {}).get("time", 0),
                "地域匹配": track.get("dimensions", {}).get("region", 0),
            }

            # 添加行动建议
            action_items = track.get("action_items", [])
            if action_items:
                row["行动建议"] = "; ".join(action_items[:3])

            export_data.append(row)

        return pd.DataFrame(export_data)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 导出 PDF 报告", use_container_width=True):
            st.info("PDF 导出功能开发中...")

    with col2:
        # 生成 Excel 数据
        export_df = prepare_export_data(result)

        # 创建 Excel 文件 - 使用内存中的 bytes
        import io

        from openpyxl import Workbook
        from openpyxl.utils.dataframe import dataframe_to_rows

        wb = Workbook()

        # 写入规划结果
        ws1 = wb.active
        ws1.title = "规划结果"
        for r in dataframe_to_rows(export_df, index=False, header=True):
            ws1.append(r)

        # 写入学生信息
        ws2 = wb.create_sheet("学生信息")
        student_info = [
            ["学生姓名", result.get("student", {}).get("name", "未知")],
            ["总分", result.get("student", {}).get("total_score", 0)],
            ["排名", result.get("student", {}).get("ranking", 0)],
            ["年级", result.get("student", {}).get("grade", "未知")],
            ["生成时间", datetime.now().strftime("%Y-%m-%d %H:%M")],
        ]
        for row in student_info:
            ws2.append(row)

        # 保存到 bytes
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        excel_bytes = buffer.getvalue()

        st.download_button(
            label="📊 导出 Excel",
            data=excel_bytes,
            file_name=f"升学规划结果_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col3:
        if st.button("📱 分享链接", use_container_width=True):
            st.info("分享功能开发中...")
