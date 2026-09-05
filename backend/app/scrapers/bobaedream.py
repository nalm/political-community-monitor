import re
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseScraper


class BobaedreamScraper(BaseScraper):
    def __init__(self):
        super().__init__("bobaedream")
        self.base_url = "https://www.bobaedream.co.kr"
        self.list_url = "https://www.bobaedream.co.kr/list?code=politic&s_cate=1"

    async def fetch_hot_posts(self, limit: int = 30) -> List[Dict[str, Any]]:
        posts: List[Dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            page = 1
            while len(posts) < limit and page <= 3:
                url = f"{self.list_url}&page={page}" if page > 1 else self.list_url
                r = await client.get(url, headers=self.get_headers())
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")

                for tr in soup.select("table.clistTable tbody tr, tbody tr"):
                    # 상단 고정 베스트글은 tr class="best" 로 표시된다. 최신글이 아니므로 제외.
                    if self.is_notice_row(tr):
                        continue

                    # 목록 컬럼: num01 / pl14(제목) / author02 / date / recomm / count(조회)
                    num_td = tr.select_one("td.num01")
                    if num_td is None or not num_td.get_text(strip=True).isdigit():
                        continue

                    a = tr.select_one("td.pl14 a, a.bsubject")
                    if not a:
                        continue
                    href = a.get("href", "")
                    cid_match = re.search(r'No=(\d+)', href)
                    if not cid_match:
                        continue

                    title = self.clean_text(a.get_text())
                    if len(title) < 2:
                        continue
                    # 댓글수는 제목 링크 밖의 별도 앵커에 <strong class="totreply"> 로 들어있다.
                    cmt_count = self.first_int(tr.select_one("td.pl14 strong.totreply"))

                    author_td = tr.select_one("td.author02")
                    posts.append({
                        "community_id": self.community_id,
                        "original_id": cid_match.group(1),
                        "title": title,
                        "url": href if href.startswith("http") else self.base_url + href,
                        "author": self.clean_text(author_td.get_text()) if author_td else "보배회원",
                        "view_count": self.first_int(tr.select_one("td.count")),
                        "vote_count": self.first_int(tr.select_one("td.recomm")),
                        "comment_count": cmt_count,
                    })
                page += 1

        return self.finalize(posts, limit)
