import random
import sys
from pathlib import Path

import duckdb

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from edu_info.utils.logger import setup_logger

logger = setup_logger("score_generator")

def get_base_score(uni):
    """根据院校档次确定基准分 (2025 辽宁物理类)"""
    if uni['is_985']:
        if uni['name'] in ["北京大学", "清华大学", "复旦大学", "上海交通大学", "中国科学院大学", "浙江大学", "中国科学技术大学"]:
            return random.randint(685, 705)
        return random.randint(630, 675)
    elif uni['is_211']:
        return random.randint(590, 630)
    elif uni['is_double_first_class']:
        return random.randint(560, 595)

    # 辽宁省内公办本科
    if "辽宁" in uni['location'] or "沈阳" in uni['location'] or "大连" in uni['location']:
        if uni['type'] in ["医药", "财经"]:
            return random.randint(510, 560)
        return random.randint(460, 520)

    # 民办或外省普通本科
    if uni['id'] > 13000: # 简易判断民办代码区间
        return random.randint(390, 460)

    return random.randint(450, 500)

def get_major_offset(major_name):
    """根据专业热门程度调整分数"""
    hot_keywords = ["计算机", "人工智能", "软件", "电子", "金融", "数据科学", "临床医学", "口腔"]
    cold_keywords = ["哲学", "历史", "农学", "园艺", "护理", "公共事业"]

    for kw in hot_keywords:
        if kw in major_name:
            return random.randint(8, 15)
    for kw in cold_keywords:
        if kw in major_name:
            return random.randint(-15, -5)
    return random.randint(-3, 3)

def main():
    db_path = Path(__file__).parent.parent / "data" / "duckdb" / "edu_planning.db"
    conn = duckdb.connect(str(db_path))

    # 获取所有院校信息
    unis = conn.execute("""
        SELECT id, name, is_985, is_211, is_double_first_class, location, type
        FROM universities
    """).fetchall()

    uni_map = {u[0]: {
        'id': u[0], 'name': u[1], 'is_985': u[2], 'is_211': u[3],
        'is_double_first_class': u[4], 'location': u[5], 'type': u[6]
    } for u in unis}

    # 获取所有专业
    majors = conn.execute("SELECT id, university_id, name FROM majors").fetchall()

    logger.info(f"开始为 {len(majors)} 个专业生成 2025 年参考分数线...")

    # 确保序列
    conn.execute("CREATE SEQUENCE IF NOT EXISTS scores_id_seq;")

    success = 0
    for major_id, uni_id, major_name in majors:
        uni = uni_map.get(uni_id)
        if not uni:
            continue

        # 核心逻辑：生成分数
        base = get_base_score(uni)
        offset = get_major_offset(major_name)
        final_score = base + offset

        # 对应估算位次 (根据辽宁物理类一分一段表粗略模拟)
        # 700分->50名, 680分->300名, 650分->2500名, 600分->15000名, 550分->40000名, 510分->70000名
        if final_score >= 680:
            rank = random.randint(50, 400)
        elif final_score >= 650:
            rank = random.randint(1000, 3000)
        elif final_score >= 600:
            rank = random.randint(10000, 18000)
        elif final_score >= 550:
            rank = random.randint(35000, 45000)
        elif final_score >= 510:
            rank = random.randint(65000, 75000)
        else:
            rank = random.randint(80000, 120000)

        try:
            conn.execute("""
                INSERT INTO admission_scores (
                    id, university_id, major_id, year, province, category, min_score, min_rank, batch
                ) VALUES (nextval('scores_id_seq'), ?, ?, 2025, '辽宁', '物理类', ?, ?, '本科批')
                ON CONFLICT (university_id, major_id, year, province, category) DO UPDATE SET
                    min_score = excluded.min_score,
                    min_rank = excluded.min_rank
            """, (uni_id, major_id, final_score, rank))
            success += 1
        except Exception as e:
            logger.error(f"生成失败 {uni['name']} - {major_name}: {e}")

    conn.commit()
    conn.close()
    logger.info(f"✅ 成功生成 {success} 条 2025 年参考分数数据。")

if __name__ == "__main__":
    main()
