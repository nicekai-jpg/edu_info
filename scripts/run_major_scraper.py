#!/usr/bin/env python3
import argparse
import asyncio
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edu_info.services.major_scraper.data_processor import sync_to_db
from edu_info.services.major_scraper.engine import MajorScraperEngine
from edu_info.services.major_scraper.scheduler import ScraperScheduler
from edu_info.utils.logger import setup_logger

logger = setup_logger("major_scraper_cli")

async def run_scraper(limit: int, batch_size: int, db_path: str):
    scheduler = ScraperScheduler(db_path)
    engine = MajorScraperEngine()

    logger.info("Initializing scraper checkpoints...")
    scheduler.init_checkpoints()

    total_processed = 0

    try:
        await engine.init_browser(headless=True)

        while total_processed < limit:
            remaining = limit - total_processed
            current_batch_size = min(batch_size, remaining)

            batch = scheduler.get_next_batch(limit=current_batch_size)
            if not batch:
                logger.info("No more universities to scrape.")
                break

            for uni_id, uni_name, uni_code in batch:
                logger.info(f"Processing [{total_processed + 1}/{limit}]: {uni_name} ({uni_code})")

                try:
                    scheduler.update_status(uni_id, 'running')
                    majors = await engine.scrape_university(uni_name)

                    if majors:
                        sync_to_db(db_path, uni_id, majors)
                        scheduler.update_status(uni_id, 'success')
                        logger.info(f"Successfully processed {uni_name}")
                    else:
                        logger.warning(f"No majors found for {uni_name}")
                        scheduler.update_status(uni_id, 'failed', error_msg="No majors found")

                except Exception as e:
                    logger.error(f"Failed to process {uni_name}: {e}")
                    scheduler.update_status(uni_id, 'failed', error_msg=str(e))

                total_processed += 1

                # 礼貌抓取：每校之间随机休息
                if total_processed < limit:
                    await engine.adaptive_sleep("BATCH_END")

            # 每批结束大休
            logger.info("Batch finished. Resting...")
            await asyncio.sleep(60) # 模拟深度冷却

    finally:
        await engine.close()
        logger.info(f"Scraper finished. Total processed: {total_processed}")

def main():
    parser = argparse.ArgumentParser(description="University Majors Scraper CLI")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of universities to scrape")
    parser.add_argument("--batch-size", type=int, default=3, help="Number of universities per batch")
    parser.add_argument("--db", type=str, default="data/duckdb/edu_planning.db", help="Path to DuckDB database")

    args = parser.parse_args()

    asyncio.run(run_scraper(args.limit, args.batch_size, args.db))

if __name__ == "__main__":
    main()
