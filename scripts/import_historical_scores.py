#!/usr/bin/env python3
"""
下载、解密并解析 2022 - 2025 历年辽宁省高考官方本科投档分数线数据
统一打包为 JSON 数据，供内存算法引擎查询历史录取走势。
"""
import io
import json
import re
import sys
import urllib3
import zipfile
from pathlib import Path

# 禁用 SSL 警告提示
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import msoffcrypto
import pandas as pd
import requests
from edu_info.utils.logger import setup_logger

logger = setup_logger("historical_score_importer")

# 数据配置表
YEAR_CONFIGS = {
    "2025": {
        "物理类": "https://www.lnzsks.com/lnzkbfiles/2025/2025gklqfsxbksidecpfrf0720l.xlsx",
        "历史类": "https://www.lnzsks.com/lnzkbfiles/2025/2025gklqfsxbkdiedcpade0720w.xlsx",
    },
    "2024": {
        "物理类": "https://www.lnzsks.com/lnzkbfiles/2024/2024gkbktdxsiexieft02l.zip",
        "历史类": "https://www.lnzsks.com/lnzkbfiles/2024/2024gkbkptdxosiexie01w.zip",
    },
    "2023": {
        "物理类": "https://www.lnzsks.com/lnzkbfiles/2023/2023gkptlfsx0720l.xlsx",
        "历史类": "https://www.lnzsks.com/lnzkbfiles/2023/2023gkptlfsx0720w.xlsx",
    },
    "2022": {
        "物理类": "https://www.lnzsks.com/lnzkbfiles/2022/2022ptlbk0720l01.xlsx",
        "历史类": "https://www.lnzsks.com/lnzkbfiles/2022/2022ptlbk0720w01.xlsx",
    }
}

def get_rank_for_score(score: float, year: int, category: str) -> int:
    """
    根据各年份辽宁一分一段表的重要节点估算位次
    """
    if category == "物理类":
        if year == 2025:
            milestones = [(750, 1), (700, 29), (680, 440), (650, 2310), (600, 13601), (550, 30500), (515, 45900), (500, 53200), (450, 79000), (400, 104000), (367, 118109), (150, 150000), (0, 160000)]
        elif year == 2024:
            milestones = [(750, 1), (700, 50), (680, 350), (650, 2022), (600, 12500), (550, 28000), (500, 40000), (450, 72000), (400, 95000), (360, 115000), (150, 145000), (0, 155000)]
        elif year == 2023:
            milestones = [(750, 1), (700, 40), (680, 300), (650, 1800), (600, 11500), (550, 26000), (494, 40000), (450, 68000), (400, 90000), (360, 115000), (150, 145000), (0, 155000)]
        else:  # 2022
            milestones = [(750, 1), (700, 35), (680, 280), (650, 1700), (600, 11000), (550, 25000), (501, 40000), (450, 67000), (400, 88000), (362, 115000), (150, 145000), (0, 155000)]
    else:  # 历史类
        if year == 2025:
            milestones = [(750, 1), (650, 100), (600, 2025), (550, 5400), (522, 8600), (500, 11500), (437, 26916), (150, 50000), (0, 55000)]
        elif year == 2024:
            milestones = [(750, 1), (650, 120), (600, 2200), (550, 5800), (500, 7500), (450, 18000), (400, 28000), (150, 48000), (0, 52000)]
        elif year == 2023:
            milestones = [(750, 1), (650, 110), (600, 2100), (550, 5600), (490, 8000), (450, 17000), (404, 28000), (150, 48000), (0, 52000)]
        else:  # 2022
            milestones = [(750, 1), (650, 105), (600, 2050), (550, 5500), (500, 8000), (450, 17500), (404, 28000), (150, 48000), (0, 52000)]
            
    milestones = sorted(milestones, key=lambda x: x[0], reverse=True)
    if score >= milestones[0][0]:
        return milestones[0][1]
    if score <= milestones[-1][0]:
        return milestones[-1][1]
        
    for i in range(len(milestones) - 1):
        s_high, r_high = milestones[i]
        s_low, r_low = milestones[i+1]
        if s_low <= score <= s_high:
            ratio = (score - s_low) / (s_high - s_low)
            rank = r_low + ratio * (r_high - r_low)
            return int(rank)
            
    return 100000

def download_and_decrypt(url: str, cache_file: Path) -> io.BytesIO:
    """下载并解密数据，自适应处理 zip 压缩格式和 VelvetSweatshop 加密格式"""
    if cache_file.exists():
        logger.info(f"使用缓存: {cache_file.name}")
        with open(cache_file, "rb") as f:
            raw_data = io.BytesIO(f.read())
    else:
        logger.info(f"下载文件: {url}")
        r = requests.get(url, verify=False, timeout=30)
        r.raise_for_status()
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "wb") as f:
            f.write(r.content)
        raw_data = io.BytesIO(r.content)
        
    # 自适应 ZIP 解压
    if cache_file.suffix == ".zip":
        logger.info("  检测到 ZIP 文件，正在解压...")
        z = zipfile.ZipFile(raw_data)
        inner_file = z.namelist()[0]
        excel_data = io.BytesIO(z.read(inner_file))
    else:
        excel_data = raw_data
        
    # 自适应 Excel 解密
    try:
        file = msoffcrypto.OfficeFile(excel_data)
        file.load_key(password="VelvetSweatshop")
        decrypted = io.BytesIO()
        file.decrypt(decrypted)
        decrypted.seek(0)
        logger.info("  已成功进行 VelvetSweatshop 密码解密。")
        return decrypted
    except msoffcrypto.exceptions.DecryptionError:
        logger.info("  文件未加密，直接读取。")
        excel_data.seek(0)
        return excel_data
    except Exception:
        logger.info("  无需解密，直接读取。")
        excel_data.seek(0)
        return excel_data

def parse_sheet(decrypted_data: io.BytesIO, year: int, category: str, universities: dict, majors: dict, scores: list):
    """解析表格行"""
    df = pd.read_excel(decrypted_data, engine="openpyxl", header=None)
    
    # 985/211 库
    ref_by_name = {}
    ref_path = Path("src/edu_info/data/universities_985_211.json")
    if ref_path.exists():
        with open(ref_path, encoding="utf-8") as f:
            ref_list = json.load(f)
            ref_by_name = {ref["name"]: ref for ref in ref_list}
            
    current_uni_code = None
    current_uni_name = None
    
    count_rows = 0
    for idx, row in df.iterrows():
        if idx < 5:
            continue
            
        val_uni_code = str(row[0]).strip() if not pd.isna(row[0]) else None
        val_uni_name = str(row[1]).strip() if not pd.isna(row[1]) else None
        
        if val_uni_code and val_uni_code != "nan" and val_uni_code != "":
            current_uni_code = val_uni_code
        if val_uni_name and val_uni_name != "nan" and val_uni_name != "":
            current_uni_name = val_uni_name
            
        if not current_uni_code or not current_uni_name:
            continue
            
        val_major_code = str(row[2]).strip() if not pd.isna(row[2]) else None
        val_major_name = str(row[3]).strip() if not pd.isna(row[3]) else None
        val_score = row[4]
        
        if not val_major_code or not val_major_name or pd.isna(val_score):
            continue
            
        try:
            uni_id = int(current_uni_code)
            major_code_int = int(float(val_major_code))
            major_id = int(f"{uni_id}{major_code_int:03d}")
            min_score = int(float(val_score))
        except ValueError:
            continue
            
        # 1. 高校库（全局合并，保留 985/211 属性）
        if uni_id not in universities:
            ref = ref_by_name.get(current_uni_name)
            if ref:
                is_985 = ref.get("is_985", False)
                is_211 = ref.get("is_211", False)
                is_double_first_class = ref.get("is_double_first_class", False)
                location = ref.get("location", "未知")
                uni_type = ref.get("type", "综合")
            else:
                is_985 = False
                is_211 = False
                is_double_first_class = False
                location = "辽宁" if any(x in current_uni_name for x in ["辽宁", "大连", "沈阳"]) else "其他"
                uni_type = "综合"
                if any(x in current_uni_name for x in ["理工", "工业", "工程", "科技"]):
                    uni_type = "理工"
                elif "师范" in current_uni_name:
                    uni_type = "师范"
                elif any(x in current_uni_name for x in ["财经", "商业", "经济", "金融"]):
                    uni_type = "财经"
                elif "医" in current_uni_name:
                    uni_type = "医药"
                    
            universities[uni_id] = {
                "id": uni_id,
                "name": current_uni_name,
                "code": current_uni_code,
                "location": location,
                "type": uni_type,
                "is_985": is_985,
                "is_211": is_211,
                "is_double_first_class": is_double_first_class,
                "project_type": None
            }
            
        # 2. 专业库（全局合并）
        if major_id not in majors:
            majors[major_id] = {
                "id": major_id,
                "university_id": uni_id,
                "name": val_major_name,
                "code": val_major_code,
                "category": "理工" if category == "物理类" else "文史",
                "degree": "本科"
            }
            
        # 3. 分数库
        scores.append({
            "university_id": uni_id,
            "major_id": major_id,
            "year": year,
            "province": "辽宁",
            "category": category,
            "min_score": min_score,
            "max_score": None,
            "avg_score": None,
            "min_rank": get_rank_for_score(min_score, year, category),
            "max_rank": None,
            "plan_count": None,
            "actual_count": None,
            "batch": "本科批"
        })
        count_rows += 1
        
    logger.info(f"  年份 {year} - {category}：成功解析 {count_rows} 条录取分数线数据")

def main():
    logger.info("============================================================")
    logger.info(" 开始爬取与解析 2022 - 2025 历年官方投档数据...")
    logger.info("============================================================")
    
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    universities = {}
    majors = {}
    scores = []
    
    # 循环读取历年配置
    for year_str, cfg in YEAR_CONFIGS.items():
        year = int(year_str)
        year_raw_dir = raw_dir / str(year)
        year_raw_dir.mkdir(parents=True, exist_ok=True)
        
        # 物理类
        phys_ext = ".zip" if "zip" in cfg["物理类"] else ".xlsx"
        phys_dec = download_and_decrypt(cfg["物理类"], year_raw_dir / f"physics_{year}_raw{phys_ext}")
        parse_sheet(phys_dec, year, "物理类", universities, majors, scores)
        
        # 历史类
        hist_ext = ".zip" if "zip" in cfg["历史类"] else ".xlsx"
        hist_dec = download_and_decrypt(cfg["历史类"], year_raw_dir / f"history_{year}_raw{hist_ext}")
        parse_sheet(hist_dec, year, "历史类", universities, majors, scores)
        
    # 格式化输出
    uni_list = sorted(list(universities.values()), key=lambda x: x["id"])
    major_list = sorted(list(majors.values()), key=lambda x: x["id"])
    score_list = sorted(scores, key=lambda x: (x["year"], x["university_id"], x["major_id"], x["category"]))
    
    logger.info("保存整合后的正式 JSON 文件...")
    with open(processed_dir / "universities.json", "w", encoding="utf-8") as f:
        json.dump(uni_list, f, ensure_ascii=False, indent=2)
        
    with open(processed_dir / "majors.json", "w", encoding="utf-8") as f:
        json.dump(major_list, f, ensure_ascii=False, indent=2)
        
    with open(processed_dir / "scores.json", "w", encoding="utf-8") as f:
        json.dump(score_list, f, ensure_ascii=False, indent=2)
        
    # 分年份汇总显示
    logger.info("=" * 60)
    logger.info("导入统计:")
    logger.info(f"  高校总数：{len(uni_list)} 所")
    logger.info(f"  专业总数：{len(major_list)} 个")
    logger.info(f"  分数线总计：{len(score_list)} 条")
    for y in sorted(list(set(x["year"] for x in score_list))):
        y_count = sum(1 for x in score_list if x["year"] == y)
        logger.info(f"    - {y} 年录取分数数据：{y_count} 条")
    logger.info("=" * 60)
    logger.info("🎉 历年投档库历史数据全部更新成功！")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
