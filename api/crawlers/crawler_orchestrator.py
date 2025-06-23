import shutil

from api.handlers.s3_handler import upload_files_to_s3
from api.crawlers.Crawlers import CRAWLER_REGISTRY, BaseCrawler
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crawler")


async def perform_due_diligence_v2(json_payload):
    vendor_name = json_payload["vendor_name"]
    schedule_id = json_payload["schedule_id"]
    pages = json_payload["pages"]
    directors = json_payload["directors"]
    website_url = json_payload["website_url"]
    crawlers = json_payload["crawlers"]

    for crawler_requested in crawlers:
        crawler: BaseCrawler | None = CRAWLER_REGISTRY.get(crawler_requested.lower())
        beautified_crawler_requested = crawler_requested.lower().replace("_", " ")
        if crawler is not None:
            logger.info(f"Search Engine: {crawler.get_search_engine_url()}")
            if crawler.get_search_engine_url() is None:
                logger.error(f"Search engine for {crawler.get_category()} not set, skipping this crawler.")
                continue
            logger.info (f"Starting {beautified_crawler_requested} search for schedule {schedule_id}...")
            logger.info(f"Using {vendor_name}, {website_url}...")
            await crawler.crawl(vendor_name, directors, schedule_id, pages, website_url)
            logger.info(f"Completed {beautified_crawler_requested} search for schedule {schedule_id}.")
        else:
            logger.error(f"Crawler requested isn't supported: {crawler_requested}")

    logger.info("Uploading files to S3...")
    await upload_files_to_s3(os.environ.get('BUCKET_NAME', "vdd-crawler"), schedule_id)
    logger.info("Upload to S3 complete")
    #logger.info("Cleaning up local file system")
    #shutil.rmtree(f"./tmp/{schedule_id}", onexc=handle_cleanup_exception)
    #Test after demo
    #logger.info(f"All done for {schedule_id}.")



