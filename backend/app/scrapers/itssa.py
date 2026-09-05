import httpx
from typing import List, Dict, Any
from .base import BaseScraper, ScrapeError


class ItssaScraper(BaseScraper):
    def __init__(self):
        super().__init__("itssa")
        self.base_url = "https://itssa.co.kr"
        self.list_url = "https://itssa.co.kr/hot_politics"

    async def fetch_hot_posts(self, limit: int = 30) -> List[Dict[str, Any]]:
        posts: List[Dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            page = 1
            while len(posts) < limit and page <= 4:
                url = f"{self.list_url}?page={page}" if page > 1 else self.list_url
                try:
                    soup = await self.fetch_soup(client, url)
                except ScrapeError:
                    # 뒷 페이지 실패는 지금까지 모은 것으로 진행한다.
                    # 첫 페이지부터 실패면 수집 자체가 안 된 것이므로 그대로 알린다.
                    if posts:
                        break
                    raise

                for tr in soup.select("table tbody tr, .list_table tbody tr, tr.ub-content"):
                    # 잇싸 공지 행의 class 는 'notice' 가 아니라 'lnu' 다.
                    if self.is_notice_row(tr):
                        continue

                    a = tr.select_one("td.title a, .title a, a")
                    if not a:
                        continue
                    href = a.get("href", "")
                    # 다른 게시판(/notice, /weekly_east 등) 링크 배제
                    if not href or "#" in href or "/hot_politics/" not in href:
                        continue

                    cid = href.split("?")[0].split("/")[-1]
                    if not cid.isdigit():
                        continue

                    title = self.clean_text(a.get_text())
                    if len(title) < 2:
                        continue

                    author_el = tr.select_one("td.ldtu-nickname")
                    # 목록 컬럼: ldtu-number / ldtu-title-wrap / ldtu-nickname
                    #            / ldtu-date / lu-read(조회) / lu-vote(추천)
                    posts.append({
                        "community_id": self.community_id,
                        "original_id": cid,
                        "title": title,
                        "url": href if href.startswith("http") else self.base_url + href,
                        "author": self.clean_text(author_el.get_text()) if author_el else "잇싸 회원",
                        "view_count": self.first_int(tr.select_one("td.lu-read")),
                        "vote_count": self.first_int(tr.select_one("td.ldtu-vote")),
                        "comment_count": self.first_int(tr.select_one("a.lu-comment")),
                    })
                page += 1

        return self.finalize(posts, limit)
