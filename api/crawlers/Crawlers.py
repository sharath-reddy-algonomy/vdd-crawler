from abc import ABC, abstractmethod
from api.page_objects.google_crawler_page import CrawlerPage
from api.config import REGULATORY_DATABASE_SEARCH_ENGINE_URL, DEFAULT_SEARCH_ENGINE_URL, NEWS_SEARCH_ENGINE_URL

import logging

logger = logging.getLogger('crawlers')


def get_search_term(actor_name) -> str:
    return (
        f'-filetype:csv -filetype:xls -filetype:xlsx "{actor_name}" ("facilitation payment" | litigation | judicial | fine | launder | OFAC | '
        f'terror | manipulate | counterfeit | traffic | court | appeal | investigate | guilty | illegal | '
        f'arrest | evasion | sentence | kickback | prison | jail | corruption | corrupt | "grease payment" '
        f'| crime | bribe | fraud | condemn | accuse | implicate)')


def get_hindi_search_term(actor_name):
    return (f'-filetype:csv -filetype:xls -filetype:xlsx "{actor_name}" (अपराध | रिश्वत | धोखाधड़ी | निंदा | आरोप | शामिल | ग्रेस भुगतान | '
            f'मुकदमा | न्यायिक | जुर्माना | मनी लॉन्ड्रिंग | आतंकवाद | नकली | तस्करी | कोर्ट | '
            f'अपील | जांच | दोषी | अवैध | गिरफ्तारी | चोरी | सजा | घूस | जेल | भ्रष्टाचार)')


class BaseCrawler(ABC):
    @abstractmethod
    def get_search_engine_url(self) -> str | None:
        pass

    @abstractmethod
    async def crawl(self, actor_name, directors, schedule_id, pages, site_url: None):
        pass

    @abstractmethod
    def get_category(self) -> str:
        pass
    @abstractmethod
    def should_crawl_for_director(self):
        pass


class GoogleCrawler(BaseCrawler):
    def get_category(self) -> str:
        return "Google"

    def get_search_engine_url(self) -> str:
        return DEFAULT_SEARCH_ENGINE_URL

    def should_crawl_for_director(self):
        return True

    async def crawl(self, actor_name, directors, schedule_id, pages, site_url: None):
        google_page = CrawlerPage()
        logger.info(f"Performing search using English search terms for {actor_name}...")
        search_term = get_search_term(actor_name)
        await google_page.search_and_download(search_term, pages, f"{schedule_id}/{self.get_category()}",
                                              search_url=self.get_search_engine_url())
        logger.info(f"Completed search using English search terms for {actor_name}.")

        logger.info(f"Performing search using Hindi search terms for {actor_name}...")
        hindi_search_term = get_hindi_search_term(actor_name)
        await google_page.search_and_download(hindi_search_term, pages, f"{schedule_id}/{self.get_category()}/Hindi",
                                              search_url=self.get_search_engine_url())
        logger.info(f"Completed search using Hindi search terms for {actor_name}.")

        if self.should_crawl_for_director():
            for director in directors:
                logger.info(f"Performing search using English search terms for director {director}...")
                director_search_term = get_search_term(director)
                await (google_page.search_and_download(director_search_term,
                                                       pages,
                                                       f"{schedule_id}/{self.get_category()}/Directors/{director}",
                                                       search_url=self.get_search_engine_url()))
                logger.info(f"Completed search using English search terms for director {director}.")

                logger.info(f"Performing search using Hindi search terms for director {director}...")
                director_hindi_search_term = get_hindi_search_term(director)
                await google_page.search_and_download(director_hindi_search_term,
                                                      pages,
                                                      f"{schedule_id}/{self.get_category()}/Directors/{director}/Hindi",
                                                      search_url=self.get_search_engine_url())
                logger.info(f"Completed search using Hindi search terms for director {director}.")


class NewsCrawler(GoogleCrawler):
    def get_search_engine_url(self) -> str:
        return NEWS_SEARCH_ENGINE_URL

    def get_category(self) -> str:
        return "News"

    def should_crawl_for_director(self):
        return False


class RegulatoryDatabaseCrawler(GoogleCrawler):
    def get_search_engine_url(self) -> str:
        return REGULATORY_DATABASE_SEARCH_ENGINE_URL

    def get_category(self) -> str:
        return "Regulatory Databases"

    def should_crawl_for_director(self):
        return False

    def strip_vendor_business_suffix(self, vendor_name):
        suffixes_to_remove = [" limited", " ltd", " pvt", " private"]
        cleaned_name = vendor_name.lower()
        for suffix in suffixes_to_remove:
            cleaned_name = cleaned_name.replace(suffix, "")
        return cleaned_name.strip()

    async def crawl(self, actor_name, directors, schedule_id, pages, site_url: None):
        google_page = CrawlerPage()
        stripped_vendor_name = self.strip_vendor_business_suffix(actor_name)
        logger.info(f"Performing BSE Search for {actor_name}...")
        search_term = f'-filetype:pdf -filetype:xls -filetype:xlsx site:https://www.bseindia.com/ "{stripped_vendor_name}"'
        await google_page.search_and_download(search_term, pages, f"{schedule_id}/{self.get_category()}/BSE",
                                              search_url=self.get_search_engine_url(), use_proxy=False)

        logger.info(f"Performing NSE Search for {actor_name}...")
        search_term = f'-filetype:pdf -filetype:xls -filetype:xlsx site:https://www.nseindia.com/ "{stripped_vendor_name}"'
        await google_page.search_and_download(search_term, pages, f"{schedule_id}/{self.get_category()}/NSE",
                                              search_url=self.get_search_engine_url(), use_proxy=False)

        await super().crawl(actor_name, directors, schedule_id, pages, site_url)





class OfficialWebsiteCrawler(BaseCrawler):

    def get_search_engine_url(self) -> str:
        return DEFAULT_SEARCH_ENGINE_URL

    def get_category(self) -> str:
        return "OfficialWebsite"

    def should_crawl_for_director(self):
        return False

    async def crawl(self, actor_name, directors, schedule_id, pages, site_url: None):
        if not site_url:
            logger.info('Website URL not specified, skipping official website search.')
            return
        google_page = CrawlerPage()
        logger.info(f"Performing official website search for {actor_name} on site {site_url}...")
        search_term = f'site:{site_url} "{actor_name}" ("facilitation payment" | litigation | judicial | fine | launder | OFAC | '
        f'terror | manipulate | counterfeit | traffic | court | appeal | investigate | guilty | illegal | '
        f'arrest | evasion | sentence | kickback | prison | jail | corruption | corrupt | "grease payment" '
        f'| crime | bribe | fraud | condemn | accuse | implicate)'
        await google_page.search_and_download(search_term, pages, f"{schedule_id}/{self.get_category()}",
                                              search_url=self.get_search_engine_url())
        logger.info("Completed official website search")


CRAWLER_REGISTRY: dict[str, BaseCrawler] = dict(google=GoogleCrawler(), news=NewsCrawler(), regulatory_databases=RegulatoryDatabaseCrawler(),
                        official_website=OfficialWebsiteCrawler())
