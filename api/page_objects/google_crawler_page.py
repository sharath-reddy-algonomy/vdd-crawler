import fitz
from bs4 import BeautifulSoup
from typing import Dict
from typing import Set
from pyppeteer.errors import PageError, TimeoutError, NetworkError
from pyppeteer_stealth import stealth
from urllib.request import urlopen
from api.config import DEFAULT_SEARCH_ENGINE_URL, REGULATORY_DATABASE_SEARCH_ENGINE_URL
import os
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crawler")


async def extract_urls(page) -> Set[str]:
    try:
        await page.waitForSelector('body')
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        list_anchors = []
        for anchor in soup.find_all("a", {'class': 'gs-title'}, href=True):
            list_anchors.append(anchor['href'])

        return set(list_anchors)
    except Exception as e:
        logger.error(f'Error extracting URLs: {e}')
        return set()


async def can_paginate(page):
    ele = await page.xpath('//div[@class="gsc-cursor"]')
    return len(ele) != 0


async def has_results(page):
    ele = await page.querySelector('div[id="resInfo-0"]')
    result = await page.evaluate('(element) => element.textContent', ele)
    return len(result.strip()) != 0


async def extract_text_from_pdf(pdf_path: str):
    try:
        doc = fitz.open(pdf_path)
        text_file_path = os.path.splitext(pdf_path)[0] + '.txt'
        with open(text_file_path, 'w') as text_file:
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text_file.write(page.get_text())
        logger.info(f"Text extracted and saved to {text_file_path}")
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")


async def _retry_navigation(page, url, retries=3, timeout=300000):
    for attempt in range(retries):
        try:
            await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': timeout})
            await page.waitForSelector('body')
            return
        except TimeoutError as e:
            if attempt == retries - 1:
                raise e
            logger.error(f'Timeout loading {url}.Retrying...Attempt{attempt + 1}')
        except PageError as e:
            if attempt == retries - 1:
                raise e
            logger.error(f'Network Error loading {url}.Retrying...Attempt{attempt + 1}')


class CrawlerPage:

    def __init__(self, browser, working_folder):
        self.page_number = None
        self.browser = browser
        self.working_folder = working_folder
        os.makedirs(self.working_folder, exist_ok=True)

    async def perform_google_search(self, search_term: str, search_url=DEFAULT_SEARCH_ENGINE_URL):
        page = await self.browser.newPage()
        await stealth(page)
        try:
            await page.goto(DEFAULT_SEARCH_ENGINE_URL)
            await page.type('input[name="search"]', search_term)
            await page.keyboard.press('Enter')
            await page.waitForSelector('div[id="resInfo-0"]')

            pdf_path = self.working_folder + '/google_results.pdf'
            await page.pdf(path=pdf_path)
        except TimeoutError as te:
            logger.error(f'Timeout error occurred while performing search: {te}')
            return None

        self.page_number = 1
        return page

    async def google_site_search(self, search_term: str):
        page = await self.browser.newPage()
        await stealth(page)
        await page.goto(REGULATORY_DATABASE_SEARCH_ENGINE_URL)
        await page.type('input[name="search"]', search_term)
        await page.keyboard.press('Enter')
        return page

    async def navigate_to_next_page(self, page):
        try:
            self.page_number += 1
            logger.info(f'Navigating to page {self.page_number}')
            page_selector = f'div[aria-label="Page {self.page_number}"]'
            page_selector_to_check = f'div[aria-label="Page {self.page_number - 1}"]'
            await asyncio.gather(
                page.waitForNavigation(),
                page.click(page_selector),
            )
            await page.waitForSelector(page_selector_to_check)
            pdf_path = self.working_folder + f'/google_results_{self.page_number}.pdf'
            await page.pdf(path=pdf_path)

            return page
        except TimeoutError as e:
            return page
        except Exception as e:
            logger.error(f'Error navigating to next page: {e}')
            return page

    async def write_pdf_file(self, url, file_name):
        file_path = f'{self.working_folder}/{file_name}'
        try:
            pdf_content = urlopen(url)
            with open(file_path, 'wb') as f:
                f.write(pdf_content.read())
            logger.info(f'Converted page: {url} to PDF {file_name}')
        except Exception as e:
            logger.error(f'Error writing PDF file {file_name}: {e}')

    async def prepare_pdfs(self, urls_manifest: Dict):
        for url, file_name in urls_manifest.items():
            if url.lower().endswith('.pdf'):
                logger.info(f'Downloading PDF: {url} to {file_name}')
                await self.write_pdf_file(url, file_name)
                logger.info(f'Downloaded PDF: {url} to {file_name}')
            else:
                logger.info(f'Converting page: {url} to PDF {file_name}')
                page = await self.browser.newPage()
                await stealth(page)
                try:
                    await page.goto(url)
                    pdf_path = os.path.join(self.working_folder, file_name)
                    await page.pdf(path=pdf_path)
                    logger.info(f'Converted: {url} to PDF {file_name}')
                except TimeoutError as e:
                    logger.error('Page either too large or is taking too long to load, skipping')
                except PageError as e:
                    logger.error(f'Page error converting page to PDF: {url}: {e}')
                except NetworkError as e:
                    logger.error(f'Network error converting page to PDF: {url}: {e}')
                finally:
                    await page.close()
            await extract_text_from_pdf(f'{self.working_folder}/{file_name}')

    async def convert_to_pdf(self, content, file_name: str):
        page = await self.browser.newPage()
        await page.setContent(content)
        await page.content()
        await page.screenshot(options={'path': file_name})
        pdf_path = os.path.join("./tmp", file_name)
        await page.pdf(path=pdf_path, format='A4')
        await page.close()

    async def close(self):
        await self.browser.close()
