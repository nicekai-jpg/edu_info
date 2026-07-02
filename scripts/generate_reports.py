#!/usr/bin/env python3
"""
升学规划批量报告生成器 (纯内存历年数据升级版)

直接读取 data/raw/2025/ 目录下的 JSON 文本文件装载到内存中，无需依赖 DuckDB。
读取 data/input_students.json，为每个学生生成精美的包含历年投档线走势的 Markdown 规划报告。
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edu_info.core.planning_engine import PlanningEngine
from edu_info.core.target_generator import ScoreRange
from edu_info.models.schemas import Student, University, TargetUniversity
from edu_info.utils.logger import setup_logger

logger = setup_logger("batch_report_generator")

def load_universities_from_json(data_dir: Path) -> list[University]:
    """直接从 JSON 文件加载高校列表"""
    file_path = data_dir / "universities_2025.json"
    logger.info(f"从 {file_path} 加载高校数据...")
    
    with open(file_path, encoding="utf-8") as f:
        uni_data = json.load(f)
        
    return [
        University(
            id=u["id"],
            name=u["name"],
            code=u.get("code") or "00000",
            location=u.get("location") or "未知",
            type=u.get("type") or "综合",
            is_985=bool(u.get("is_985", False)),
            is_211=bool(u.get("is_211", False)),
            is_double_first_class=bool(u.get("is_double_first_class", False)),
            project_type=u.get("project_type"),
            ownership=u.get("ownership") or "公办",
            tuition_fee=u.get("tuition_fee") or 5500,
            english_name=u.get("english_name"),
            website=u.get("website"),
            ownership_type=u.get("ownership_type") or u.get("ownership") or "公办",
            industry_tags=u.get("industry_tags") or [],
            city_level=u.get("city_level"),
            discipline_evaluations=u.get("discipline_evaluations") or {},
            doctorate_points=u.get("doctorate_points") or 0,
            master_points=u.get("master_points") or 0,
            national_key_disciplines=u.get("national_key_disciplines") or [],
            accommodation_fee=u.get("accommodation_fee") or 1200,
            major_tuition_fees=u.get("major_tuition_fees") or {},
            avg_living_cost=u.get("avg_living_cost"),
            overall_employment_rate=u.get("overall_employment_rate"),
            postgraduate_rate=u.get("postgraduate_rate"),
            abroad_rate=u.get("abroad_rate"),
            key_employers=u.get("key_employers") or [],
            description=u.get("description"),
            key_labs=u.get("key_labs") or [],
            famous_alumni=u.get("famous_alumni") or [],
            tuition_rules=u.get("tuition_rules") or {},
            admission_constraints=u.get("admission_constraints") or {},
            career_metrics=u.get("career_metrics") or {},
            academic_accreditations=u.get("academic_accreditations") or {}
        ) for u in uni_data
    ]

def load_score_data_from_json(data_dir: Path) -> tuple[dict[int, ScoreRange], list[dict]]:
    """直接从 JSON 分数文件在内存中过滤 2025 年数据用于计算，并保留完整数据列表用于历史匹配"""
    file_path = data_dir / "scores_2025.json"
    logger.info(f"从 {file_path} 加载并聚合分数数据...")
    
    with open(file_path, encoding="utf-8") as f:
        scores_raw = json.load(f)
        
    # 按 university_id 归类 2025 年的分数和位次
    uni_scores = {}
    for s in scores_raw:
        # 只取 2025 年数据用于“当前规划”的匹配基准
        if s.get("year") != 2025:
            continue
            
        uni_id = s["university_id"]
        min_score = s.get("min_score")
        min_rank = s.get("min_rank")
        
        if min_score is not None and min_rank is not None:
            uni_scores.setdefault(uni_id, []).append((min_score, min_rank))
            
    # 计算并封装成 ScoreRange
    score_data = {}
    for uni_id, score_tuples in uni_scores.items():
        scores = [t[0] for t in score_tuples]
        ranks = [t[1] for t in score_tuples]
        
        min_score = min(scores)
        avg_score = int(sum(scores) / len(scores))
        max_score = max(scores)
        
        min_rank = max(ranks)  # 投档最低位次（数值最大）
        avg_rank = int(sum(ranks) / len(ranks))
        max_rank = min(ranks)  # 投档最高位次（数值最小）
        
        score_data[uni_id] = ScoreRange(
            min_score=min_score,
            avg_score=avg_score,
            max_score=max_score,
            min_rank=min_rank,
            avg_rank=avg_rank,
            max_rank=max_rank
        )
        
    return score_data, scores_raw

def major_matches(category_name: str, specific_name: str) -> bool:
    """判断具体专业名是否属于大类专业"""
    if not category_name or not specific_name:
        return False
    if category_name == specific_name:
        return True
    cat = category_name.strip()
    spec = specific_name.strip()
    if cat.endswith("类"):
        core = cat[:-1]
    else:
        core = cat
    if core in spec:
        return True
        
    special_mappings = {
        "计算机类": ["计算机", "软件", "大数据", "网络工程", "人工智能", "信息安全", "智能科学与技术"],
        "电子信息类": ["电子", "通信", "集成电路", "微电子", "光电"],
        "经济学类": ["经济", "金融", "财政", "税收"],
        "工商管理类": ["管理", "会计", "财务", "审计", "营销"],
        "数学类": ["数学", "统计"],
    }
    if cat in special_mappings:
        for keyword in special_mappings[cat]:
            if keyword in spec:
                return True
    return False

def format_history_scores(target, scores_raw: list[dict], major_id_to_name: dict) -> str:
    """提取该院校推荐分类下的相关专业历年录取最低分数走势"""
    history_by_year = {}
    for s in scores_raw:
        if s["university_id"] == target.university.id:
            m_name = major_id_to_name.get(s["major_id"])
            if m_name and major_matches(target.major, m_name):
                history_by_year.setdefault(s["year"], []).append(s)
                
    years = sorted(list(history_by_year.keys()), reverse=True)
    
    parts = []
    for y in years:
        if y == 2025:
            continue
        year_scores = history_by_year[y]
        min_score = min(x["min_score"] for x in year_scores)
        max_rank = max(x["min_rank"] for x in year_scores)
        parts.append(f"{y}年: {min_score}分(位次第{max_rank}名)")
        
    if not parts:
        return "暂无往年同大类专业录取参考数据"
        
    return "历年参考投档线：" + "；".join(parts)


def format_target_university(i: int, target: TargetUniversity, scores_raw: list[dict], major_id_to_name: dict) -> str:
    from edu_info.core.target_generator import get_major_tuition
    
    history_str = format_history_scores(target, scores_raw, major_id_to_name)
    spec_tuition = get_major_tuition(target.university, target.major or "")
    
    # 构造学科实力与评级字符串
    eval_grades = []
    if target.university.discipline_evaluations:
        for m_key, grade in target.university.discipline_evaluations.items():
            if m_key in (target.major or "") or (target.major or "") in m_key:
                eval_grades.append(f"{m_key}学科评估为 **[{grade}]**")
    
    academic_str = ""
    if eval_grades:
        academic_str += "、".join(eval_grades)
    if target.university.doctorate_points:
        academic_str += ("；" if academic_str else "") + f"拥有一级学科博士点 {target.university.doctorate_points} 个"
    elif target.university.master_points:
        academic_str += ("；" if academic_str else "") + f"拥有一级学科硕士点 {target.university.master_points} 个"
        
    # 就业与深造前景
    employ_parts = []
    if target.university.postgraduate_rate:
        employ_parts.append(f"国内读研深造率 {target.university.postgraduate_rate:.1f}%")
    if target.university.abroad_rate:
        employ_parts.append(f"出国深造率 {target.university.abroad_rate:.1f}%")
    if target.university.overall_employment_rate:
        employ_parts.append(f"毕业生总体就业率 {target.university.overall_employment_rate:.1f}%")
    employ_str = ", ".join(employ_parts) if employ_parts else "暂无官方就业质量报告数据"
    
    # 行业名片与背景底蕴
    bg_parts = []
    if target.university.industry_tags:
        bg_parts.append(f"业内美誉：{'、'.join(target.university.industry_tags)}")
    if target.university.key_labs:
        bg_parts.append(f"重点实验室/国家平台：{'、'.join(target.university.key_labs)}")
    if target.university.famous_alumni:
        bg_parts.append(f"知名杰出校友：{'、'.join(target.university.famous_alumni)}")
    bg_str = "; ".join(bg_parts)
    
    # 组合输出
    out = f"{i}. **{target.university.name}** ({target.university.location})\n"
    out += f"   - **推荐专业**：{target.major or '相关专业'}\n"
    out += f"   - **录取概率估计**：{target.probability:.1f}%\n"
    out += f"   - **2025年最低投档线**：{target.min_score} 分 (最低位次：第 {target.min_rank} 名)\n"
    out += f"   - **办学性质与费用**：{target.university.ownership or '公办'} / 细分学费约 {spec_tuition}元/年 (住宿费约 {target.university.accommodation_fee or 1200}元/年)\n"
    
    if academic_str:
        out += f"   - **学科实力与办学层次**：{academic_str}\n"
    if bg_str:
        out += f"   - **办学底蕴与名片**：{bg_str}\n"
    if employ_str:
        out += f"   - **深造与就业前景**：{employ_str}\n"
        if target.university.key_employers:
            out += f"     * 核心合作单位去向：{'、'.join(target.university.key_employers[:4])}\n"
            
    out += f"   - **{history_str}**\n"
    out += f"   - **规划建议**：{target.analysis or '分数线接近，建议作为填报志愿选择，重点关注专业倾向。'}\n\n"
    return out


def generate_markdown_report(student: Student, result, scores_raw: list[dict], major_id_to_name: dict) -> str:
    """生成 Markdown 报告格式文本"""
    interests = "、".join(student.interests or []) if student.interests else "无"
    locations = "、".join(student.preferred_locations or []) if student.preferred_locations else "不限"
    
    best_match = result.top_routes[0] if result.top_routes else None
    best_route_name = best_match.route.route_name if best_match else "普通高考"
    
    subjects_str = "、".join(student.subjects) if student.subjects else "物理、化学、生物（默认标准理科组合）" if student.category == "物理类" else "历史、政治、地理（默认标准文科组合）"
    
    # 选科冲突警告
    targets_empty_warning = ""
    if not result.high_targets and not result.medium_targets and not result.low_targets:
        from edu_info.core.subject_validator import SubjectValidator
        req_primary, req_secondaries = SubjectValidator.get_required_subjects(best_route_name, student.category)
        if "化学" in req_secondaries and (not student.subjects or "化学" not in student.subjects):
            targets_empty_warning = f"""> [!WARNING]
> **重要提示（选科红线预警）：**
> 您偏好的专业方向 **{best_route_name}**（如计算机类、电子信息类等理工农医类专业）要求首选物理且**再选科目必须包含 [化学]**。
> 您的选考组合为 **{subjects_str}**，因**缺少 [化学]** 导致无法投档报考此类专业。
> **建议行动**：建议修改学业兴趣，避开需要物理和化学的理工农医专业，或者调整升学规划路线（如选择数学类、金融学、管理科学等不限化学的专业）。
\n"""

    report = f"""# 🧑‍🎓 {student.name} 同学升学规划方案报告

## 📌 1. 学生基本档案 (Student Profile)
- **姓名**：{student.name}
- **年级**：{student.grade}
- **高考科类**：{student.category}
- **选考科目组合**：{subjects_str}
- **生源地**：辽宁省{student.city or '未指定'}
- **高考估分/成绩**：{student.total_score or '未输入'} 分 (预估省位次：第 {student.ranking or '未指定'} 名)
- **家庭预算限制**：{student.family_budget or '不限'} 万元/年
- **偏好城市**：{locations}
- **兴趣方向**：{interests}

---

## 🗺️ 2. 推荐升学赛道与匹配打分 (Recommended Paths)
根据学生的学业成绩、个人特长及预算，系统匹配出的 Top 3 最佳升学赛道：

| 推荐赛道 | 赛道类型 | 匹配度得分 | 核心行动建议 |
| :--- | :--- | :---: | :--- |
"""
    
    for i, match in enumerate(result.top_routes[:3], 1):
        rec_txt = match.recommendations[0] if match.recommendations else "保持平时成绩，关注最新招生简章"
        report += f"| {i}. **{match.route.route_name}** | {match.route.route_type} | {match.match_score:.1f} 分 | {rec_txt} |\n"
        
    report += f"""
---

## 🏫 3. 2025 年高校录取“冲稳保”推荐 (Target Universities)
根据 **{best_route_name}** 赛道，结合 2025 年辽宁省招生录取分数线，为您推荐以下三档目标高校：

{targets_empty_warning}### 🔥 3.1 冲刺目标 (Reach Universities) - 建议填报在第一志愿序列 (录取概率 30% - 50%)
"""
    if result.high_targets:
        for i, target in enumerate(result.high_targets, 1):
            report += format_target_university(i, target, scores_raw, major_id_to_name)
    else:
        report += "* 暂无符合条件的冲刺目标高校，建议根据一分一段表微调志愿范围。\n\n"

    report += """### 💎 3.2 稳妥目标 (Match Universities) - 建议填报在中间志愿序列 (录取概率 50% - 80%)
"""
    if result.medium_targets:
        for i, target in enumerate(result.medium_targets, 1):
            report += format_target_university(i, target, scores_raw, major_id_to_name)
    else:
        report += "* 暂无符合条件的稳妥目标高校。\n\n"

    report += """### 🛡️ 3.3 保底目标 (Safety Universities) - 建议填报在靠后志愿序列 (录取概率 80% - 95%)
"""
    if result.low_targets:
        for i, target in enumerate(result.low_targets, 1):
            report += format_target_university(i, target, scores_raw, major_id_to_name)
    else:
        report += "* 暂无符合条件的保底目标高校。\n\n"

    report += f"""---

## ⚖️ 4. 整体规划可行性与风险评估 (Risk Assessment)
- **推荐方案可行性评分**：{result.overall_feasibility:.1f} / 100
- **综合评估建议**：{result.risk_assessment or '整体路线搭配合理。首选专业方向明确，建议结合自身兴趣坚定执行学业提升计划。'}

---

## 📋 5. 核心行动执行清单 (Action Items)
我们为您的后续执行阶段制定了以下具体清单：
"""
    if result.action_items:
        for item in result.action_items:
            report += f"- [ ] {item}\n"
    else:
        report += "- [ ] 保持平时文化课成绩，重点提升薄弱科目得分\n"
        report += "- [ ] 关注辽宁省招生考试之窗，留意最新招生计划和批次时间安排\n"
        
    report += "\n---\n*报告生成时间：" + result.created_at.strftime("%Y-%m-%d %H:%M:%S") + "*\n"
    return report

def main():
    # 数据目录定义
    data_dir = Path("data/raw/2025")
    
    # 纯内存直接读取 JSON，免去 DuckDB 初始化和 SQL 开销
    logger.info("⚡️ 正在以纯内存 JSON 直读模式加载高校和分数映射数据...")
    universities = load_universities_from_json(data_dir)
    score_data, scores_raw = load_score_data_from_json(data_dir)
    
    # 加载专业库，用于历史映射名称查询
    with open(data_dir / "majors_2025.json", encoding="utf-8") as f:
        majors_raw = json.load(f)
    major_id_to_name = {m["id"]: m["name"] for m in majors_raw}
    
    # 初始化规划引擎（传 None，内存中计算不需要连接数据库）
    engine = PlanningEngine(None)
    
    # 读取输入学生名单
    input_file = Path("data/input_students.json")
    if not input_file.exists():
        logger.error(f"输入文件 {input_file} 不存在！请先创建。")
        return
        
    with open(input_file, encoding="utf-8") as f:
        students_raw = json.load(f)
        
    logger.info(f"读取到 {len(students_raw)} 名学生的规划请求。开始计算...")
    
    output_dir = Path("output/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary = []
    
    for s_data in students_raw:
        student = Student(
            student_code=s_data.get("student_code", "S_TEMP"),
            name=s_data["name"],
            grade=s_data.get("grade", "高三"),
            city=s_data.get("city", "未指定"),
            category=s_data["category"],
            total_score=s_data.get("total_score"),
            ranking=s_data.get("ranking"),
            english_score=s_data.get("english_score"),
            math_score=s_data.get("math_score"),
            interests=s_data.get("interests", []),
            family_budget=s_data.get("family_budget", 10.0),
            preferred_locations=s_data.get("preferred_locations", []),
            subjects=s_data.get("subjects", []),
            color_blind=s_data.get("color_blind", False),
            color_weak=s_data.get("color_weak", False)
        )
        
        # 运行规划计算
        result = engine.generate_plan(student, universities, score_data)
        
        # 渲染 Markdown (包含历年分数趋势数据)
        report_md = generate_markdown_report(student, result, scores_raw, major_id_to_name)
        
        # 写入文件
        report_file = output_dir / f"{student.name}_升学规划报告.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_md)
            
        logger.info(f"✅ 已成功为 {student.name} 生成报告：{report_file}")
        
        best_route = result.top_routes[0].route.route_name if result.top_routes else "普通高考"
        summary.append({
            "姓名": student.name,
            "科类": student.category,
            "分数": student.total_score,
            "推荐赛道": best_route,
            "可行性分": f"{result.overall_feasibility:.1f}"
        })
    
    # 输出简要汇总表格
    print("\n" + "="*50)
    print(" 🚀 规划批量计算与报告生成完成汇总 (纯内存直读版) ")
    print("="*50)
    print(f"{'姓名':<8}{'科类':<8}{'成绩':<8}{'推荐最佳赛道':<16}{'方案可行性分':<10}")
    print("-"*50)
    for s in summary:
        print(f"{s['姓名']:<8}{s['科类']:<8}{s['分数']:<8.1f}{s['推荐赛道']:<16}{s['可行性分']:<10}")
    print("="*50)
    print(f"生成的精美 Markdown 报告已全部存入: [output/reports/](file://{output_dir.absolute()})\n")

if __name__ == "__main__":
    main()
