from abc import ABC, abstractmethod
from crawler_default import  google_search_and_download
from api.config import REGULATORY_DATABASE_SEARCH_ENGINE_URL, DEFAULT_SEARCH_ENGINE_URL, NEWS_SEARCH_ENGINE_URL

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crawler")


def get_search_term(actor_name) -> str:
    return (
        f'"{actor_name}" & AND ("facilitation payment" | litigation | judicial | fine | launder | OFAC | '
        f'terror | manipulate | counterfeit | traffic | court | appeal | investigate | guilty | illegal | '
        f'arrest | evasion | sentence | kickback | prison | jail | corruption | corrupt | "grease payment" '
        f'| crime | bribe | fraud | condemn | accuse | implicate)')


def get_hindi_search_term(actor_name):
    return (f'"{actor_name}" AND (अपराध | रिश्वत | धोखाधड़ी | निंदा | आरोप | शामिल | ग्रेस भुगतान | '
     f'मुकदमा | न्यायिक | जुर्माना | मनी लॉन्ड्रिंग | आतंकवाद | नकली | तस्करी | कोर्ट | '
     f'अपील | जांच | दोषी | अवैध | गिरफ्तारी | चोरी | सजा | घूस | जेल | भ्रष्टाचार)')


class BaseCrawler(ABC):
    @abstractmethod
    def get_search_engine_url (self) -> str|None:
        pass

    @abstractmethod
    async def crawl (self, actor_name, directors, schedule_id, pages, site_url: None):
        pass

    @abstractmethod
    def get_category (self) -> str:
        pass

class GoogleCrawler(BaseCrawler):
    def get_category(self) -> str:
        return "Google"

    def get_search_engine_url(self) -> str:
        return DEFAULT_SEARCH_ENGINE_URL

    async def crawl (self, actor_name, directors, schedule_id, pages, site_url: None):
        logger.info(f"Performing generic google search using English search terms for {actor_name}...")
        search_term = get_search_term(actor_name)
        await google_search_and_download(search_term, pages, f"{schedule_id}/{self.get_category()}", search_url=self.get_search_engine_url())
        logger.info(f"Completed generic google search using English search terms for {actor_name}.")

        logger.info(f"Performing generic google search using Hindi search terms for {actor_name}...")
        hindi_search_term = get_hindi_search_term(actor_name)
        await google_search_and_download(hindi_search_term, pages, f"{schedule_id}/{self.get_category()}/Hindi", search_url=self.get_search_engine_url())
        logger.info(f"Completed generic google search using Hindi search terms for {actor_name}.")

class NewsCrawler(GoogleCrawler):
    def get_search_engine_url(self) -> str:
        return NEWS_SEARCH_ENGINE_URL

    def get_category(self) -> str:
        return "News"

class RegulatoryDatabaseCrawler(GoogleCrawler):
    def get_search_engine_url(self) -> str:
        return REGULATORY_DATABASE_SEARCH_ENGINE_URL

    def get_category(self) -> str:
        return "Regulatory Databases"

class OfficialWebsiteCrawler(BaseCrawler):

    def get_search_engine_url(self) -> str:
        return DEFAULT_SEARCH_ENGINE_URL

    def get_category(self) -> str:
        return "OfficialWebsite"

    async def crawl(self, actor_name, directors, schedule_id, pages, site_url: None):
        logger.info(f"Performing official website search for {actor_name} on site {site_url}...")
        search_term = f'{site_url}:"{actor_name}" & AND ("facilitation payment" | litigation | judicial | fine | launder | OFAC | '
        f'terror | manipulate | counterfeit | traffic | court | appeal | investigate | guilty | illegal | '
        f'arrest | evasion | sentence | kickback | prison | jail | corruption | corrupt | "grease payment" '
        f'| crime | bribe | fraud | condemn | accuse | implicate)'
        await google_search_and_download(search_term, pages, f"{schedule_id}/{self.get_category()}",
                                         search_url=self.get_search_engine_url())
        logger.info("Completed official website search")
        pass

