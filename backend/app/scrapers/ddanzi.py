import re
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseScraper


class DdanziScraper(BaseScraper):
    def __init__(self):
        super().__init__("ddanzi")
        self.base_url = "https://www.ddanzi.com"
        self.list_url = "https://www.ddanzi.com/index.php?mid=free&statusList=HOT%2CHOTBEST%2CHOTAC%2CHOTBESTAC"

    async def fetch_hot_posts(self, limit: int = 30) -> List[Dict[str, Any]]:
        posts: List[Dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            page = 1
            while len(posts) < limit and page <= 4:
                url = f"{self.list_url}&page={page}" if page > 1 else self.list_url
                r = await client.get(url, headers=self.get_headers())
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")

                # 상단 배너 영역은 class="bbn ...", 공지는 class="notice".
                for tr in soup.select("table tbody tr"):
                    if self.is_notice_row(tr):
                        continue

                    title_a = tr.select_one("td.title a")
                    if not title_a:
                        continue
                    href = title_a.get("href", "")
                    if not href or "#comment" in href:
                        continue

                    cid_match = re.search(r'document_srl=(\d+)', href) or re.search(r'/free/(\d+)', href)
                    if not cid_match:
                        continue

                    title = self.clean_text(title_a.get_text())
                    if len(title) < 2:
                        continue

                    author_el = tr.select_one("td.author")
                    # 목록 컬럼: no / title / author / time / voteNum / readNum
                    posts.append({
                        "community_id": self.community_id,
                        "original_id": cid_match.group(1),
                        "title": title,
                        "url": href if href.startswith("http") else self.base_url + href,
                        "author": self.clean_text(author_el.get_text()) if author_el else "딴지회원",
                        "view_count": self.first_int(tr.select_one("td.readNum")),
                        "vote_count": self.first_int(tr.select_one("td.voteNum")),
                        "comment_count": self.first_int(tr.select_one("td.title span.talk")),
                    })
                page += 1

        return self.finalize(posts, limit)
