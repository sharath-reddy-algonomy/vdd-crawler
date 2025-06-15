from typing import Set
from api.config import REGULATORY_DATABASE_SEARCH_ENGINE_URL, DEFAULT_SEARCH_ENGINE_URL
from api.handlers.s3_handler import upload_files_to_s3
from api.page_objects.google_crawler_page import CrawlerPage, can_paginate, extract_urls
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crawler")


async def perform_due_diligence(actor_name, directors, schedule_id: str, pages: int = 3):
    crawler = CrawlerPage()
    logger.info(
        f"Processing perform_applicable_searches for vendor: {actor_name}, schedule: {schedule_id} for {pages} page(s)")
    logger.info(f"Performing generic google search using English search terms for {actor_name}...")

    search_term = (f'"{actor_name}" AND ("facilitation payment" | litigation | judicial | fine | launder | OFAC | '
                   f'terror | manipulate | counterfeit | traffic | court | appeal | investigate | guilty | illegal | '
                   f'arrest | evasion | sentence | kickback | prison | jail | corruption | corrupt | "grease payment" '
                   f'| crime | bribe | fraud | condemn | accuse | implicate)')
    await crawler.search_and_download(search_term, pages, f"{schedule_id}/Google")
    logger.info(f"Completed generic google search using English search terms for {actor_name}.")

    logger.info(f"Performing generic google search using Hindi search terms for {actor_name}...")
    hindi_search_term = (f'"{actor_name}" AND (अपराध | रिश्वत | धोखाधड़ी | निंदा | आरोप | शामिल | ग्रेस भुगतान | '
                         f'मुकदमा | न्यायिक | जुर्माना | मनी लॉन्ड्रिंग | आतंकवाद | नकली | तस्करी | कोर्ट | '
                         f'अपील | जांच | दोषी | अवैध | गिरफ्तारी | चोरी | सजा | घूस | जेल | भ्रष्टाचार)')
    await crawler.search_and_download(hindi_search_term, pages, f"{schedule_id}/Google/Hindi")
    logger.info(f"Completed generic google search using Hindi search terms for {actor_name}.")

    logger.info(f"Performing google site search for {actor_name}...")
    await google_site_search_and_download(search_term, pages, f"{schedule_id}/Regulatory Databases")

    # Director Due Diligence
    logger.info("Performing due diligence for directors...")
    for director in directors:
        logger.info(f"Performing generic google search using English search terms for {director}")
        search_term = (f'"{director}" & AND ("facilitation payment" | litigation | judicial | fine | launder | OFAC | '
                       f'terror | manipulate | counterfeit | traffic | court | appeal | investigate | guilty | illegal | '
                       f'arrest | evasion | sentence | kickback | prison | jail | corruption | corrupt | "grease payment" '
                       f'| crime | bribe | fraud | condemn | accuse | implicate)')
        await crawler.search_and_download(search_term, pages, f"{schedule_id}/{director}/Google")
        logger.info(f"Completed generic google search using English search terms for {director}.")

        logger.info(f"Performing generic google search using Hindi search terms for {director}...")
        hindi_search_term = (f'"{director}" AND (अपराध | रिश्वत | धोखाधड़ी | निंदा | आरोप | शामिल | ग्रेस भुगतान | '
                             f'मुकदमा | न्यायिक | जुर्माना | मनी लॉन्ड्रिंग | आतंकवाद | नकली | तस्करी | कोर्ट | '
                             f'अपील | जांच | दोषी | अवैध | गिरफ्तारी | चोरी | सजा | घूस | जेल | भ्रष्टाचार)')
        await crawler.search_and_download(hindi_search_term, pages, f"{schedule_id}/{director}/Google/Hindi")

        logger.info(f"Performing google site search for {director}...")
        await google_site_search_and_download(search_term, pages, f"{schedule_id}/{director}/Regulatory Databases")


    logger.info("Uploading files to S3...")
    await upload_files_to_s3(os.environ.get('BUCKET_NAME', "vdd-crawler"), schedule_id)
    logger.info("Upload to S3 complete")

    #os.removedirs(f'/tmp/{schedule_id}')

async def google_site_search_and_download(search_term: str, pages, category: str):
    crawler = CrawlerPage()
    await crawler.search_and_download(search_term, pages, category, search_url=REGULATORY_DATABASE_SEARCH_ENGINE_URL)

