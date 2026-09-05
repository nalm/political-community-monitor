from typing import Dict
from .base import BaseScraper
from .itssa import ItssaScraper
from .ddanzi import DdanziScraper
from .bobaedream import BobaedreamScraper
from .theqoo import TheqooScraper

# 에펨코리아/다모앙 스크레이퍼는 제거되었습니다. 사유는 config.COMMUNITIES 주석 참고.
SCRAPERS: Dict[str, BaseScraper] = {
    "itssa": ItssaScraper(),
    "ddanzi": DdanziScraper(),
    "bobaedream": BobaedreamScraper(),
    "theqoo": TheqooScraper(),
}


def get_all_scrapers() -> Dict[str, BaseScraper]:
    return SCRAPERS


def get_scraper(community_id: str) -> BaseScraper:
    return SCRAPERS.get(community_id)
