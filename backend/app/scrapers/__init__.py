from typing import Dict
from .base import BaseScraper
from .itssa import ItssaScraper
from .ddanzi import DdanziScraper
from .bobaedream import BobaedreamScraper
from .theqoo import TheqooScraper
from .fmkorea import FmkoreaScraper
from .damoang import DamoangScraper

SCRAPERS: Dict[str, BaseScraper] = {
    "itssa": ItssaScraper(),
    "ddanzi": DdanziScraper(),
    "bobaedream": BobaedreamScraper(),
    "theqoo": TheqooScraper(),
    "fmkorea": FmkoreaScraper(),
    "damoang": DamoangScraper()
}

def get_all_scrapers() -> Dict[str, BaseScraper]:
    return SCRAPERS

def get_scraper(community_id: str) -> BaseScraper:
    return SCRAPERS.get(community_id)
