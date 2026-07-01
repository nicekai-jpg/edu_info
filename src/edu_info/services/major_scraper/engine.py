import asyncio
import logging
import random
from typing import Any

from playwright.async_api import BrowserContext, Page, async_playwright
from playwright_stealth import Stealth

logger = logging.getLogger(__name__)

class MajorScraperEngine:
    """
    核心爬虫引擎，使用 Playwright + Stealth 模拟真实用户行为。
    """
    def __init__(self):
        self.pw = None
        self.browser = None
        self.context: BrowserContext = None
        self.stealth = Stealth()

    async def init_browser(self, headless: bool = True):
        """
        初始化浏览器，配置随机视口和 Stealth 保护，支持代理设置。
        """
        import os

        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(headless=headless)

        # 随机化视口
        width = random.randint(1280, 1920)
        height = random.randint(720, 1080)

        # 检查代理设置
        proxy_env = os.environ.get("SCRAPER_PROXY")
        proxy_config = None
        if proxy_env:
            proxy_config = {"server": proxy_env}
            logger.info(f"使用代理进行爬取: {proxy_env}")

        self.context = await self.browser.new_context(
            viewport={'width': width, 'height': height},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            proxy=proxy_config
        )
        logger.info(f"浏览器初始化完成，视口大小: {width}x{height}")

    async def adaptive_sleep(self, level: str):
        """
        根据操作类型实现随机延迟。
        """
        delays = {
            "PAGE_LOAD": (2.0, 5.0),
            "PAGE_TURN": (1.5, 3.5),
            "BATCH_END": (5.0, 10.0),
            "ACTION": (0.5, 1.5)
        }
        low, high = delays.get(level, (1.0, 2.0))
        sleep_time = random.uniform(low, high)
        await asyncio.sleep(sleep_time)

    async def _simulate_human_behavior(self, page: Page):
        """
        模拟人类行为：随机滚动。
        """
        for _ in range(random.randint(1, 3)):
            scroll_amount = random.randint(200, 600)
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(random.uniform(0.5, 1.2))

    async def scrape_university(self, uni_name: str) -> list[dict[str, Any]]:
        """
        爬取指定高校的专业信息。
        """
        if not self.context:
            await self.init_browser()

        page = await self.context.new_page()
        await self.stealth.apply_stealth_async(page)

        majors = []
        try:
            # 1. 导航到搜索页
            logger.info(f"正在搜索高校: {uni_name}")
            await page.goto("https://gaokao.chsi.com.cn/sch/search.do", wait_until="networkidle")
            await self.adaptive_sleep("PAGE_LOAD")

            # 2. 填充搜索框并提交
            await page.fill('input[name="yxmc"]', uni_name)
            await self.adaptive_sleep("ACTION")
            await page.click('input[value="查询"]')
            await page.wait_for_load_state("networkidle")

            # 3. 点击进入高校详情页
            school_link = await page.query_selector(f'a:has-text("{uni_name}")')
            if not school_link:
                # 备选选择器
                school_link = await page.query_selector('td.js-yxmc a') or await page.query_selector('table.ch-table td a')

            if not school_link:
                logger.error(f"未找到高校 '{uni_name}' 的链接")
                return []

            await school_link.click()
            await page.wait_for_load_state("networkidle")
            await self.adaptive_sleep("PAGE_LOAD")

            # 4. 切换到“开设专业”标签
            # 详情页可能在二级路径，找到含有“开设专业”文本的链接
            majors_tab = page.get_by_role("link", name="开设专业").first
            if not majors_tab:
                logger.error(f"未找到 '{uni_name}' 的 '开设专业' 标签")
                return []

            await majors_tab.click()
            await page.wait_for_load_state("networkidle")
            await self.adaptive_sleep("PAGE_LOAD")

            # 5. 循环解析专业表格（处理分页）
            while True:
                await self._simulate_human_behavior(page)

                rows = await page.query_selector_all('table.ch-table tr')
                # 跳过表头
                for row in rows[1:]:
                    cols = await row.query_selector_all('td')
                    if len(cols) >= 5:
                        major_data = {
                            "name": (await cols[0].inner_text()).strip(),
                            "category": (await cols[1].inner_text()).strip(),
                            "major_class": (await cols[2].inner_text()).strip(),
                            "duration": (await cols[3].inner_text()).strip(),
                            "degree": (await cols[4].inner_text()).strip(),
                        }
                        majors.append(major_data)

                # 查找下一页链接
                next_page = await page.query_selector('li.lip-next:not(.lip-disabled) a')
                if next_page:
                    logger.info(f"正在翻页... 当前已采集 {len(majors)} 个专业")
                    await next_page.click()
                    await page.wait_for_load_state("networkidle")
                    await self.adaptive_sleep("PAGE_TURN")
                else:
                    break

            logger.info(f"完成采集: {uni_name}, 总计 {len(majors)} 个专业")

        except Exception as e:
            logger.error(f"爬取高校 {uni_name} 时发生错误: {e}", exc_info=True)
        finally:
            await page.close()

        return majors

    async def close(self):
        """
        关闭浏览器资源。
        """
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()
