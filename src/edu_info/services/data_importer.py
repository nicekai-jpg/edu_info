"""
数据导入服务

支持从 Excel、JSON 等格式导入高校、专业、分数线等数据
"""
import json
from pathlib import Path

import duckdb
import pandas as pd

from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


def import_universities_from_json(
    conn: duckdb.DuckDBPyConnection,
    json_path: str,
    batch_size: int = 50
) -> int:
    """
    从 JSON 文件导入高校数据

    Args:
        conn: DuckDB 连接
        json_path: JSON 文件路径
        batch_size: 批量插入大小

    Returns:
        导入的高校数量
    """
    logger.info(f"从 JSON 导入高校数据：{json_path}")

    with open(json_path, encoding='utf-8') as f:
        universities = json.load(f)

    if not isinstance(universities, list):
        universities = [universities]

    # 准备插入数据
    insert_sql = """
    INSERT INTO universities (
        id, name, code, location, type,
        is_985, is_211, is_double_first_class, project_type,
        website, description
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    count = 0
    for univ in universities:
        try:
            conn.execute(insert_sql, [
                univ.get('id'),
                univ.get('name', ''),
                univ.get('code', ''),
                univ.get('location', ''),
                univ.get('type', '综合'),
                univ.get('is_985', False),
                univ.get('is_211', False),
                univ.get('is_double_first_class', False),
                univ.get('project_type'),
                univ.get('website'),
                univ.get('description'),
            ])
            count += 1
        except Exception as e:
            logger.error(f"导入高校 {univ.get('name')} 失败：{e}")

    logger.info(f"成功导入 {count} 所高校")
    return count


def import_universities_from_excel(
    conn: duckdb.DuckDBPyConnection,
    excel_path: str,
    sheet_name: str | None = None
) -> int:
    """
    从 Excel 文件导入高校数据

    Args:
        conn: DuckDB 连接
        excel_path: Excel 文件路径
        sheet_name: 工作表名称（可选）

    Returns:
        导入的高校数量
    """
    logger.info(f"从 Excel 导入高校数据：{excel_path}")

    # 读取 Excel
    if sheet_name:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
    else:
        df = pd.read_excel(excel_path)

    # 准备插入数据
    insert_sql = """
    INSERT INTO universities (
        id, name, code, location, type,
        is_985, is_211, is_double_first_class, project_type,
        website, description
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    count = 0
    for _, row in df.iterrows():
        try:
            conn.execute(insert_sql, [
                row.get('id'),
                row.get('name', ''),
                row.get('code', ''),
                row.get('location', ''),
                row.get('type', '综合'),
                bool(row.get('is_985', False)),
                bool(row.get('is_211', False)),
                bool(row.get('is_double_first_class', False)),
                row.get('project_type'),
                row.get('website'),
                row.get('description'),
            ])
            count += 1
        except Exception as e:
            logger.error(f"导入高校 {row.get('name')} 失败：{e}")

    logger.info(f"成功导入 {count} 所高校")
    return count


def import_majors_from_json(
    conn: duckdb.DuckDBPyConnection,
    json_path: str
) -> int:
    """
    从 JSON 文件导入专业数据

    Args:
        conn: DuckDB 连接
        json_path: JSON 文件路径

    Returns:
        导入的专业数量
    """
    logger.info(f"从 JSON 导入专业数据：{json_path}")

    with open(json_path, encoding='utf-8') as f:
        majors = json.load(f)

    if not isinstance(majors, list):
        majors = [majors]

    insert_sql = """
    INSERT OR REPLACE INTO majors (
        id, university_id, name, code, category,
        degree, duration, discipline_rank, is_national_key
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    count = 0
    for major in majors:
        try:
            conn.execute(insert_sql, [
                major.get('id'),
                major.get('university_id'),
                major.get('name', ''),
                major.get('code'),
                major.get('category'),
                major.get('degree'),
                major.get('duration', 4),
                major.get('discipline_rank'),
                major.get('is_national_key', False),
            ])
            count += 1
        except Exception as e:
            logger.error(f"导入专业 {major.get('name')} 失败：{e}")

    logger.info(f"成功导入 {count} 个专业")
    return count


def import_scores_from_excel(
    conn: duckdb.DuckDBPyConnection,
    excel_path: str,
    sheet_name: str | None = None
) -> int:
    """
    从 Excel 文件导入录取分数线数据

    Args:
        conn: DuckDB 连接
        excel_path: Excel 文件路径
        sheet_name: 工作表名称（可选）

    Returns:
        导入的记录数量
    """
    logger.info(f"从 Excel 导入分数线数据：{excel_path}")

    # 读取 Excel
    if sheet_name:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
    else:
        df = pd.read_excel(excel_path)

    # 插入数据库
    insert_sql = """
    INSERT OR REPLACE INTO admission_scores (
        university_id, major_id, year, province, category,
        min_score, max_score, avg_score,
        min_rank, max_rank,
        plan_count, actual_count, batch
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    count = 0
    for _, row in df.iterrows():
        try:
            conn.execute(insert_sql, [
                row.get('university_id'),
                row.get('major_id'),
                row.get('year'),
                row.get('province', '辽宁'),
                row.get('category', '物理类'),
                row.get('min_score'),
                row.get('max_score'),
                row.get('avg_score'),
                row.get('min_rank'),
                row.get('max_rank'),
                row.get('plan_count'),
                row.get('actual_count'),
                row.get('batch'),
            ])
            count += 1
        except Exception as e:
            logger.error(f"导入分数线记录失败：{e}")

    logger.info(f"成功导入 {count} 条分数线记录")
    return count


def import_students_from_json(
    conn: duckdb.DuckDBPyConnection,
    json_path: str
) -> int:
    """
    从 JSON 文件导入学生档案数据

    Args:
        conn: DuckDB 连接
        json_path: JSON 文件路径

    Returns:
        导入的学生数量
    """
    logger.info(f"从 JSON 导入学生档案：{json_path}")

    with open(json_path, encoding='utf-8') as f:
        students = json.load(f)

    if not isinstance(students, list):
        students = [students]

    # 不插入 id 字段，让它自增
    insert_sql = """
    INSERT INTO students (
        student_code, name, gender, birth_date,
        grade, school, city, category,
        total_score, ranking,
        chinese_score, math_score, english_score,
        other_scores, interests, specialities, awards,
        family_budget, preferred_locations,
        planning_status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    count = 0
    for student in students:
        try:
            conn.execute(insert_sql, [
                student.get('student_code', ''),
                student.get('name', ''),
                student.get('gender'),
                student.get('birth_date'),
                student.get('grade', ''),
                student.get('school'),
                student.get('city', ''),
                student.get('category', '物理类'),
                student.get('total_score'),
                student.get('ranking'),
                student.get('chinese_score'),
                student.get('math_score'),
                student.get('english_score'),
                json.dumps(student.get('other_scores', {})),
                json.dumps(student.get('interests', [])),
                json.dumps(student.get('specialities', [])),
                json.dumps(student.get('awards', [])),
                student.get('family_budget'),
                json.dumps(student.get('preferred_locations', [])),
                student.get('planning_status', '未开始'),
            ])
            count += 1
        except Exception as e:
            logger.error(f"导入学生 {student.get('name')} 失败：{e}")

    logger.info(f"成功导入 {count} 个学生档案")
    return count


def import_routes_from_json(
    conn: duckdb.DuckDBPyConnection,
    json_path: str
) -> int:
    """
    从 JSON 文件导入规划路线数据

    Args:
        conn: DuckDB 连接
        json_path: JSON 文件路径

    Returns:
        导入的路线数量
    """
    logger.info(f"从 JSON 导入规划路线：{json_path}")

    with open(json_path, encoding='utf-8') as f:
        routes = json.load(f)

    if not isinstance(routes, list):
        routes = [routes]

    # 使用 INSERT OR IGNORE 避免 UNIQUE 冲突
    insert_sql = """
    INSERT INTO planning_routes (
        route_id, route_name, route_type, category,
        stages, requirements, timeline,
        target_university_types, target_major_types,
        cost_min, cost_max, description, success_rate
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    count = 0
    for route in routes:
        try:
            conn.execute(insert_sql, [
                route.get('route_id', ''),
                route.get('route_name', ''),
                route.get('route_type', ''),
                route.get('category', ''),
                json.dumps(route.get('stages', [])),
                json.dumps(route.get('requirements', {})),
                json.dumps(route.get('timeline', {})),
                json.dumps(route.get('target_university_types', [])),
                json.dumps(route.get('target_major_types', [])),
                route.get('cost_min'),
                route.get('cost_max'),
                route.get('description', ''),
                route.get('success_rate'),
            ])
            count += 1
        except Exception as e:
            logger.error(f"导入路线 {route.get('route_name')} 失败：{e}")

    logger.info(f"成功导入 {count} 条规划路线")
    return count


def import_sample_data(
    conn: duckdb.DuckDBPyConnection,
    data_type: str = "all",
    data_dir: str | None = None
) -> dict[str, int]:
    """
    导入示例数据

    Args:
        conn: DuckDB 连接
        data_type: 数据类型 (universities/majors/students/routes/all)
        data_dir: 数据目录路径（可选）

    Returns:
        导入统计字典
    """
    if data_dir is None:
        # 默认数据目录
        data_dir = str(Path(__file__).parent.parent / "data")

    logger.info(f"从 {data_dir} 导入示例数据，类型：{data_type}")

    results = {}

    # 导入高校数据
    if data_type in ["universities", "all"]:
        univ_file = Path(data_dir) / "universities_985_211.json"
        if univ_file.exists():
            count = import_universities_from_json(conn, str(univ_file))
            results["universities"] = count
        else:
            logger.warning(f"高校数据文件不存在：{univ_file}")
            results["universities"] = 0

    # 导入学生数据
    if data_type in ["students", "all"]:
        student_file = Path(data_dir) / "sample_students.json"
        if student_file.exists():
            count = import_students_from_json(conn, str(student_file))
            results["students"] = count
        else:
            logger.warning(f"学生数据文件不存在：{student_file}")
            results["students"] = 0

    # 导入路线数据
    if data_type in ["routes", "all"]:
        route_file = Path(data_dir) / "sample_routes.json"
        if route_file.exists():
            count = import_routes_from_json(conn, str(route_file))
            results["routes"] = count
        else:
            logger.warning(f"路线数据文件不存在：{route_file}")
            results["routes"] = 0

    return results


def export_to_json(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    output_path: str
) -> int:
    """
    导出数据库表到 JSON 文件

    Args:
        conn: DuckDB 连接
        table_name: 表名
        output_path: 输出文件路径

    Returns:
        导出的记录数量
    """
    logger.info(f"导出表 {table_name} 到 {output_path}")

    # 查询数据
    query = f"SELECT * FROM {table_name}"
    df = conn.execute(query).fetchdf()

    # 转换为 JSON
    records = df.to_dict('records')

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    logger.info(f"成功导出 {len(records)} 条记录")
    return len(records)
