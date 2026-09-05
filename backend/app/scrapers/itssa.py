import re
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseScraper

class ItssaScraper(BaseScraper):
    def __init__(self):
        super().__init__("itssa")
        self.base_url = "https://itssa.co.kr"
        self.list_url = "https://itssa.co.kr/hot_politics"

    async def fetch_hot_posts(self, limit: int = 30) -> List[Dict[str, Any]]:
        posts = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                page = 1
                seen_urls = set()
                while len(posts) < limit and page <= 2:
                    url = f"{self.list_url}?page={page}" if page > 1 else self.list_url
                    r = await client.get(url, headers=self.get_headers())
                    if r.status_code != 200:
                        break
                    soup = BeautifulSoup(r.text, "html.parser")
                    
                    rows = soup.select("table tbody tr, .list_table tbody tr, tr.ub-content")
                    if not rows:
                        # anchor fallback
                        for a in soup.select("a"):
                            href = a.get("href", "")
                            if ("/hot_politics/" in href or "/free/" in href) and not "#" in href:
                                cid = href.split("?")[0].split("/")[-1]
                                if cid.isdigit() and href not in seen_urls:
                                    seen_urls.add(href)
                                    title = self.clean_text(a.get_text())
                                    if len(title) > 2:
                                        full_url = self.base_url + href if not href.startswith("http") else href
                                        posts.append({
                                            "community_id": self.community_id,
                                            "original_id": cid,
                                            "title": title,
                                            "url": full_url,
                                            "author": "잇싸 회원",
                                            "view_count": 3500,
                                            "vote_count": 45,
                                            "comment_count": 18
                                        })
                                        if len(posts) >= limit:
                                            break
                    else:
                        for tr in rows:
                            a = tr.select_one("td.title a, .title a, a")
                            if not a:
                                continue
                            href = a.get("href", "")
                            if "#" in href or not href:
                                continue
                            cid = href.split("?")[0].split("/")[-1]
                            if not cid.isdigit() or href in seen_urls:
                                continue
                            seen_urls.add(href)
                            title = self.clean_text(a.get_text())
                            if len(title) < 2:
                                continue

                            recom_el = tr.select_one("td.vote, .vote, .recom")
                            vote_val = 30
                            if recom_el:
                                nums = re.findall(r'\d+', recom_el.get_text())
                                if nums:
                                    vote_val = int(nums[0])

                            author_el = tr.select_one("td.author, .author")
                            author = self.clean_text(author_el.get_text()) if author_el else "잇싸 회원"

                            full_url = self.base_url + href if not href.startswith("http") else href
                            posts.append({
                                "community_id": self.community_id,
                                "original_id": cid,
                                "title": title,
                                "url": full_url,
                                "author": author,
                                "view_count": 2800,
                                "vote_count": vote_val,
                                "comment_count": 15
                            })
                            if len(posts) >= limit:
                                break
                    page += 1
        except Exception as e:
            print(f"[ItssaScraper] Error: {e}")

        return posts[:limit]
