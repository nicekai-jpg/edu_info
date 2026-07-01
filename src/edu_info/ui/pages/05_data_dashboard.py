"""
数据看板页面

展示数据库状态和数据完整性检查
"""
import sys
from pathlib import Path

import duckdb
import streamlit as st

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_db_path() -> str:
    """获取数据库路径"""
    return str(Path(__file__).parent.parent.parent.parent / "data" / "duckdb" / "edu_planning.db")


def check_data_status() -> dict:
    """检查数据就绪状态"""
    db_path = get_db_path()

    try:
        conn = duckdb.connect(db_path)

        # 查询各类数据统计
        result = conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM universities) as uni_count,
                (SELECT COUNT(*) FROM admission_scores) as score_count,
                (SELECT COUNT(*) FROM students) as student_count,
                (SELECT COUNT(*) FROM planning_routes) as route_count
        """).fetchone()

        conn.close()

        return {
            "universities": result[0] if result else 0,
            "scores": result[1] if result else 0,
            "students": result[2] if result else 0,
            "routes": result[3] if result else 0,
            "is_ready": (result[0] > 0 and result[1] > 0) if result else False
        }
    except Exception as e:
        logger.error(f"检查数据状态失败：{e}")
        return {
            "universities": 0,
            "scores": 0,
            "students": 0,
            "routes": 0,
            "is_ready": False,
            "error": str(e)
        }


def main():
    """数据看板主函数"""
    st.markdown("# 📋 数据看板")
    st.markdown("_查看数据库状态和数据完整性_")
    st.markdown("---")

    status = check_data_status()

    # 状态卡片
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if status["universities"] > 0:
            st.success(f"✅ 高校：{status['universities']}所")
        else:
            st.error("❌ 高校：0 所")

    with col2:
        if status["scores"] > 0:
            st.success(f"✅ 分数线：{status['scores']}条")
        else:
            st.error("❌ 分数线：0 条")

    with col3:
        st.info(f"👤 学生：{status['students']}人")

    with col4:
        st.info(f"🗺️ 路线：{status['routes']}条")

    # 数据就绪提示
    st.markdown("---")
    if status["is_ready"]:
        st.success("✅ 数据已就绪，可以开始规划分析！")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**下一步操作：**")
            st.markdown("- 前往【规划服务】→【学生档案】创建学生信息")
            st.markdown("- 或直接使用【规划分析】功能")
        with col2:
            if st.button("🎯 开始规划", type="primary", use_container_width=True):
                st.session_state.current_page = "规划分析"
                st.rerun()
    else:
        st.error("❌ 数据未就绪，请先在【数据管理】→【数据导入】页面导入高校数据和分数线数据")

        if st.button("📊 前往数据导入", type="primary"):
            st.session_state.current_page = "数据导入"
            st.rerun()

    # 数据统计详情
    if status["universities"] > 0:
        st.markdown("---")
        st.markdown("### 📊 高校统计")

        try:
            conn = duckdb.connect(get_db_path())

            # 高校类型统计
            stats_df = conn.execute("""
                SELECT
                    SUM(CASE WHEN is_985 THEN 1 ELSE 0 END) as "985 高校",
                    SUM(CASE WHEN is_211 THEN 1 ELSE 0 END) as "211 高校",
                    SUM(CASE WHEN is_double_first_class THEN 1 ELSE 0 END) as "双一流",
                    COUNT(*) as "总计"
                FROM universities
            """).fetchall()

            st.dataframe(
                stats_df,
                use_container_width=True,
                hide_index=True
            )

            # 高校类别分布
            st.markdown("#### 高校类别分布")
            type_df = conn.execute("""
                SELECT
                    type as "类别",
                    COUNT(*) as "数量"
                FROM universities
                WHERE type IS NOT NULL
                GROUP BY type
                ORDER BY COUNT(*) DESC
            """).fetchall()

            if type_df:
                st.dataframe(
                    type_df,
                    use_container_width=True,
                    hide_index=True
                )

            # 分数线统计
            st.markdown("#### 分数线统计")
            score_stats = conn.execute("""
                SELECT
                    MIN(year) as "最早年份",
                    MAX(year) as "最晚年份",
                    AVG(score) as "平均分",
                    COUNT(DISTINCT university_id) as "覆盖高校"
                FROM admission_scores
            """).fetchall()

            if score_stats:
                st.dataframe(
                    score_stats,
                    use_container_width=True,
                    hide_index=True
                )

            conn.close()

        except Exception as e:
            st.warning(f"无法获取详细统计：{e}")
