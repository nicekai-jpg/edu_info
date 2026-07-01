"""
升学规划咨询系统 - Streamlit 主应用

基于国家战略发展方向，整合教育政策与高校录取数据，
为初中/高中学生提供个性化升学规划方案的本地运行工具。
"""
import sys
from pathlib import Path

import duckdb
import streamlit as st

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from edu_info import __version__
from edu_info.ui.components.common import render_header
from edu_info.utils.logger import setup_logger

# 初始化日志
logger = setup_logger(__name__)


# 页面配置
st.set_page_config(
    page_title="升学规划咨询系统",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/edu-info',
        'Report a bug': 'https://github.com/your-repo/edu-info/issues',
        'About': f"# 升学规划咨询系统 v{__version__}"
    }
)


def get_db_path() -> str:
    """获取数据库路径"""
    return str(Path(__file__).parent.parent.parent / "data" / "duckdb" / "edu_planning.db")


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
                (SELECT COUNT(*) FROM students) as student_count
        """).fetchone()

        conn.close()

        uni_count = result[0] if result else 0
        score_count = result[1] if result else 0
        student_count = result[2] if result else 0

        return {
            "universities": uni_count,
            "scores": score_count,
            "students": student_count,
            "is_ready": uni_count > 0 and score_count > 0
        }
    except Exception as e:
        logger.error(f"检查数据状态失败：{e}")
        return {
            "universities": 0,
            "scores": 0,
            "students": 0,
            "is_ready": False,
            "error": str(e)
        }


def render_sidebar():
    """渲染侧边栏导航"""
    st.sidebar.title("🎓 升学规划")
    st.sidebar.markdown("---")

    # 首页
    if st.sidebar.button("🏠 首页", use_container_width=True):
        st.session_state.current_page = "首页"
        st.rerun()

    st.sidebar.markdown("---")

    # 数据管理区域（内部使用）
    st.sidebar.markdown("### 📊 数据管理")
    st.sidebar.caption("管理员/老师使用")

    if st.sidebar.button("📊 数据导入", use_container_width=True):
        st.session_state.current_page = "数据导入"
        st.rerun()

    if st.sidebar.button("📋 数据看板", use_container_width=True):
        st.session_state.current_page = "数据看板"
        st.rerun()

    st.sidebar.markdown("---")

    # 规划服务区域（客户使用）
    st.sidebar.markdown("### 🎯 规划服务")
    st.sidebar.caption("学生/家长使用")

    if st.sidebar.button("📝 学生档案", use_container_width=True):
        st.session_state.current_page = "学生档案"
        st.rerun()

    if st.sidebar.button("🎯 规划分析", use_container_width=True):
        st.session_state.current_page = "规划分析"
        st.rerun()

    if st.sidebar.button("📈 结果展示", use_container_width=True):
        st.session_state.current_page = "结果展示"
        st.rerun()

    st.sidebar.markdown("---")

    # 数据状态提示
    status = check_data_status()
    if status["is_ready"]:
        st.sidebar.success("✅ 数据已就绪")
    else:
        st.sidebar.warning("⚠️ 数据未就绪")


def render_home():
    """渲染首页"""
    render_header("升学规划咨询系统", "基于国家战略的个性化升学规划工具")

    # 业务流程图
    st.markdown("## 📋 业务流程")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        ### 步骤 1：数据准备
        **（内部管理员操作）**

        - 📊 导入高校数据
        - 📊 导入分数线数据
        - ✅ 验证数据完整性
        """)

    with col2:
        st.markdown("""
        ### 步骤 2：学生档案
        **（学生/家长操作）**

        - 📝 创建学生档案
        - 📝 填写成绩信息
        - 📝 记录兴趣特长
        """)

    with col3:
        st.markdown("""
        ### 步骤 3：规划分析
        **（核心服务）**

        - 🎯 智能规划分析
        - 🎯 生成三档目标
        - 🎯 可行性评估
        """)

    st.markdown("---")

    # 系统状态检查
    st.markdown("## 🔍 系统状态")

    status = check_data_status()

    col1, col2, col3 = st.columns(3)

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

    st.markdown("---")

    if status["is_ready"]:
        st.success("✅ 数据已就绪，可以开始规划分析！")

        if st.button("🎯 开始规划分析", type="primary"):
            st.session_state.current_page = "规划分析"
            st.rerun()
    else:
        st.error("❌ 数据未就绪，请先在【数据管理】→【数据导入】页面导入高校数据和分数线数据")

        if st.button("📊 前往数据导入", type="primary"):
            st.session_state.current_page = "数据导入"
            st.rerun()

    st.markdown("---")

    # 核心功能
    st.markdown("## 📝 核心功能")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        ### 📊 数据管理
        - 高校数据导入
        - 分数线数据导入
        - 数据状态监控
        """)

    with col2:
        st.markdown("""
        ### 🎯 升学途径
        - 普通高考
        - 强基计划
        - 科技特长生
        - 艺术特长生
        - 体育特长生
        """)

    with col3:
        st.markdown("""
        ### 📈 数据覆盖
        - 985 高校：39 所
        - 211 高校：116 所
        - 双一流：147 所
        - 近 5 年分数线
        """)


def render_data_dashboard():
    """渲染数据看板页面"""
    st.markdown("# 📋 数据看板")
    st.markdown("_查看数据库状态和数据完整性_")
    st.markdown("---")

    status = check_data_status()

    # 状态卡片
    col1, col2, col3 = st.columns(3)

    with col1:
        if status["universities"] > 0:
            st.success(f"✅ 高校数据：{status['universities']}所")
        else:
            st.error("❌ 高校数据：0 所（请先导入）")

    with col2:
        if status["scores"] > 0:
            st.success(f"✅ 分数线：{status['scores']}条")
        else:
            st.error("❌ 分数线：0 条（请先导入）")

    with col3:
        st.info(f"👤 学生：{status['students']}人")

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
            df = conn.execute("""
                SELECT
                    SUM(CASE WHEN is_985 THEN 1 ELSE 0 END) as "985 高校",
                    SUM(CASE WHEN is_211 THEN 1 ELSE 0 END) as "211 高校",
                    SUM(CASE WHEN is_double_first_class THEN 1 ELSE 0 END) as "双一流",
                    COUNT(*) as "总计"
                FROM universities
            """).fetchall()

            conn.close()

            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.warning(f"无法获取详细统计：{e}")


def main():
    """主函数"""
    # 初始化 session state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "首页"

    # 渲染侧边栏
    render_sidebar()

    # 根据选择渲染页面
    page = st.session_state.current_page

    if page == "首页":
        render_home()

    elif page == "数据导入":
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "data_import",
            str(Path(__file__).parent / "ui" / "pages" / "02_data_import.py")
        )
        data_import_page = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_import_page)
        data_import_page.main()

    elif page == "数据看板":
        render_data_dashboard()

    elif page == "学生档案":
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "student_profile",
            str(Path(__file__).parent / "ui" / "pages" / "01_student_profile.py")
        )
        student_page = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(student_page)
        student_page.main()

    elif page == "规划分析":
        # 数据检查
        status = check_data_status()
        if not status["is_ready"]:
            st.error("❌ 数据未就绪！请先在【数据管理】→【数据导入】页面导入高校数据和分数线数据")
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info("💡 提示：数据导入是内部功能，由管理员或老师操作")
            with col2:
                if st.button("📊 前往数据导入", type="primary"):
                    st.session_state.current_page = "数据导入"
                    st.rerun()
            return

        # 导入规划分析页面
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "analysis",
            str(Path(__file__).parent / "ui" / "pages" / "03_planning_analysis.py")
        )
        analysis_page = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(analysis_page)
        analysis_page.main()

    elif page == "结果展示":
        # 数据检查
        status = check_data_status()
        if not status["is_ready"]:
            st.error("❌ 数据未就绪！请先在【数据管理】→【数据导入】页面导入高校数据和分数线数据")

            if st.button("📊 前往数据导入", type="primary"):
                st.session_state.current_page = "数据导入"
                st.rerun()
            return

        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "results",
            str(Path(__file__).parent / "ui" / "pages" / "04_results_display_track.py")
        )
        results_page = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(results_page)
        results_page.main()
        results_page = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(results_page)
        results_page.main()


def cli():
    """CLI 入口点 - 启动 Streamlit 应用"""
    import subprocess
    import sys

    # 获取 main.py 的绝对路径
    main_path = Path(__file__).resolve()

    # 构建 streamlit run 命令
    cmd = [sys.executable, "-m", "streamlit", "run", str(main_path)]

    print("启动升学规划咨询系统...")
    print(f"命令: {' '.join(cmd)}")

    # 执行命令
    subprocess.run(cmd)


if __name__ == "__main__":
    main()
