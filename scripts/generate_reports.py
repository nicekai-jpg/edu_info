#!/usr/bin/env python3
"""
升学规划批量报告生成器

读取 data/input_students.json，利用规划引擎计算后为每个学生生成精美的 Markdown 报告。
"""
import sys
import os
import json
from pathlib import Path
import duckdb

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edu_info.core.planning_engine import PlanningEngine
from edu_info.core.target_generator import ScoreRange
from edu_info.models.schemas import Student, University
from edu_info.utils.logger import setup_logger

logger = setup_logger("batch_report_generator")

def ensure_database():
    """确保本地 DuckDB 数据库存在并初始化"""
    db_path = Path("data/duckdb/edu_planning.db")
    if not db_path.exists():
        logger.info("数据库文件不存在，正在进行自动初始化与数据导入...")
        # 调用初始化脚本
        import subprocess
        subprocess.run([sys.executable, "scripts/init_database.py"], check=True)
        subprocess.run([sys.executable, "scripts/import_2025_data.py"], check=True)
        logger.info("数据库初始化及数据加载完成！")
    return db_path

def load_universities(conn):
    """从数据库加载高校列表"""
    rows = conn.execute("""
        SELECT id, name, code, location, type, 
               is_985, is_211, is_double_first_class, project_type 
        FROM universities
    """).fetchall()
    
    return [
        University(
            id=r[0], name=r[1], code=r[2] or "00000", location=r[3] or "未知", type=r[4] or "综合",
            is_985=bool(r[5]), is_211=bool(r[6]), is_double_first_class=bool(r[7]), project_type=r[8]
        ) for r in rows
    ]

def load_score_data(conn):
    """从数据库计算并加载 2025 年高校的录取分数范围"""
    rows = conn.execute("""
        SELECT university_id, 
               MIN(min_score) as min_score,
               CAST(AVG(min_score) as INTEGER) as avg_score,
               MAX(min_score) as max_score,
               MAX(min_rank) as min_rank,
               CAST(AVG(min_rank) as INTEGER) as avg_rank,
               MIN(min_rank) as max_rank
        FROM admission_scores
        WHERE year = 2025
        GROUP BY university_id
    """).fetchall()
    
    score_data = {}
    for r in rows:
        if r[1] is not None and r[4] is not None:
            score_data[r[0]] = ScoreRange(
                min_score=r[1],
                avg_score=r[2] or r[1],
                max_score=r[3] or r[1],
                min_rank=r[4],
                avg_rank=r[5] or r[4],
                max_rank=r[6] or r[4]
            )
    return score_data

def generate_markdown_report(student: Student, result) -> str:
    """生成 Markdown 报告格式文本"""
    # 格式化兴趣和位置
    interests = "、".join(student.interests or []) if student.interests else "无"
    locations = "、".join(student.preferred_locations or []) if student.preferred_locations else "不限"
    
    # 最佳通道
    best_match = result.top_routes[0] if result.top_routes else None
    best_route_name = best_match.route.route_name if best_match else "普通高考"
    best_score = best_match.match_score if best_match else 0
    
    report = f"""# 🧑‍🎓 {student.name} 同学升学规划方案报告

## 📌 1. 学生基本档案 (Student Profile)
- **姓名**：{student.name}
- **年级**：{student.grade}
- **高考科类**：{student.category}
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

### 🔥 3.1 冲刺目标 (Reach Universities) - 建议填报在第一志愿序列 (录取概率 30% - 50%)
"""
    if result.high_targets:
        for i, target in enumerate(result.high_targets, 1):
            report += f"{i}. **{target.university.name}** ({target.university.location})\n"
            report += f"   - **推荐专业**：{target.major or '相关计算机/热门专业'}\n"
            report += f"   - **2025最低分/位次**：{target.min_score} 分 / 第 {target.min_rank} 名\n"
            report += f"   - **录取概率估计**：{target.probability:.1f}%\n"
            report += f"   - **规划建议**：{target.analysis or '分数线接近，建议作为冲刺志愿填报，关注省排名动态。'}\n\n"
    else:
        report += "* 暂无符合条件的冲刺目标高校，建议根据一分一段表微调志愿范围。\n\n"

    report += """### 💎 3.2 稳妥目标 (Match Universities) - 建议填报在中间志愿序列 (录取概率 50% - 80%)
"""
    if result.medium_targets:
        for i, target in enumerate(result.medium_targets, 1):
            report += f"{i}. **{target.university.name}** ({target.university.location})\n"
            report += f"   - **推荐专业**：{target.major or '相关计算机/热门专业'}\n"
            report += f"   - **2025最低分/位次**：{target.min_score} 分 / 第 {target.min_rank} 名\n"
            report += f"   - **录取概率估计**：{target.probability:.1f}%\n"
            report += f"   - **规划建议**：{target.analysis or '分数匹配度高，录取概率较大，建议作为稳妥志愿填报。'}\n\n"
    else:
        report += "* 暂无符合条件的稳妥目标高校。\n\n"

    report += """### 🛡️ 3.3 保底目标 (Safety Universities) - 建议填报在靠后志愿序列 (录取概率 80% - 95%)
"""
    if result.low_targets:
        for i, target in enumerate(result.low_targets, 1):
            report += f"{i}. **{target.university.name}** ({target.university.location})\n"
            report += f"   - **推荐专业**：{target.major or '相关计算机/热门专业'}\n"
            report += f"   - **2025最低分/位次**：{target.min_score} 分 / 第 {target.min_rank} 名\n"
            report += f"   - **录取概率估计**：{target.probability:.1f}%\n"
            report += f"   - **规划建议**：{target.analysis or '分数留有充足安全余量，录取极有保障，建议作为保底志愿填报。'}\n\n"
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
    # 确保数据库就绪
    db_path = ensure_database()
    
    # 建立 DuckDB 连接
    conn = duckdb.connect(str(db_path))
    
    # 加载支撑数据
    logger.info("正在从数据库加载高校和分数映射数据...")
    universities = load_universities(conn)
    score_data = load_score_data(conn)
    
    # 初始化规划引擎
    engine = PlanningEngine(str(db_path))
    
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
            interests=s_data.get("interests", []),
            family_budget=s_data.get("family_budget", 10.0),
            preferred_locations=s_data.get("preferred_locations", []),
        )
        
        # 运行规划计算
        result = engine.generate_plan(student, universities, score_data)
        
        # 渲染 Markdown
        report_md = generate_markdown_report(student, result)
        
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
        
    conn.close()
    
    # 输出简要汇总表格
    print("\n" + "="*50)
    print(" 🚀 规划批量计算与报告生成完成汇总 ")
    print("="*50)
    print(f"{'姓名':<8}{'科类':<8}{'成绩':<8}{'推荐最佳赛道':<16}{'方案可行性分':<10}")
    print("-"*50)
    for s in summary:
        print(f"{s['姓名']:<8}{s['科类']:<8}{s['分数']:<8.1f}{s['推荐赛道']:<16}{s['可行性分']:<10}")
    print("="*50)
    print(f"生成的精美 Markdown 报告已全部存入: [output/reports/](file://{output_dir.absolute()})\n")

if __name__ == "__main__":
    main()
