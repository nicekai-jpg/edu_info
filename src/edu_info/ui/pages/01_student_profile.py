"""
学生档案管理页面

功能：
- 创建学生档案
- 编辑学生信息
- 查看档案列表
- 搜索学生
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb
import streamlit as st

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from edu_info.ui.components.common import (
    render_empty_state,
    render_header,
    render_student_card,
)
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_db_path() -> str:
    """获取数据库路径"""
    # 项目根目录是 /Users/limingkai/nas/project/edu_info
    # 当前文件路径：src/edu_info/ui/pages/01_学生档案管理.py
    # 需要向上 3 级回到项目根目录
    project_root = Path(__file__).parent.parent.parent.parent.parent
    return str(project_root / "data" / "duckdb" / "edu_planning.db")


def load_students_from_db() -> list[dict[str, Any]]:
    """从数据库加载学生列表"""
    db_path = get_db_path()

    try:
        conn = duckdb.connect(db_path)

        # 查询学生数据
        students = conn.execute("""
            SELECT
                id, name, student_code, grade, school, city, category,
                total_score, ranking,
                chinese_score, math_score, english_score,
                interests, specialities, awards,
                family_budget, preferred_locations,
                created_at, updated_at
            FROM students
            ORDER BY created_at DESC
        """).fetchall()

        conn.close()

        # 转换为字典列表
        result = []
        for row in students:
            student = {
                "id": row[0],
                "name": row[1],
                "student_code": row[2],
                "grade": row[3],
                "school": row[4],
                "city": row[5],
                "category": row[6],
                "total_score": float(row[7]) if row[7] else 0,
                "ranking": row[8],
                "chinese_score": float(row[9]) if row[9] else 0,
                "math_score": float(row[10]) if row[10] else 0,
                "english_score": float(row[11]) if row[11] else 0,
                "interests": json.loads(row[12]) if row[12] else [],
                "specialities": (
                    json.loads(row[13])
                    if isinstance(row[13], str) and row[13].strip().startswith("[")
                    else ([s.strip() for s in str(row[13]).split(",") if s.strip()] if row[13] else [])
                ),
                "awards": json.loads(row[14]) if row[14] else [],
                "family_budget": float(row[15]) if row[15] else 0,
                "preferred_locations": json.loads(row[16]) if row[16] else [],
                "created_at": str(row[17]) if row[17] else "",
                "updated_at": str(row[18]) if row[18] else "",
            }
            # 生成 specialities_str 方便页面上的文本框渲染
            specs = student["specialities"]
            student["specialities_str"] = ", ".join(specs) if isinstance(specs, list) else str(specs)
            result.append(student)

        return result
    except Exception as e:
        logger.error(f"从数据库加载学生失败：{e}")
        return []


def save_student_to_db(student_data: dict[str, Any]) -> bool:
    """保存学生到数据库"""
    db_path = get_db_path()

    # 规范化 specialities，若是逗号分隔字符串，转为列表保存
    specs = student_data.get("specialities", [])
    if isinstance(specs, str):
        specs = [s.strip() for s in specs.split(",") if s.strip()]

    try:
        conn = duckdb.connect(db_path)

        if "id" in student_data and student_data["id"]:
            # 更新现有学生
            conn.execute("""
                UPDATE students SET
                    name = ?, student_code = ?, grade = ?, school = ?, city = ?,
                    category = ?, total_score = ?, ranking = ?,
                    chinese_score = ?, math_score = ?, english_score = ?,
                    interests = ?, specialities = ?, awards = ?,
                    family_budget = ?, preferred_locations = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                student_data.get("name"),
                student_data.get("student_code"),
                student_data.get("grade"),
                student_data.get("school"),
                student_data.get("city"),
                student_data.get("category"),
                student_data.get("total_score"),
                student_data.get("ranking"),
                student_data.get("chinese_score"),
                student_data.get("math_score"),
                student_data.get("english_score"),
                json.dumps(student_data.get("interests", []), ensure_ascii=False),
                json.dumps(specs, ensure_ascii=False),
                json.dumps(student_data.get("awards", []), ensure_ascii=False),
                student_data.get("family_budget"),
                json.dumps(student_data.get("preferred_locations", []), ensure_ascii=False),
                datetime.now(),
                student_data.get("id"),
            ))
            logger.info(f"更新学生 {student_data.get('name')} 成功")
        else:
            res = conn.execute('SELECT COALESCE(MAX(id), 0) + 1 FROM students').fetchone()
            max_id = res[0] if res else 1
            student_code = student_data.get("student_code", f"S{datetime.now().year}{max_id:04d}")
            conn.execute("""
                INSERT INTO students (
                    name, student_code, grade, school, city, category,
                    total_score, ranking,
                    chinese_score, math_score, english_score,
                    interests, specialities, awards,
                    family_budget, preferred_locations,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                student_data.get("name"),
                student_code,
                student_data.get("grade"),
                student_data.get("school"),
                student_data.get("city"),
                student_data.get("category"),
                student_data.get("total_score"),
                student_data.get("ranking"),
                student_data.get("chinese_score"),
                student_data.get("math_score"),
                student_data.get("english_score"),
                json.dumps(student_data.get("interests", []), ensure_ascii=False),
                json.dumps(specs, ensure_ascii=False),
                json.dumps(student_data.get("awards", []), ensure_ascii=False),
                student_data.get("family_budget"),
                json.dumps(student_data.get("preferred_locations", []), ensure_ascii=False),
                datetime.now(),
                datetime.now(),
            ))
            logger.info(f"创建学生 {student_data.get('name')} 成功")

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"保存学生失败：{e}")
        return False


def delete_student_from_db(student_id: int) -> bool:
    """从数据库删除学生"""
    db_path = get_db_path()

    try:
        conn = duckdb.connect(db_path)
        conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
        conn.close()
        logger.info(f"删除学生 ID={student_id} 成功")
        return True
    except Exception as e:
        logger.error(f"删除学生失败：{e}")
        return False


def render_student_form(student_data: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    渲染学生信息表单

    Args:
        student_data: 现有学生数据（编辑模式）

    Returns:
        表单数据字典
    """
    form_data = {}

    with st.form("student_form"):
        st.markdown("### 基本信息")

        col1, col2 = st.columns(2)

        with col1:
            form_data["name"] = st.text_input(
                "姓名 *",
                value=student_data.get("name", "") if student_data else "",
                help="学生姓名"
            )

            form_data["grade"] = st.selectbox(
                "年级 *",
                ["初一", "初二", "初三", "高一", "高二", "高三"],
                index=["初一", "初二", "初三", "高一", "高二", "高三"].index(
                    student_data.get("grade", "初三")
                ) if student_data and student_data.get("grade") else 2,
                help="当前年级"
            )

            form_data["city"] = st.text_input(
                "城市 *",
                value=student_data.get("city", "沈阳") if student_data else "沈阳",
                help="所在城市"
            )

        with col2:
            form_data["school"] = st.text_input(
                "学校",
                value=student_data.get("school", "") if student_data else "",
                help="学校名称"
            )

            form_data["category"] = st.selectbox(
                "选科",
                ["未分科", "物理类", "历史类"],
                index=["未分科", "物理类", "历史类"].index(
                    student_data.get("category", "未分科")
                ) if student_data and student_data.get("category") else 0,
                help="选科类别"
            )

        st.markdown("### 成绩信息")

        col1, col2, col3 = st.columns(3)

        with col1:
            form_data["chinese_score"] = st.number_input(
                "语文",
                min_value=0.0,
                max_value=150.0,
                value=float(student_data.get("chinese_score", 120.0)) if student_data else 120.0,
                help="语文成绩"
            )

            form_data["math_score"] = st.number_input(
                "数学",
                min_value=0.0,
                max_value=150.0,
                value=float(student_data.get("math_score", 120.0)) if student_data else 120.0,
                help="数学成绩"
            )

        with col2:
            form_data["english_score"] = st.number_input(
                "英语",
                min_value=0.0,
                max_value=150.0,
                value=float(student_data.get("english_score", 120.0)) if student_data else 120.0,
                help="英语成绩"
            )

            form_data["total_score"] = st.number_input(
                "总分",
                min_value=0.0,
                max_value=750.0,
                value=float(student_data.get("total_score", 680.0)) if student_data else 680.0,
                help="总分（满分 750）"
            )

        with col3:
            form_data["ranking"] = st.number_input(
                "位次",
                min_value=0,
                value=int(student_data.get("ranking", 1000)) if student_data else 1000,
                help="年级/市位次"
            )

        st.markdown("### 兴趣特长")

        form_data["interests"] = st.multiselect(
            "兴趣领域",
            ["编程", "机器人", "数学", "物理", "化学", "生物", "文学", "历史", "外语", "艺术", "体育"],
            default=student_data.get("interests", []) if student_data else [],
            help="选择兴趣领域"
        )

        form_data["specialities"] = st.text_area(
            "特长与竞赛获奖",
            value=student_data.get("specialities_str", "") if student_data else "",
            help="例如：信息学竞赛省二、钢琴十级等",
            placeholder="请输入特长和竞赛获奖情况"
        )

        st.markdown("### 家庭情况")

        col1, col2 = st.columns(2)

        with col1:
            form_data["family_budget"] = st.number_input(
                "家庭教育预算（万元/年）",
                min_value=0.0,
                max_value=1000.0,
                value=float(student_data.get("family_budget", 10.0)) if student_data else 10.0,
                help="每年教育预算"
            )

        with col2:
            form_data["preferred_locations"] = st.multiselect(
                "偏好地区",
                ["北京", "上海", "广东", "浙江", "江苏", "辽宁", "其他"],
                default=student_data.get("preferred_locations", []) if student_data else [],
                help="偏好就读地区"
            )

        # 提交按钮
        submitted = st.form_submit_button("💾 保存档案", use_container_width=True)

        form_data["submitted"] = submitted

    return form_data


def render_student_list(students: list[dict[str, Any]]):
    """
    渲染学生列表

    Args:
        students: 学生列表
    """
    if not students:
        render_empty_state(
            "暂无学生档案",
            "点击右上角\"创建档案\"按钮添加第一个学生",
            icon="📭"
        )
        return

    st.markdown(f"### 📋 学生列表 ({len(students)} 人)")

    for _i, student in enumerate(students, 1):
        render_student_card(student)


def main():
    """主函数"""
    render_header("学生档案管理", "创建和管理学生档案")

    # 从数据库加载学生数据
    if "students" not in st.session_state or st.session_state.get("refresh_students", False):
        st.session_state.students = load_students_from_db()
        st.session_state.refresh_students = False

    students = st.session_state.students

    # 侧边栏操作
    with st.sidebar:
        st.markdown("### 操作")

        if st.button("➕ 创建档案", use_container_width=True):
            st.session_state.show_form = True
            st.session_state.editing_student = None

        if st.button("📋 学生列表", use_container_width=True):
            st.session_state.show_form = False

        st.markdown("---")

        # 搜索
        search_query = st.text_input("🔍 搜索学生", placeholder="输入姓名或学校")

    # 显示表单或列表
    if st.session_state.get("show_form", False):
        # 表单模式
        editing_student = st.session_state.get("editing_student")

        form_data = render_student_form(editing_student)

        if form_data.get("submitted"):
            # 验证必填字段
            if not form_data.get("name") or not form_data.get("grade") or not form_data.get("city"):
                st.error("请填写必填字段（姓名、年级、城市）")
            else:
                # 创建或更新学生
                student = {
                    "id": editing_student.get("id") if editing_student and "id" in editing_student else None,
                    "name": form_data["name"],
                    "student_code": editing_student.get("student_code") if editing_student else None,
                    "grade": form_data["grade"],
                    "city": form_data["city"],
                    "school": form_data["school"],
                    "category": form_data["category"],
                    "total_score": form_data["total_score"],
                    "ranking": form_data["ranking"],
                    "chinese_score": form_data["chinese_score"],
                    "math_score": form_data["math_score"],
                    "english_score": form_data["english_score"],
                    "interests": form_data["interests"],
                    "specialities": form_data["specialities"],
                    "awards": form_data.get("awards", []),
                    "family_budget": form_data["family_budget"],
                    "preferred_locations": form_data["preferred_locations"],
                }

                if save_student_to_db(student):
                    if editing_student and "id" in editing_student:
                        st.success(f"✅ 学生 {student['name']} 信息已更新")
                    else:
                        st.success(f"✅ 学生 {student['name']} 档案已创建")

                    # 刷新学生列表
                    st.session_state.refresh_students = True
                    st.session_state.show_form = False
                    st.session_state.editing_student = None
                    st.rerun()
                else:
                    st.error("保存失败，请重试")

    else:
        # 列表模式
        # 从 session state 获取学生列表
        students = st.session_state.students

        # 搜索过滤
        if search_query:
            students = [
                s for s in students
                if search_query.lower() in s.get("name", "").lower()
                or search_query.lower() in s.get("school", "").lower()
            ]

        if not students:
            render_empty_state(
                "暂无学生档案",
                '点击"➕ 创建档案"添加第一个学生',
                icon="📭"
            )
        else:
            st.markdown(f"### 📋 学生列表 ({len(students)} 人)")

            for _i, student in enumerate(students, 1):
                render_student_card(student)


if __name__ == "__main__":
    main()
