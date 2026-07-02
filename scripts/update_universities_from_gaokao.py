import re
import json
import urllib.parse
import urllib.request
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = Path("data/processed/universities.json")
BACKUP_PATH = Path("data/processed/universities_backup.json")

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

def fetch_html(url: str) -> str | None:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.read().decode("utf-8")
    except Exception:
        return None

def update_single_school(u: dict) -> dict:
    name = u["name"]
    
    # 1. 检索并获取 schId 以及 5 位真实教育部国标代码 (moe_code)
    encoded_name = urllib.parse.quote(name)
    search_url = f"https://gaokao.chsi.com.cn/sch/search.do?yxmc={encoded_name}"
    html = fetch_html(search_url)
    
    sch_id = None
    moe_code = None
    
    if html:
        # 正则提取 schId, 5位国标代码 (从校徽图片文件名中提取，如 10141.jpg), 以及学校名称
        pattern = r'<div class="sch-item"\s+@click="window\.open\(\'/sch/schoolInfo(?:Main)?--schId-(\d+)\.dhtml\', \'_blank\'\)">\s*<img src=\'https://t1\.chei\.com\.cn/common/xh/(\d+)\.jpg\'.*?class="[^"]*js-yxk-yxmc"[^>]*>\s*([^\n<]+)\s*</span>'
        items = re.findall(pattern, html, re.DOTALL)
        for item_id, item_code, item_name in items:
            if item_name.strip() == name:
                sch_id = item_id
                moe_code = item_code
                break
        if not sch_id and items:
            sch_id = items[0][0]
            moe_code = items[0][1]

    # 2. 爬取基础资料 (使用抓取出的 5 位真实代码)
    if moe_code and len(moe_code) == 5:
        detail_url = f"https://gaokao.chsi.com.cn/wap/gdwz/detail/{moe_code}"
        data = fetch_json(detail_url)
        if data and data.get("flag") and data.get("msg"):
            msg = data["msg"]
            u["moe_code"] = moe_code
            u["website_official"] = msg.get("xxwz") or u.get("website_official")
            u["website"] = msg.get("xxwz") or u.get("website")
            u["website_admissions"] = msg.get("zswz") or u.get("website_admissions")
            u["contact_phone"] = msg.get("dh") or u.get("contact_phone")
            if msg.get("ssmc"):
                u["governing_body"] = msg.get("ssmc")
                
    # 3. 爬取满意度及专业推荐
    if sch_id:
        appraisal_url = f"https://gaokao.chsi.com.cn/zyk/pub/appraisalinfo/{sch_id}"
        app_data = fetch_json(appraisal_url)
        if app_data and app_data.get("flag") and app_data.get("msg"):
            msg = app_data["msg"]
            ratings = {}
            for app in msg.get("schappraisalinfo", []):
                t = app.get("type")
                r = app.get("avgRank")
                if t and r is not None:
                    ratings[t] = float(r)
            if ratings:
                u["appraisal_ratings"] = ratings
                
            recom_majors = [item.get("zymc") for item in msg.get("zytjcountinfo", [])[:5]]
            if recom_majors:
                u["top_employers_list"] = recom_majors + u.get("top_employers_list", [])[:2]

    return u

def main():
    if not DB_PATH.exists():
        logger.error(f"数据库文件 {DB_PATH} 不存在！")
        return

    # 备份数据库
    with open(DB_PATH, "r", encoding="utf-8") as f:
        unis = json.load(f)
        
    with open(BACKUP_PATH, "w", encoding="utf-8") as f:
        json.dump(unis, f, ensure_ascii=False, indent=2)
    logger.info(f"已创建数据库备份至: {BACKUP_PATH}")

    logger.info(f"读取到 {len(unis)} 所高校。开始启动多线程抓取...")
    
    updated_unis = []
    success_count = 0
    
    # 采用 ThreadPoolExecutor 进行并发爬取
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(update_single_school, u.copy()): u for u in unis}
        
        for idx, future in enumerate(as_completed(futures), 1):
            try:
                res = future.result()
                updated_unis.append(res)
                if res.get("website_official") or res.get("appraisal_ratings"):
                    success_count += 1
            except Exception as e:
                orig_u = futures[future]
                logger.error(f"爬取 {orig_u['name']} 失败: {e}")
                updated_unis.append(orig_u)
                
            if idx % 50 == 0:
                logger.info(f"进度进度: {idx}/{len(unis)} ({idx/len(unis)*100:.1f}%) ...")

    # 写回数据库
    # 按照ID排序确保数据库稳定性
    updated_unis.sort(key=lambda x: x["id"])
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(updated_unis, f, ensure_ascii=False, indent=2)
        
    logger.info("=" * 60)
    logger.info(f"🎉 阳光高考真实数据同步完成！")
    logger.info(f"   已更新/核对 {len(updated_unis)} 所高校，其中 {success_count} 所成功同步真实字段值。")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
