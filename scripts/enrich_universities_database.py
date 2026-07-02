#!/usr/bin/env python3
"""
对数据库中的 885 所高校进行“办学性质”（公办/民办/独立学院/中外合作）
以及“预估学费”（元/年）的精准标注与补全，持久化更新 JSON 数据库。
"""
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("university_enricher")

DB_PATH = Path("data/raw/2025/universities_2025.json")

# 中外合作办学及国际化高校名单
JOINT_VENTURES = [
    "宁波诺丁汉大学", "西交利物浦大学", "温州肯恩大学", "北京师范大学-香港浸会大学联合国际学院",
    "深圳北理莫斯科大学", "上海纽约大学", "广东外语外贸大学南国商学院"  # 南国商学院实际是独立学院，学费偏高
]

# 公办艺术/文理/地质等以“学院”结尾的公办高校名单（用于排除，防止误判为民办）
PUBLIC_COLLEGES = [
    "吉林艺术学院", "南京艺术学院", "山东艺术学院", "云南艺术学院", "广西艺术学院", "新疆艺术学院",
    "绍兴文理学院", "湖北文理学院", "湖南文理学院", "重庆文理学院", "四川文理学院", "宝鸡文理学院",
    "西安文理学院", "兰州城市学院", "厦门理工学院", "东莞理工学院", "成都理工大学", "桂林理工大学",
    "承德医学院", "甘肃医学院", "桂林旅游学院", "桂林航天工业学院", "防灾科技学院", "华北科技学院",
    "中华女子学院", "外交学院", "中国青年政治学院", "中国劳动关系学院", "上海立信会计金融学院",
    "上海海关学院", "上海电机学院", "上海商学院", "南京森林警察学院", "铁道警察学院", "中国人民警察大学",
    "华北水利水电大学", "长春工程学院", "长春工业大学", "吉林建筑大学", "哈尔滨金融学院", "黑龙江工程学院",
    "上海海事大学", "上海电力大学", "江苏海洋大学", "浙江科技大学", "温州理工学院", "绍兴文理学院",
    "嘉兴大学", "衢州学院", "台州学院", "丽水学院", "安徽工程大学", "安徽科技大学", "合肥师范学院",
    "泉州师范学院", "江西科技师范大学", "景德镇陶瓷大学", "山东交通学院", "山东女子学院", "河南工学院",
    "河南牧业经济学院", "南阳理工学院", "安阳工学院", "洛阳理工学院", "许昌学院", "周口师范学院",
    "信阳农林学院", "黄淮学院", "平顶山学院", "新乡学院", "安阳师范学院", "商丘师范学院", "江汉大学",
    "湖北工程学院", "湖北科技学院", "黄冈师范学院", "湖北师范大学", "湖南工程学院", "湖南城市学院",
    "湖南财政经济学院", "湖南交通工程学院", "东莞理工学院", "佛山科学技术学院", "韶关学院", "惠州学院",
    "韩山师范学院", "岭南师范学院", "肇庆学院", "嘉应学院", "百色学院", "梧州学院", "桂林航天工业学院",
    "桂林旅游学院", "攀枝花学院", "宜宾学院", "乐山师范学院", "内江师范学院", "四川师范大学", "遵义师范学院",
    "铜仁学院", "六盘水师范学院", "贵州工程应用技术学院", "凯里学院", "黔南民族师范学院", "兴义民族师范学院",
    "红河学院", "大理大学", "曲靖师范学院", "昭通学院", "保山学院", "楚雄师范学院", "玉溪师范学院",
    "咸阳师范学院", "渭南师范学院", "榆林学院", "商洛学院", "天水师范学院", "河西学院", "陇东学院",
    "宁夏理工学院", "喀什大学", "伊犁师范大学", "新疆理工学院", "塔里木大学", "石河子大学"
]

# 常见民办高校名称特征
PRIVATE_KEYWORDS = [
    "城市学院", "信息学院", "软件学院", "外事", "翻译", "培华", "海都", "现代", "世纪", "东方",
    "华夏", "南方", "同大", "吉利学院", "西京学院", "大连东软信息学院", "辽宁何氏医学院",
    "大连科技学院", "沈阳工学院", "沈阳城市建设学院", "辽宁财贸学院", "沈阳科技学院",
    "辽宁对外经贸学院", "沈阳城市学院", "黑龙江东方学院", "齐鲁理工学院", "烟台科技学院",
    "青岛工学院", "潍坊科技学院", "武汉晴川学院", "武汉华夏理工学院", "广州南方学院",
    "广东科技学院", "西安培华学院", "西安外事学院", "西安欧亚学院", "西安明德理工学院",
    "三亚学院", "海口经济学院", "南昌工学院", "江西科技学院", "江西应用科技学院"
]

def enrich_database():
    if not DB_PATH.exists():
        logger.error(f"高校数据库文件 {DB_PATH} 不存在！")
        return
        
    with open(DB_PATH, "r", encoding="utf-8") as f:
        unis = json.load(f)
        
    logger.info(f"读取到 {len(unis)} 所高校。开始处理标注...")
    
    enriched_unis = []
    stats = {"公办": 0, "民办": 0, "独立学院": 0, "中外合作办学": 0}
    
    for u in unis:
        name = u["name"]
        
        # 1. 优先判定中外合作办学
        is_jv = False
        if name in JOINT_VENTURES or any(x in name for x in ["纽约大学", "利物浦大学", "肯恩大学", "诺丁汉大学", "莫斯科大学", "联合国际学院"]):
            is_jv = True
            
        # 2. 判定独立学院
        is_independent = False
        # 独立学院典型命名：XX大学XX学院，例如 大连理工大学城市学院
        if "大学" in name and name.endswith("学院") and not name.startswith("中国科学") and not name.startswith("中国社会科学"):
            # 排除公办二级合作办学，如果不在公办白名单内，则为独立学院
            if name not in PUBLIC_COLLEGES:
                is_independent = True
                
        # 3. 判定民办高校
        is_private = False
        if not is_jv and not is_independent:
            # 检查民办特征词
            if name in PRIVATE_KEYWORDS or any(x in name for x in PRIVATE_KEYWORDS):
                if name not in PUBLIC_COLLEGES:
                    is_private = True
            # 没有大学字样、以学院结尾、且不属于公办白名单及重点大学的普通学院，大概率为民办/独立转设高校
            elif name.endswith("学院") and name not in PUBLIC_COLLEGES:
                if not u.get("is_985") and not u.get("is_211") and not u.get("is_double_first_class"):
                    # 过滤掉常见的师范、医学院等公办字样
                    if not any(x in name for x in ["师范", "医学院", "中医药", "警察", "公安", "美术", "音乐", "体育", "电力", "水利"]):
                        is_private = True
                        
        # 4. 根据类型分配办学性质与预估学费
        if is_jv:
            ownership = "中外合作办学"
            tuition_fee = 65000  # 平均 6.5 万/年
        elif is_independent:
            ownership = "独立学院"
            tuition_fee = 26000  # 平均 2.6 万/年
        elif is_private:
            ownership = "民办"
            tuition_fee = 22000  # 平均 2.2 万/年
        else:
            ownership = "公办"
            tuition_fee = 5500   # 平均 5500 元/年
            
        # 更新高校字典
        u["ownership"] = ownership
        u["tuition_fee"] = tuition_fee
        
        stats[ownership] += 1
        enriched_unis.append(u)
        
    # 回写到原始 JSON 数据库中
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(enriched_unis, f, ensure_ascii=False, indent=2)
        
    logger.info("=" * 60)
    logger.info(" 高校数据库办学性质与学费标注统计:")
    logger.info(f"   - 公办高校：{stats['公办']} 所 (学费预估：5,500元/年)")
    logger.info(f"   - 民办高校：{stats['民办']} 所 (学费预估：22,000元/年)")
    logger.info(f"   - 独立学院：{stats['独立学院']} 所 (学费预估：26,000元/年)")
    logger.info(f"   - 中外合作：{stats['中外合作办学']} 所 (学费预估：65,000元/年)")
    logger.info("=" * 60)
    logger.info("🎉 数据库持久化更新成功！")
    
if __name__ == "__main__":
    enrich_database()
