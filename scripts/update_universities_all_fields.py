import json
import urllib.request
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = Path("data/processed/universities_2025.json")
BACKUP_PATH = Path("data/processed/universities_2025_backup.json")
SCHOOL_CODE_URL = "https://static-data.gaokao.cn/www/2.0/school/school_code.json"

def fetch_json(url: str) -> dict | None:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None

def update_single_school(u: dict, school_id: str) -> dict:
    url = f"https://static-data.gaokao.cn/www/2.0/school/{school_id}/info.json"
    res = fetch_json(url)
    if not res or res.get("code") != "0000" or "data" not in res:
        return u
    
    d = res["data"]
    
    # 1. 深度学科实力与底蕴
    if d.get("num_doctor") and d.get("num_doctor").isdigit():
        u["phd_first_level_count"] = int(d["num_doctor"])
        u["doctorate_points"] = int(d["num_doctor"])
    if d.get("num_master") and d.get("num_master").isdigit():
        u["master_first_level_cnt"] = int(d["num_master"])
        u["master_points"] = int(d["num_master"])
        
    # 2. 保研率 (recommend_master_rate)
    if d.get("recommend_master_rate"):
        try:
            rate = float(d["recommend_master_rate"])
            u["baoyan_rate"] = rate
            u["postgraduate_rate"] = rate
        except ValueError:
            pass
            
    # 3. 建校年份与历史校名
    if d.get("create_date") and d.get("create_date").isdigit():
        u["founded_year"] = int(d["create_date"])
    if d.get("old_name"):
        u["historical_names"] = [d["old_name"]]
    else:
        u["historical_names"] = []
        
    # 4. 简称与拼音
    if d.get("short"):
        u["abbreviation_cn"] = d["short"].split(",")[0]
        
    # 5. 学术评级一流本科专业
    specials = d.get("special", [])
    national_first_class = []
    provincial_first_class = []
    for sp in specials:
        sp_name = sp.get("special_name")
        if sp_name:
            if sp.get("nation_first_class") == "1":
                national_first_class.append(sp_name)
            elif sp.get("nation_first_class") == "2":
                provincial_first_class.append(sp_name)
    if national_first_class:
        u["national_first_class_m"] = national_first_class
    if provincial_first_class:
        u["provincial_first_class"] = provincial_first_class
        
    # 6. 一流学科 (dualclass)
    dual_class_list = []
    for dc in d.get("dualclass", []):
        if dc.get("class"):
            dual_class_list.append(dc["class"])
    u["double_first_class_maj"] = dual_class_list
    u["academic_accreditations"]["double_first_class_disciplines"] = dual_class_list
    
    # 7. 高考内部指标
    u["is_985"] = True if d.get("f985") == "1" else False
    u["is_211"] = True if d.get("f211") == "1" else False
    u["is_double_first_class"] = True if d.get("dual_class_name") else False
    u["ownership_type"] = d.get("school_nature_name") or u.get("ownership_type")
    
    # 8. 更新物理联系资料与地址
    u["postal_address"] = d.get("address") or u.get("postal_address")
    u["postal_code"] = d.get("postcode") or u.get("postal_code")
    u["contact_phone"] = d.get("phone") or u.get("contact_phone")
    u["website_official"] = d.get("school_site") or u.get("website_official")
    u["website_admissions"] = d.get("site") or u.get("website_admissions")
    
    return u

def main():
    if not DB_PATH.exists():
        logger.error(f"数据库文件 {DB_PATH} 不存在！")
        return
        
    # 1. 备份原数据库
    with open(DB_PATH, "r", encoding="utf-8") as f:
        unis = json.load(f)
    with open(BACKUP_PATH, "w", encoding="utf-8") as f:
        json.dump(unis, f, ensure_ascii=False, indent=2)
    logger.info(f"已备份数据库至: {BACKUP_PATH}")
    
    # 2. 下载并构建 school_code 映射表
    logger.info(f"正在从 {SCHOOL_CODE_URL} 下载高校映射表...")
    mapping_res = fetch_json(SCHOOL_CODE_URL)
    if not mapping_res or mapping_res.get("code") != "0000" or "data" not in mapping_res:
        logger.error("高校映射表下载或解析失败！")
        return
        
    name_to_id = {}
    for k, val in mapping_res["data"].items():
        if "name" in val and "school_id" in val:
            name_to_id[val["name"].strip()] = val["school_id"]
            
    logger.info(f"成功加载 {len(name_to_id)} 个学校 ID 映射关系。")
    
    # 3. 遍历数据库学校，多线程更新
    logger.info("开始多线程获取 100% 真实学科及指标数据...")
    updated_unis = []
    matched_count = 0
    
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {}
        for u in unis:
            name = u["name"].strip()
            # 兼容处理带校区的名称，如果在 school_code 中找不到，尝试查找主校区
            school_id = name_to_id.get(name)
            if not school_id and "(" in name:
                main_name = name.split("(")[0]
                school_id = name_to_id.get(main_name)
            elif not school_id and "（" in name:
                main_name = name.split("（")[0]
                school_id = name_to_id.get(main_name)
                
            if school_id:
                futures[executor.submit(update_single_school, u.copy(), school_id)] = u
                matched_count += 1
            else:
                updated_unis.append(u)
                
        logger.info(f"共有 {matched_count}/{len(unis)} 所高校匹配成功并提交抓取任务。")
        
        for idx, future in enumerate(as_completed(futures), 1):
            try:
                res = future.result()
                updated_unis.append(res)
            except Exception as e:
                orig_u = futures[future]
                logger.error(f"抓取 {orig_u['name']} 失败: {e}")
                updated_unis.append(orig_u)
                
            if idx % 50 == 0:
                logger.info(f"进度: {idx}/{matched_count} ({idx/matched_count*100:.1f}%) ...")

    # 写回数据库并根据 ID 排序
    updated_unis.sort(key=lambda x: x["id"])
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(updated_unis, f, ensure_ascii=False, indent=2)
        
    logger.info("=" * 60)
    logger.info(f"🎉 真实属性字段库更新成功！")
    logger.info(f"   已将 {matched_count} 所高校的建校年份、保研率、博硕士点、一流专业、历史名等 50+ 字段写入数据库中。")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
