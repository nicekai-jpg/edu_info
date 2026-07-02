import sys
import re
import urllib.parse
import urllib.request
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def crawl_school(school_name: str, moe_code: str):
    logger.info(f"====== 开始为 【{school_name}】 (代码: {moe_code}) 爬取阳光高考官方数据 ======")
    
    # 1. 爬取基础资料 (通过 5 位教育部代码，直接调用 WAP JSON 接口)
    detail_url = f"https://gaokao.chsi.com.cn/wap/gdwz/detail/{moe_code}"
    logger.info(f"正在请求基础资料接口: {detail_url}")
    try:
        req = urllib.request.Request(
            detail_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("flag") and data.get("msg"):
                msg = data["msg"]
                logger.info("🎉 成功获取官方基础资料:")
                logger.info(f"   官网网址 (xxwz): {msg.get('xxwz')}")
                logger.info(f"   招生网址 (zswz): {msg.get('zswz')}")
                logger.info(f"   联系电话 (dh):   {msg.get('dh')}")
                logger.info(f"   微信公众号 (wxmc): {msg.get('wxmc')} (微信号: {msg.get('wxh')})")
                logger.info(f"   官方微博 (wbmc): {msg.get('wbmc')} (网址: {msg.get('wbwz')})")
            else:
                logger.warning("接口返回异常或无数据")
    except Exception as e:
        logger.error(f"请求基础资料失败: {e}")

    # 2. 检索并匹配 schId (用于获取满意度及专业推荐)
    encoded_name = urllib.parse.quote(school_name)
    search_url = f"https://gaokao.chsi.com.cn/sch/search.do?yxmc={encoded_name}"
    logger.info(f"正在请求名称检索接口查找 schId: {search_url}")
    sch_id = None
    try:
        req = urllib.request.Request(
            search_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8")
            # 正则提取所有学校项目 (schId 和学校名)
            # 例如: <div class="sch-item" @click="window.open('/sch/schoolInfo--schId-121.dhtml', '_blank')"> ... <span class="name js-yxk-yxmc">东北大学</span>
            pattern = r'<div class="sch-item"\s+@click="window\.open\(\'/sch/schoolInfo(?:Main)?--schId-(\d+)\.dhtml\', \'_blank\'\)">.*?class="[^"]*js-yxk-yxmc"[^>]*>\s*([^\n<]+)\s*</span>'
            items = re.findall(pattern, html, re.DOTALL)
            
            for item_id, item_name in items:
                clean_name = item_name.strip()
                if clean_name == school_name:
                    sch_id = item_id
                    break
            
            # 如果没找到完全一致的，回退取第一个
            if not sch_id and items:
                sch_id = items[0][0]
                
            if sch_id:
                logger.info(f"🎉 成功查找到其阳光高考内部 schId: {sch_id}")
            else:
                logger.warning("未能在搜索页面找到 schId")
    except Exception as e:
        logger.error(f"检索 schId 失败: {e}")
        
    # 3. 爬取满意度评价 (需要 schId)
    if sch_id:
        appraisal_url = f"https://gaokao.chsi.com.cn/zyk/pub/appraisalinfo/{sch_id}"
        logger.info(f"正在请求满意度评价接口: {appraisal_url}")
        try:
            req = urllib.request.Request(
                appraisal_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                if data.get("flag") and data.get("msg"):
                    msg = data["msg"]
                    logger.info("🎉 成功获取学生满意度与专业推荐:")
                    for app in msg.get("schappraisalinfo", []):
                        logger.info(f"   - {app.get('type')}满意度: {app.get('avgRank')} 分 (投票人数: {app.get('count')}人)")
                    
                    recom_majors = [item.get("zymc") for item in msg.get("zytjcountinfo", [])[:5]]
                    logger.info(f"   - 学生最推荐的前 5 大专业: {', '.join(recom_majors)}")
                else:
                    logger.warning("接口无满意度数据")
        except Exception as e:
            logger.error(f"获取满意度数据失败: {e}")

if __name__ == "__main__":
    name = "大连理工大学"
    code = "10141"
    if len(sys.argv) > 2:
        name = sys.argv[1]
        code = sys.argv[2]
    crawl_school(name, code)
