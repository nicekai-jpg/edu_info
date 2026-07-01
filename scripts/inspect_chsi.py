
import asyncio

from playwright.async_api import async_playwright
from playwright_stealth import stealth


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await stealth(page)

        print("Navigating to search page...")
        await page.goto("https://gaokao.chsi.com.cn/sch/search.do", wait_until="networkidle")

        # Take a screenshot to debug if needed
        # await page.screenshot(path="search_page.png")

        # Check for search input
        search_input = await page.query_selector('input[name="yxmc"]')
        if search_input:
            print("Found search input 'yxmc'")
        else:
            inputs = await page.query_selector_all('input')
            for inp in inputs:
                name = await inp.get_attribute('name')
                id = await inp.get_attribute('id')
                print(f"Input: name={name}, id={id}")

        await page.fill('input[name="yxmc"]', "大连理工大学")
        await page.click('input[value="查询"]')

        await page.wait_for_load_state("networkidle")
        print("Search submitted.")

        # Find school link
        school_link = await page.query_selector('td.js-yxmc a')
        if not school_link:
             # Try generic table selector
             school_link = await page.query_selector('table.ch-table td a')

        if school_link:
            href = await school_link.get_attribute('href')
            print(f"Found school link: {href}")
            await school_link.click()
            await page.wait_for_load_state("networkidle")

            # Now look for "开设专业" tab
            # It's usually a link with text "开设专业"
            majors_tab = await page.get_by_role("link", name="开设专业").first
            if majors_tab:
                print("Found '开设专业' tab")
                await majors_tab.click()
                await page.wait_for_load_state("networkidle")

                # Check table structure
                table = await page.query_selector('table.ch-table')
                if table:
                    print("Found majors table")
                    headers = await table.query_selector_all('th')
                    header_texts = [await h.inner_text() for h in headers]
                    print(f"Table headers: {header_texts}")
            else:
                print("Could not find '开设专业' tab")
        else:
            print("Could not find school link")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
