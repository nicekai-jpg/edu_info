#!/usr/bin/env python3
"""
对数据库中 885 所高校灌装首轮学术评估评级、行业标签、博硕士点数量、
细分专业学费标准、住宿费、深造率及就业率等核心指标。
"""
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("academic_seeder")

DB_PATH = Path("data/raw/2025/universities_2025.json")

# 1. 行业标签 Seeding 列表
INDUSTRY_TAGS = {
    "国防七子": ["北京航空航天大学", "北京理工大学", "哈尔滨工业大学", "哈尔滨工程大学", "南京航空航天大学", "南京理工大学", "西北工业大学"],
    "两电一邮": ["电子科技大学", "西安电子科技大学", "北京邮电大学"],
    "五院四系": ["中国政法大学", "西南政法大学", "西北政法大学", "华东政法大学", "中南财经政法大学", "北京大学", "中国人民大学", "武汉大学", "吉林大学"],
    "电气二龙四虎": ["武汉大学", "华北电力大学", "清华大学", "西安交通大学", "浙江大学", "华中科技大学"],
    "建筑老八校": ["清华大学", "东南大学", "天津大学", "同济大学", "华南理工大学", "哈尔滨工业大学", "西安建筑科技大学", "重庆大学"],
    "四大工学院": ["华中科技大学", "华南理工大学", "大连理工大学", "东南大学"]
}

# 2. 知名高校部分核心专业第四五轮学科评估评级表 (A+/A/A-)
DISCIPLINE_EVALUATIONS = {
    # 计算机类
    "计算机科学与技术": {
        "A+": ["清华大学", "北京大学", "浙江大学", "国防科技大学"],
        "A": ["北京航空航天大学", "北京邮电大学", "哈尔滨工业大学", "上海交通大学", "南京大学", "华中科技大学", "电子科技大学"],
        "A-": ["北京理工大学", "东北大学", "吉林大学", "同济大学", "中国科学技术大学", "武汉大学", "西安交通大学", "西安电子科技大学"]
    },
    # 软件工程
    "软件工程": {
        "A+": ["清华大学", "北京大学", "国防科技大学", "浙江大学"],
        "A": ["北京航空航天大学", "哈尔滨工业大学", "南京大学", "武汉大学", "华中科技大学"],
        "A-": ["北京理工大学", "东北大学", "上海交通大学", "同济大学", "苏州大学", "中国科学技术大学", "四川大学", "西安电子科技大学"]
    },
    # 电子信息类 / 电子科学
    "电子科学与技术": {
        "A+": ["电子科技大学", "西安电子科技大学"],
        "A": ["北京大学", "清华大学", "东南大学"],
        "A-": ["北京邮电大学", "复旦大学", "上海交通大学", "南京大学", "浙江大学"]
    },
    # 机械类
    "机械工程": {
        "A+": ["清华大学", "哈尔滨工业大学", "华中科技大学", "西安交通大学"],
        "A": ["北京理工大学", "大连理工大学", "浙江大学", "上海交通大学"],
        "A-": ["北京航空航天大学", "吉林大学", "南京航空航天大学", "西南交通大学", "东北大学"]
    },
    # 控制类 / 自动化
    "控制科学与工程": {
        "A+": ["清华大学", "哈尔滨工业大学", "浙江大学"],
        "A": ["北京理工大学", "华中科技大学", "西安交通大学", "国防科技大学", "山东大学"],
        "A-": ["北京航空航天大学", "东北大学", "上海交通大学", "南京航空航天大学"]
    },
    # 法学
    "法学": {
        "A+": ["中国政法大学", "中国人民大学"],
        "A": ["北京大学", "清华大学", "华东政法大学", "武汉大学", "西南政法大学"],
        "A-": ["吉林大学", "大连海事大学", "上海交通大学", "南京大学", "浙江大学", "厦门大学", "中南财经政法大学"]
    },
    # 金融 / 经济学
    "应用经济学": {
        "A+": ["北京大学", "中国人民大学"],
        "A": ["清华大学", "南开大学", "复旦大学", "上海财经大学", "厦门大学"],
        "A-": ["对外经济贸易大学", "东北财经大学", "中南财经政法大学", "西南财经大学"]
    }
}

def seed_academic_data():
    if not DB_PATH.exists():
        logger.error(f"高校数据库文件 {DB_PATH} 不存在！")
        return
        
    with open(DB_PATH, "r", encoding="utf-8") as f:
        unis = json.load(f)
        
    logger.info(f"读取到 {len(unis)} 所高校。开始静态实力指标灌装...")
    
    seeded_unis = []
    for u in unis:
        name = u["name"]
        
        # 1. 灌装行业标签
        tags = []
        for tag_name, member_list in INDUSTRY_TAGS.items():
            if name in member_list:
                tags.append(tag_name)
        u["industry_tags"] = tags
        
        # 2. 灌装学科评估等级
        evals = {}
        for major_name, grades_dict in DISCIPLINE_EVALUATIONS.items():
            for grade, schools in grades_dict.items():
                if name in schools:
                    evals[major_name] = grade
                    break
        u["discipline_evaluations"] = evals
        
        # 3. 按照高校层级分级估算博硕士点数量、就业深造率
        if u.get("is_985"):
            doctorate_points = 48
            master_points = 58
            overall_employment_rate = 96.2
            postgraduate_rate = 48.5
            abroad_rate = 8.5
            key_employers = ["中国航天科工", "国家电网", "中国建筑", "华为", "腾讯", "中国中铁", "字节跳动"]
        elif u.get("is_211") or u.get("is_double_first_class"):
            doctorate_points = 22
            master_points = 38
            overall_employment_rate = 94.5
            postgraduate_rate = 32.0
            abroad_rate = 4.2
            key_employers = ["中国建筑", "中建三局", "国家电网", "华为", "地方建投", "地方国企"]
        else:
            # 普通公办
            if u.get("ownership") == "公办":
                doctorate_points = 4
                master_points = 18
                overall_employment_rate = 90.5
                postgraduate_rate = 14.5
                abroad_rate = 1.0
                key_employers = ["中建集团", "中国铁建", "地方民营企业", "中小型科技公司"]
            # 民办 / 独立学院
            else:
                doctorate_points = 0
                master_points = 0
                overall_employment_rate = 86.0
                postgraduate_rate = 3.5
                abroad_rate = 0.5
                key_employers = ["本地民营企业", "中小型互联网公司", "外包科技服务商"]
                
        u["doctorate_points"] = u.get("doctorate_points", doctorate_points)
        u["master_points"] = u.get("master_points", master_points)
        u["overall_employment_rate"] = u.get("overall_employment_rate", overall_employment_rate)
        u["postgraduate_rate"] = u.get("postgraduate_rate", postgraduate_rate)
        u["abroad_rate"] = u.get("abroad_rate", abroad_rate)
        u["key_employers"] = u.get("key_employers") or key_employers
        
        # 4. 灌装费用细分明细（住宿费与专业浮动学费）
        ownership = u.get("ownership")
        if ownership == "中外合作办学":
            accommodation_fee = 3000
            major_tuition_fees = {"普通专业": 65000, "商科类": 80000, "艺术类": 90000}
        elif ownership == "独立学院":
            accommodation_fee = 1800
            major_tuition_fees = {"普通专业": 26000, "软件工程": 28000, "艺术类": 29000}
        elif ownership == "民办":
            accommodation_fee = 1800
            major_tuition_fees = {"普通专业": 22000, "软件工程": 24000, "艺术类": 25000}
        else:
            # 公办普通本科
            accommodation_fee = 1200
            major_tuition_fees = {
                "普通文科": 4800,
                "普通理科": 5200,
                "普通工科": 5500,
                "医学类": 6200,
                "软件工程(高年级)": 12000,
                "艺术类": 10000
            }
            
        u["accommodation_fee"] = u.get("accommodation_fee", accommodation_fee)
        u["major_tuition_fees"] = u.get("major_tuition_fees") or major_tuition_fees
        u["ownership_type"] = u.get("ownership_type") or u.get("ownership") or "公办"
        
        # 5. 所在城市生活费估算
        loc = u.get("location", "未知")
        if loc in ["北京", "上海", "广东"]:
            avg_living_cost = 2500
            city_level = "一线"
        elif loc in ["江苏", "浙江", "天津", "福建", "四川", "湖北", "陕西"]:
            avg_living_cost = 1800
            city_level = "新一线/二线"
        else:
            avg_living_cost = 1200
            city_level = "三线及以下"
            
        u["avg_living_cost"] = u.get("avg_living_cost", avg_living_cost)
        u["city_level"] = u.get("city_level", city_level)
        
        # 6. 学校简介补充（极简化，用于后续展示）
        if not u.get("description"):
            u["description"] = f"{name}是位于我国{loc}的{u.get('type', '综合')}类大学。学校致力于培养具有创新精神的高水平人才。"
            
        seeded_unis.append(u)
        
    # 写回数据库
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(seeded_unis, f, ensure_ascii=False, indent=2)
        
    logger.info("=" * 60)
    logger.info("🎉 静态学科与行业实力背景数据 Seeding 导入完成！")
    logger.info(f"   已向 {len(seeded_unis)} 所高校写入：学科评估、博硕士点、专业收费明细、住宿费、读研深造率等特征。")
    logger.info("=" * 60)

if __name__ == "__main__":
    seed_academic_data()
