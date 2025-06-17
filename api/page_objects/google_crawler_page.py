import fitz
from bs4 import BeautifulSoup
from typing import Dict
from typing import Set
from pyppeteer.errors import PageError, TimeoutError, NetworkError
from pyppeteer_stealth import stealth
from urllib.request import urlopen
from api.config import DEFAULT_SEARCH_ENGINE_URL, PACKETSTREAM_PROXY_URL, PACKETSTREAM_USERNAME, PACKETSTREAM_PASSWORD
from pyppeteer import launch
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

def handle_request(request):
    asyncio.create_task (intercept_request(request))

async def intercept_request (request):
    blocked_resource_types = [
        'beacon',
        'csp_report',
        'font',
        'image',
        'imageset',
        'media',
        'object',
        'texttrack',
        'stylesheet',
    ]
    if request.resourceType in blocked_resource_types:
        logger.info (f'Blocked type: {request.resourceType}, url: {request.url}')
        await request.abort()
    else:
        await request.continue_()


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


async def write_pdf_file(url, file_path):
    try:
        pdf_content = urlopen(url)
        with open(file_path, 'wb') as f:
            f.write(pdf_content.read())
        logger.info(f'Converted page: {url} to PDF {file_path}')
    except Exception as e:
        logger.error(f'Error writing PDF file {file_path}: {e}')


class CrawlerPage:

    def __init__(self):
        self.page_number = None
        self._browser_with_proxy = None
        self._browser = None

    async def get_browser_with_proxy(self):
        if self._browser_with_proxy is None:
            self._browser_with_proxy = await launch({
                'executablePath': '/usr/bin/chromium',
                'headless': True,
                'ignoreHTTPSErrors': True,
                'args': ['--no-sandbox', '--disable-dev-shm-usage', f'--proxy-server={PACKETSTREAM_PROXY_URL}', '--ignore-certificate-errors'],
            })
        return self._browser_with_proxy

    async def new_intercepted_page(self):
        browser = await self.get_browser_with_proxy()
        page = await browser.newPage()
        await page.setRequestInterception(True)
        page.on('request', handle_request)
        await page.authenticate({"username":f"{PACKETSTREAM_USERNAME}", "password":f"{PACKETSTREAM_PASSWORD}"})
        return page

    async def get_browser(self):
        if self._browser is None:
            self._browser = await launch({
                'executablePath': '/usr/bin/chromium',
                'headless': True,
                'ignoreHTTPSErrors': True,
                'args': ['--no-sandbox', '--disable-dev-shm-usage','--ignore-certificate-errors'],
            })
        return self._browser

    async def new_page(self):
        browser = await self.get_browser()
        page = await browser.newPage()
        return page


    async def perform_google_search(self, search_term: str, working_dir, search_url=DEFAULT_SEARCH_ENGINE_URL):
        page = await self.new_intercepted_page()
        await stealth(page)
        try:
            await page.goto(search_url)
            await page.type('input[name="search"]', search_term)
            await page.keyboard.press('Enter')
            await page.waitForSelector('div[id="resInfo-0"]')

            pdf_path = working_dir + '/google_results.pdf'
            await page.pdf(path=pdf_path)
        except TimeoutError as te:
            logger.error(f'Timeout error occurred while performing search: {te}')
            pdf_path = working_dir + '/google_error.pdf'
            await page.pdf(path=pdf_path)
            return None

        self.page_number = 1
        return page

    async def navigate_to_next_page(self, page, working_dir):
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
            pdf_path = working_dir + f'/google_results_{self.page_number}.pdf'
            await page.pdf(path=pdf_path)

            return page
        except TimeoutError as e:
            return page
        except Exception as e:
            logger.error(f'Error navigating to next page: {e}')
            return page

    async def prepare_pdfs(self, urls_manifest: Dict, working_dir):
        for url, file_name in urls_manifest.items():
            file_path = f"{working_dir}/{file_name}.pdf"
            if url.lower().endswith('.pdf'):
                logger.info(f'Downloading PDF: {url} to {file_name}')
                await write_pdf_file(url, file_path)
                logger.info(f'Downloaded PDF: {url} to {file_name}')
            else:
                logger.info(f'Converting page: {url} to PDF {file_name}')
                page = await self.new_page()
                await stealth(page)
                try:
                    await page.goto(url)
                    pdf_path = os.path.join(working_dir, f'{file_name}.pdf')
                    await page.pdf(path=pdf_path)
                    logger.info(f'Converted: {url} to PDF {file_name}.pdf')
                except TimeoutError as e:
                    logger.error('Page either too large or is taking too long to load, skipping')
                except PageError as e:
                    logger.error(f'Page error converting page to PDF: {url}: {e}')
                except NetworkError as e:
                    logger.error(f'Network error converting page to PDF: {url}: {e}')
                finally:
                    await page.close()
            await extract_text_from_pdf(file_path)

    async def convert_to_pdf(self, content, file_name: str):
        page = await self.new_intercepted_page()
        await page.setContent(content)
        await page.content()
        await page.screenshot(options={'path': file_name})
        pdf_path = os.path.join("./tmp", file_name)
        await page.pdf(path=pdf_path, format='A4')
        await page.close()

    async def search_and_download(self, search_term: str,
        num_of_results_pages_to_scrape: int,
        category: str,
        search_url=DEFAULT_SEARCH_ENGINE_URL):

        dir_path = f'./tmp/{category}'
        os.makedirs(dir_path, exist_ok=True)
        search_page_urls = set()

        try:
            page_number = 1
            search_page = None
            while page_number <= num_of_results_pages_to_scrape:
                if page_number == 1:
                    logger.info(f'Using search term: {search_term}')
                    search_page = await self.perform_google_search(search_term, dir_path, search_url=search_url)
                elif await can_paginate(search_page):
                    logger.info('Navigating to next page...')
                    search_page = await self.navigate_to_next_page(search_page, dir_path)
                else:
                    break

                search_page_urls.update(await extract_urls(search_page))
                logger.info(f'Found {len(search_page_urls)} URLs')
                page_number += 1
        except Exception as e:
            logger.error(f'Error occurred: {e}')
        logger.info("Preparing manifest...")
        manifest_map = await create_manifest_for_urls(search_page_urls, category)
        logger.info("Manifest created")
        logger.info("System attempting to create PDF and TXT files out of the extracted URLs, this may take a while...")
        await self.prepare_pdfs(manifest_map, dir_path)
        logger.info("PDF and TXT extraction complete.")

    def __del__(self):
        if self._browser_with_proxy is not None:
            self._browser_with_proxy.close()
        if self._browser is not None:
            self._browser.close()
