import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edu_info.services.major_scraper.engine import MajorScraperEngine
from edu_info.utils.logger import setup_logger

logger = setup_logger("test_engine")

async def main():
    engine = MajorScraperEngine()
    try:
        logger.info("Initializing browser...")
        await engine.init_browser()
        logger.info("Scraping 大连理工大学...")
        majors = await engine.scrape_university("大连理工大学")
        logger.info(f"Found {len(majors)} majors")
        for m in majors[:5]:
            logger.info(m)
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await engine.close()

if __name__ == "__main__":
    asyncio.run(main())
