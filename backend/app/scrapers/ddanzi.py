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
        posts = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                page = 1
                seen_ids = set()
                while len(posts) < limit and page <= 4:
                    url = f"{self.list_url}&page={page}" if page > 1 else self.list_url
                    r = await client.get(url, headers=self.get_headers())
                    if r.status_code != 200:
                        break
                    soup = BeautifulSoup(r.text, "html.parser")

                    for tr in soup.select("table tbody tr"):
                        # 공지글/이벤트글 필터링
                        tr_class = str(tr.get("class", []))
                        if "notice" in tr_class or "notice_expand" in tr_class:
                            continue
                        
                        num_el = tr.select_one("td.no, td.num")
                        if num_el and ("공지" in num_el.get_text() or "notice" in num_el.get_text().lower()):
                            continue

                        title_a = tr.select_one("td.title a")
                        if not title_a:
                            continue
                        href = title_a.get("href", "")
                        if not href or "#comment" in href:
                            continue
                        title = self.clean_text(title_a.get_text())
                        if not title or len(title) < 2:
                            continue

                        cid_match = re.search(r'document_srl=(\d+)', href)
                        if not cid_match:
                            cid_match = re.search(r'/free/(\d+)', href)
                        cid = cid_match.group(1) if cid_match else href.split("/")[-1].split("?")[0]
                        if not cid.isdigit() or cid in seen_ids:
                            continue
                        seen_ids.add(cid)

                        vote_el = tr.select_one("td.voteNum, td.m_no")
                        vote_val = 50
                        if vote_el:
                            nums = re.findall(r'\d+', vote_el.get_text())
                            if nums:
                                vote_val = int(nums[0])

                        read_el = tr.select_one("td.readNum")
                        read_val = 6000
                        if read_el:
                            nums = re.findall(r'\d+', read_el.get_text())
                            if nums:
                                read_val = int(nums[0])

                        author_el = tr.select_one("td.author")
                        author = self.clean_text(author_el.get_text()) if author_el else "딴지회원"

                        full_url = self.base_url + href if not href.startswith("http") else href
                        posts.append({
                            "community_id": self.community_id,
                            "original_id": cid,
                            "title": title,
                            "url": full_url,
                            "author": author,
                            "view_count": read_val,
                            "vote_count": vote_val,
                            "comment_count": 25
                        })
                        if len(posts) >= limit:
                            break
                    page += 1
        except Exception as e:
            print(f"[DdanziScraper] Error: {e}")

        return posts[:limit]
