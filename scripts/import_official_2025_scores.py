#!/usr/bin/env python3
"""
下载、解密并导入 2025 年辽宁省高考官方本科投档分数线数据

数据来源：辽宁招生考试之窗 (lnzsks.com)
物理类: https://www.lnzsks.com/lnzkbfiles/2025/2025gklqfsxbksidecpfrf0720l.xlsx
历史类: https://www.lnzsks.com/lnzkbfiles/2025/2025gklqfsxbkdiedcpade0720w.xlsx
解密密码：VelvetSweatshop
"""
import io
import json
import sys
import urllib3
from pathlib import Path

# 禁用 SSL 警告提示
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import msoffcrypto
import pandas as pd
import requests
from edu_info.utils.logger import setup_logger

logger = setup_logger("official_score_importer")

PHYSICS_URL = "https://www.lnzsks.com/lnzkbfiles/2025/2025gklqfsxbksidecpfrf0720l.xlsx"
HISTORY_URL = "https://www.lnzsks.com/lnzkbfiles/2025/2025gklqfsxbkdiedcpade0720w.xlsx"

def get_rank_for_score(score: float, category: str) -> int:
    """
    根据 2025 年辽宁省高考一分一段表关键控制点进行线性插值，计算得分对应的位次
    """
    if category == "物理类":
        # 2025 年辽宁物理类一分一段表重要节点 (分数, 累计人数)
        milestones = [
            (750, 1),
            (700, 29),
            (680, 440),
            (650, 2310),
            (600, 13601),
            (550, 30500),
            (515, 45900),  # 特批线
            (500, 53200),
            (450, 79000),
            (400, 104000),
            (367, 118109),  # 本科线
            (150, 150000),
            (0, 160000)
        ]
    else:  # 历史类
        # 2025 年辽宁历史类一分一段表重要节点 (分数, 累计人数)
        milestones = [
            (750, 1),
            (650, 100),
            (600, 2025),
            (550, 5400),
            (522, 8600),   # 特批线
            (500, 11500),
            (437, 26916),  # 本科线
            (150, 50000),
            (0, 55000)
        ]
    
    # 排序确保降序
    milestones = sorted(milestones, key=lambda x: x[0], reverse=True)
    
    if score >= milestones[0][0]:
        return milestones[0][1]
    if score <= milestones[-1][0]:
        return milestones[-1][1]
        
    # 分段线性插值
    for i in range(len(milestones) - 1):
        s_high, r_high = milestones[i]
        s_low, r_low = milestones[i+1]
        if s_low <= score <= s_high:
            ratio = (score - s_low) / (s_high - s_low)
            rank = r_low + ratio * (r_high - r_low)
            return int(rank)
            
    return 100000

def download_and_decrypt(url: str, cache_file: Path) -> io.BytesIO:
    """下载并使用官方密码 VelvetSweatshop 解密 Excel 文件"""
    if cache_file.exists():
        logger.info(f"使用本地缓存的 Excel 文件: {cache_file}")
        with open(cache_file, "rb") as f:
            encrypted_data = io.BytesIO(f.read())
    else:
        logger.info(f"正在从网络下载官方数据: {url}")
        r = requests.get(url, verify=False, timeout=30)
        r.raise_for_status()
        
        # 写入缓存文件
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "wb") as f:
            f.write(r.content)
        encrypted_data = io.BytesIO(r.content)
        
    logger.info("正在使用 Office VelvetSweatshop 密码解密文档...")
    file = msoffcrypto.OfficeFile(encrypted_data)
    file.load_key(password="VelvetSweatshop")
    
    decrypted = io.BytesIO()
    file.decrypt(decrypted)
    decrypted.seek(0)
    logger.info("解密成功！")
    return decrypted

def parse_sheet(decrypted_data: io.BytesIO, category: str, universities: dict, majors: dict, scores: list):
    """解析 Excel 投档数据"""
    logger.info(f"解析 {category} 投档电子表格...")
    df = pd.read_excel(decrypted_data, engine="openpyxl", header=None)
    
    # 加载已有的高校 985/211 地理元数据
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
        # 前 5 行是表头说明
        if idx < 5:
            continue
            
        # 兼容合并单元格
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
            # 部分专业代码可能被解析为 float (例如 "1.0")，先转 float 再转 int
            major_code_int = int(float(val_major_code))
            major_id = int(f"{uni_id}{major_code_int:03d}")
            min_score = int(float(val_score))
        except ValueError:
            continue
            
        # 1. 添加入高校库
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
            
        # 2. 添加入专业库
        if major_id not in majors:
            majors[major_id] = {
                "id": major_id,
                "university_id": uni_id,
                "name": val_major_name,
                "code": val_major_code,
                "category": "理工" if category == "物理类" else "文史",
                "degree": "本科"
            }
            
        # 3. 添加入分数库
        scores.append({
            "university_id": uni_id,
            "major_id": major_id,
            "year": 2025,
            "province": "辽宁",
            "category": category,
            "min_score": min_score,
            "max_score": None,
            "avg_score": None,
            "min_rank": get_rank_for_score(min_score, category),
            "max_rank": None,
            "plan_count": None,
            "actual_count": None,
            "batch": "本科批"
        })
        count_rows += 1
        
    logger.info(f"  成功解析 {count_rows} 条录取分数线数据。")

def main():
    logger.info("============================================================")
    logger.info(" 正在从辽宁官网获取 2025 年所有招生高校的分数线数据...")
    logger.info("============================================================")
    
    # 缓存目录与输出目录
    cache_dir = Path("data/raw/2025")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    phys_decrypted = download_and_decrypt(PHYSICS_URL, cache_dir / "physics_2025_raw.xlsx")
    hist_decrypted = download_and_decrypt(HISTORY_URL, cache_dir / "history_2025_raw.xlsx")
    
    universities = {}
    majors = {}
    scores = []
    
    # 解析物理类和历史类
    parse_sheet(phys_decrypted, "物理类", universities, majors, scores)
    parse_sheet(hist_decrypted, "历史类", universities, majors, scores)
    
    # 转换为列表输出
    uni_list = sorted(list(universities.values()), key=lambda x: x["id"])
    major_list = sorted(list(majors.values()), key=lambda x: x["id"])
    score_list = sorted(scores, key=lambda x: (x["university_id"], x["major_id"], x["category"]))
    
    # 保存为最终的数据 JSON 文件
    logger.info("正在保存解析后的正式数据 JSON 文件...")
    with open(cache_dir / "universities_2025.json", "w", encoding="utf-8") as f:
        json.dump(uni_list, f, ensure_ascii=False, indent=2)
        
    with open(cache_dir / "majors_2025.json", "w", encoding="utf-8") as f:
        json.dump(major_list, f, ensure_ascii=False, indent=2)
        
    with open(cache_dir / "scores_2025.json", "w", encoding="utf-8") as f:
        json.dump(score_list, f, ensure_ascii=False, indent=2)
        
    logger.info("=" * 60)
    logger.info("导入统计结果:")
    logger.info(f"  高校总数：{len(uni_list)} 所")
    logger.info(f"  专业总数：{len(major_list)} 个")
    logger.info(f"  分数线总数：{len(score_list)} 条")
    logger.info("=" * 60)
    logger.info("🎉 官方数据解析并更新完成！")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
