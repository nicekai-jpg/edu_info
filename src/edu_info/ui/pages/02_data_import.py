"""
数据导入页面

支持 Excel/CSV 数据导入
"""
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from edu_info.database import get_connection
from edu_info.services.data_importer import (
    import_scores_from_excel,
    import_students_from_json,
    import_universities_from_excel,
    import_universities_from_json,
)
from edu_info.ui.components.common import render_header
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """主函数"""
    render_header("数据导入", "导入高校分数线和政策文件数据")

    # 初始化 session state
    if "import_stats" not in st.session_state:
        st.session_state.import_stats = None

    # 数据库路径
    DB_PATH = str(Path(__file__).parent.parent.parent.parent / "data" / "duckdb" / "edu_planning.db")

    # 侧边栏
    with st.sidebar:
        st.markdown("### 导入说明")

        st.markdown("""
        **导入步骤**:

        1. 选择数据类型
        2. 上传文件
        3. 预览数据
        4. 确认导入

        **注意事项**:

        - 文件格式必须符合要求
        - 必填字段不能为空
        - 分数范围 0-750
        - 位次必须为正整数
        """)

        if st.session_state.import_stats:
            st.markdown("### 导入统计")
            stats = st.session_state.import_stats
            if "universities" in stats:
                st.success(f"✅ 高校：{stats['universities']}所")
            if "students" in stats:
                st.success(f"✅ 学生：{stats['students']}个")
            if "scores" in stats:
                st.success(f"✅ 分数线：{stats['scores']}条")

    # 主内容区 - 标签页
    tab1, tab2, tab3 = st.tabs(["🏫 高校数据", "📝 学生档案", "📊 分数线数据"])

    with tab1:
        st.markdown("### 🏫 高校数据导入")

        st.markdown("""
        **支持格式**:
        - JSON 文件（推荐）
        - Excel 文件

        **字段要求**:
        - `id`: 高校 ID（整数）
        - `name`: 高校名称
        - `code`: 高校代码
        - `location`: 所在地
        - `is_985`, `is_211`, `is_double_first_class`: 布尔值
        """)

        # 文件上传
        uploaded_file = st.file_uploader(
            "选择 JSON 或 Excel 文件",
            type=["json", "xlsx", "csv"],
            help="上传高校数据文件",
            key="university_file"
        )

        if uploaded_file:
            # 预览数据
            st.markdown("#### 数据预览")

            try:
                if uploaded_file.name.endswith('.json'):
                    data = json.load(uploaded_file)
                    if isinstance(data, list):
                        df = pd.DataFrame(data)
                    else:
                        df = pd.DataFrame([data])
                else:
                    df = pd.read_excel(uploaded_file)

                st.dataframe(df.head(10), use_container_width=True)
                st.info(f"共 {len(df)} 条记录")

                # 导入按钮
                if st.button("📥 导入高校数据", type="primary", use_container_width=True):
                    with st.spinner("正在导入数据..."):
                        # 保存临时文件
                        temp_path = Path("data/imports") / f"temp_{uploaded_file.name}"
                        temp_path.parent.mkdir(parents=True, exist_ok=True)

                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getvalue())

                        # 导入数据库
                        conn = get_connection(DB_PATH)

                        if uploaded_file.name.endswith('.json'):
                            count = import_universities_from_json(conn, str(temp_path))
                        else:
                            # 使用 Excel 导入函数
                            count = import_universities_from_excel(conn, str(temp_path))

                        conn.close()

                        # 更新统计
                        if st.session_state.import_stats is None:
                            st.session_state.import_stats = {}
                        st.session_state.import_stats["universities"] = count

                        st.success(f"✅ 成功导入 {count} 所高校！")
                        st.rerun()

            except Exception as e:
                st.error(f"❌ 文件解析失败：{e}")

    with tab2:
        st.markdown("### 📝 学生档案导入")

        st.markdown("""
        **支持格式**:
        - JSON 文件

        **字段要求**:
        - `student_code`: 学号（必填）
        - `name`: 姓名（必填）
        - `grade`: 年级
        - `total_score`: 总分
        - `interests`: 兴趣列表
        - `specialities`: 特长列表
        """)

        # 文件上传
        uploaded_file = st.file_uploader(
            "选择 JSON 文件",
            type=["json"],
            help="上传学生档案文件",
            key="student_file"
        )

        if uploaded_file:
            # 预览数据
            st.markdown("#### 数据预览")

            try:
                data = json.load(uploaded_file)
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame([data])

                st.dataframe(df.head(10), use_container_width=True)
                st.info(f"共 {len(df)} 条记录")

                # 导入按钮
                if st.button("📥 导入学生档案", type="primary", use_container_width=True):
                    with st.spinner("正在导入数据..."):
                        # 保存临时文件
                        temp_path = Path("data/imports") / f"temp_{uploaded_file.name}"
                        temp_path.parent.mkdir(parents=True, exist_ok=True)

                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getvalue())

                        # 导入数据库
                        conn = get_connection(DB_PATH)
                        count = import_students_from_json(conn, str(temp_path))
                        conn.close()

                        # 更新统计
                        if st.session_state.import_stats is None:
                            st.session_state.import_stats = {}
                        st.session_state.import_stats["students"] = count

                        st.success(f"✅ 成功导入 {count} 个学生档案！")
                        st.rerun()

            except Exception as e:
                st.error(f"❌ 文件解析失败：{e}")

    with tab3:
        st.markdown("### 📊 分数线数据导入")

        st.markdown("""
        **支持格式**:
        - Excel 文件

        **字段要求**:
        - `university_id`: 高校 ID
        - `major_id`: 专业 ID
        - `year`: 年份
        - `province`: 省份
        - `category`: 类别（物理类/历史类）
        - `min_score`: 最低分
        - `min_rank`: 最低位次
        """)

        # 文件上传
        uploaded_file = st.file_uploader(
            "选择 Excel 文件",
            type=["xlsx", "csv"],
            help="上传分数线数据文件",
            key="score_file"
        )

        if uploaded_file:
            # 预览数据
            st.markdown("#### 数据预览")

            try:
                df = pd.read_excel(uploaded_file)
                st.dataframe(df.head(10), use_container_width=True)
                st.info(f"共 {len(df)} 条记录")

                # 导入按钮
                if st.button("📥 导入分数线数据", type="primary", use_container_width=True):
                    with st.spinner("正在导入数据..."):
                        # 保存临时文件
                        temp_path = Path("data/imports") / f"temp_{uploaded_file.name}"
                        temp_path.parent.mkdir(parents=True, exist_ok=True)

                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getvalue())

                        # 导入数据库
                        conn = get_connection(DB_PATH)
                        count = import_scores_from_excel(conn, str(temp_path))
                        conn.close()

                        # 更新统计
                        if st.session_state.import_stats is None:
                            st.session_state.import_stats = {}
                        st.session_state.import_stats["scores"] = count

                        st.success(f"✅ 成功导入 {count} 条分数线记录！")
                        st.rerun()

            except Exception as e:
                st.error(f"❌ 文件解析失败：{e}")

        # 下载模板
        st.markdown("---")
        st.markdown("#### 📋 下载模板")

        st.download_button(
            label="📥 下载分数线 Excel 模板",
            data="高校 ID，专业 ID，年份，省份，类别，最低分，最低位次\n1,1,2024，辽宁，物理类，680,100",
            file_name="分数线模板.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
