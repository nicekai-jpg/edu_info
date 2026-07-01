import sys
from pathlib import Path

import duckdb

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from edu_info.utils.logger import setup_logger

logger = setup_logger("major_injector")

# 标准专业模版 (基于教育部目录)
MAJOR_TEMPLATES = {
    "理工": [
        {"name": "计算机科学与技术", "category": "工学", "major_class": "计算机类", "duration": 4, "degree": "工学学士"},
        {"name": "软件工程", "category": "工学", "major_class": "计算机类", "duration": 4, "degree": "工学学士"},
        {"name": "人工智能", "category": "工学", "major_class": "计算机类", "duration": 4, "degree": "工学学士"},
        {"name": "电子信息工程", "category": "工学", "major_class": "电子信息类", "duration": 4, "degree": "工学学士"},
        {"name": "自动化", "category": "工学", "major_class": "自动化类", "duration": 4, "degree": "工学学士"},
        {"name": "机械设计制造及其自动化", "category": "工学", "major_class": "机械类", "duration": 4, "degree": "工学学士"},
        {"name": "电气工程及其自动化", "category": "工学", "major_class": "电气类", "duration": 4, "degree": "工学学士"},
        {"name": "通信工程", "category": "工学", "major_class": "电子信息类", "duration": 4, "degree": "工学学士"},
        {"name": "数学与应用数学", "category": "理学", "major_class": "数学类", "duration": 4, "degree": "理学学士"},
        {"name": "物理学", "category": "理学", "major_class": "物理学类", "duration": 4, "degree": "理学学士"},
    ],
    "综合": [
        {"name": "汉语言文学", "category": "文学", "major_class": "中国语言文学类", "duration": 4, "degree": "文学学士"},
        {"name": "法学", "category": "法学", "major_class": "法学类", "duration": 4, "degree": "法学学士"},
        {"name": "经济学", "category": "经济学", "major_class": "经济学类", "duration": 4, "degree": "经济学学士"},
        {"name": "金融学", "category": "经济学", "major_class": "金融学类", "duration": 4, "degree": "经济学学士"},
        {"name": "工商管理", "category": "管理学", "major_class": "工商管理类", "duration": 4, "degree": "管理学学士"},
        {"name": "会计学", "category": "管理学", "major_class": "工商管理类", "duration": 4, "degree": "管理学学士"},
        {"name": "新闻学", "category": "文学", "major_class": "新闻传播学类", "duration": 4, "degree": "文学学士"},
        {"name": "英语", "category": "文学", "major_class": "外国语言文学类", "duration": 4, "degree": "文学学士"},
    ],
    "医药": [
        {"name": "临床医学", "category": "医学", "major_class": "临床医学类", "duration": 5, "degree": "医学学士"},
        {"name": "口腔医学", "category": "医学", "major_class": "口腔医学类", "duration": 5, "degree": "医学学士"},
        {"name": "药学", "category": "医学", "major_class": "药学类", "duration": 4, "degree": "理学学士"},
        {"name": "护理学", "category": "医学", "major_class": "护理学类", "duration": 4, "degree": "理学学士"},
        {"name": "中医学", "category": "医学", "major_class": "中医学类", "duration": 5, "degree": "医学学士"},
    ],
    "财经": [
        {"name": "会计学", "category": "管理学", "major_class": "工商管理类", "duration": 4, "degree": "管理学学士"},
        {"name": "金融学", "category": "经济学", "major_class": "金融学类", "duration": 4, "degree": "经济学学士"},
        {"name": "财务管理", "category": "管理学", "major_class": "工商管理类", "duration": 4, "degree": "管理学学士"},
        {"name": "国际经济与贸易", "category": "经济学", "major_class": "经济与贸易类", "duration": 4, "degree": "经济学学士"},
        {"name": "审计学", "category": "管理学", "major_class": "工商管理类", "duration": 4, "degree": "管理学学士"},
    ],
    "师范": [
        {"name": "汉语言文学（师范）", "category": "文学", "major_class": "中国语言文学类", "duration": 4, "degree": "文学学士"},
        {"name": "数学与应用数学（师范）", "category": "理学", "major_class": "数学类", "duration": 4, "degree": "理学学士"},
        {"name": "英语（师范）", "category": "文学", "major_class": "外国语言文学类", "duration": 4, "degree": "文学学士"},
        {"name": "教育学", "category": "教育学", "major_class": "教育学类", "duration": 4, "degree": "教育学学士"},
        {"name": "学前教育", "category": "教育学", "major_class": "教育学类", "duration": 4, "degree": "教育学学士"},
    ]
}

def main():
    db_path = Path(__file__).parent.parent / "data" / "duckdb" / "edu_planning.db"
    conn = duckdb.connect(str(db_path))

    # 获取所有院校
    unis = conn.execute("SELECT id, name, type FROM universities").fetchall()
    logger.info(f"开始为 {len(unis)} 所院校注入真实专业...")

    # 清理旧专业（可选，如果你想完全重新开始）
    # conn.execute("DELETE FROM majors")

    # 确保序列存在
    conn.execute("CREATE SEQUENCE IF NOT EXISTS majors_id_seq;")

    total_majors = 0
    for uni_id, uni_name, uni_type in unis:
        # 根据学校类型选择模版，默认为综合
        template_key = uni_type if uni_type in MAJOR_TEMPLATES else "综合"
        majors = MAJOR_TEMPLATES[template_key]

        # 补充：如果是 985/211，额外增加几个通用理工专业
        is_985_211 = conn.execute("SELECT is_double_first_class FROM universities WHERE id = ?", (uni_id,)).fetchone()[0]
        if is_985_211 and template_key != "理工":
            majors = majors + MAJOR_TEMPLATES["理工"][:3]

        for m in majors:
            try:
                # 使用 ON CONFLICT 处理重复 (university_id + name)
                conn.execute("""
                    INSERT INTO majors (
                        id, university_id, name, category, major_class, duration, degree, is_ln_recruiting
                    ) VALUES (nextval('majors_id_seq'), ?, ?, ?, ?, ?, ?, TRUE)
                    ON CONFLICT (university_id, name) DO UPDATE SET
                        category = excluded.category,
                        major_class = excluded.major_class,
                        duration = excluded.duration,
                        degree = excluded.degree,
                        is_ln_recruiting = TRUE
                """, (
                    uni_id, m["name"], m["category"], m.get("major_class"), m["duration"], m["degree"]
                ))
                total_majors += 1
            except Exception as e:
                logger.error(f"注入失败 {uni_name} - {m['name']}: {e}")

    conn.commit()
    conn.close()
    logger.info(f"✅ 成功注入/更新 {total_majors} 个专业数据。")

if __name__ == "__main__":
    main()
