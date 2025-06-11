from typing import Set
from api.config import REGULATORY_DATABASE_SEARCH_ENGINE_URL, DEFAULT_SEARCH_ENGINE_URL
from api.handlers.s3_handler import upload_files_to_s3
from api.page_objects.google_crawler_page import CrawlerPage, can_paginate, extract_urls
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crawler")


async def perform_due_diligence(actor_name, schedule_id: str, pages: int = 3):
    logger.info(
        f"Processing perform_applicable_searches for vendor: {actor_name}, schedule: {schedule_id} for {pages} page(s)")
    logger.info(f"Performing generic google search using English search terms for {actor_name}...")
    search_term = (f'"{actor_name}" AND ("facilitation payment" | litigation | judicial | fine | launder | OFAC | '
                   f'terror | manipulate | counterfeit | traffic | court | appeal | investigate | guilty | illegal | '
                   f'arrest | evasion | sentence | kickback | prison | jail | corruption | corrupt | "grease payment" '
                   f'| crime | bribe | fraud | condemn | accuse | implicate)')
    await google_search_and_download(search_term, pages, f"{schedule_id}/Google")
    logger.info(f"Completed generic google search using English search terms for {actor_name}.")

    logger.info(f"Performing generic google search using Hindi search terms for {actor_name}...")
    hindi_search_term = (f'"{actor_name}" AND (अपराध | रिश्वत | धोखाधड़ी | निंदा | आरोप | शामिल | ग्रेस भुगतान | '
                         f'मुकदमा | न्यायिक | जुर्माना | मनी लॉन्ड्रिंग | आतंकवाद | नकली | तस्करी | कोर्ट | '
                         f'अपील | जांच | दोषी | अवैध | गिरफ्तारी | चोरी | सजा | घूस | जेल | भ्रष्टाचार)')
    await google_search_and_download(hindi_search_term, pages, f"{schedule_id}/Google/hindi")
    logger.info(f"Completed generic google search using Hindi search terms for {actor_name}.")

    logger.info(f"Performing google site search for {actor_name}...")
    await google_site_search_and_download(search_term, pages, f"{schedule_id}/Regulatory Databases")

    logger.info("Uploading files to S3...")
    await upload_files_to_s3(os.environ.get('BUCKET_NAME', "vdd-crawler"), schedule_id)
    logger.info("Upload to S3 complete")

    #os.removedirs(f'/tmp/{schedule_id}')


async def google_search_and_download(
        search_term: str,
        num_of_results_pages_to_scrape: int,
        category: str,
        search_url=DEFAULT_SEARCH_ENGINE_URL):
    logger.info("Beginning default search engine search...")
    dir_path = f'./tmp/{category}'
    os.makedirs(dir_path, exist_ok=True)
    crawler = CrawlerPage(working_folder=dir_path)
    search_page_urls = set()

    try:
        page_number = 1
        search_page = None
        while page_number <= num_of_results_pages_to_scrape:
            if page_number == 1:
                logger.info(f'Using search term: {search_term}')
                search_page = await crawler.perform_google_search(search_term, search_url=search_url)
            elif await can_paginate(search_page):
                logger.info('Navigating to next page...')
                search_page = await crawler.navigate_to_next_page(search_page)
            else:
                break

            search_page_urls.update(await extract_urls(search_page))
            logger.info(f'Found {len(search_page_urls)} URLs')
            page_number += 1
        logger.info(f"Completed performing search against default search engine.")
    except Exception as e:
        logger.error(f'Error occurred: {e}')
    logger.info("Preparing manifest...")
    manifest_map = await create_manifest_for_urls(search_page_urls, category)
    logger.info("Manifest created")
    logger.info("System attempting to create PDF and TXT files out of the extracted URLs, this may take a while...")
    await crawler.prepare_pdfs(manifest_map)
    logger.info("PDF and TXT extraction complete.")

async def google_site_search_and_download(search_term: str, pages, category: str):
    await google_search_and_download(search_term, pages, category, search_url=REGULATORY_DATABASE_SEARCH_ENGINE_URL)


async def create_manifest_for_urls(urls: Set, category: str):
    manifest_file_path = os.path.join('./tmp', category, 'manifest.txt')
    manifest_map = {}
    with open(manifest_file_path, 'w') as manifest_file:
        file_number = 1
        for url in urls:
            manifest_map[url] = f"{file_number}"
            manifest_file.write(f"{file_number} -> {url}\n")
            file_number += 1
    return manifest_map
