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
        posts = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                page = 1
                seen_urls = set()
                while len(posts) < limit and page <= 2:
                    url = f"{self.list_url}&page={page}" if page > 1 else self.list_url
                    r = await client.get(url, headers=self.get_headers())
                    if r.status_code != 200:
                        break
                    soup = BeautifulSoup(r.text, "html.parser")

                    for tr in soup.select("table.clistTable tbody tr, tbody tr"):
                        tds = tr.find_all("td")
                        if len(tds) < 5:
                            continue
                        
                        a = tr.select_one("a.bsubject, td.plSubject a, a")
                        if not a:
                            continue
                        href = a.get("href", "")
                        if not href or href in seen_urls:
                            continue
                        if "view?code=politic" not in href and "code=politic" not in href:
                            continue
                        seen_urls.add(href)

                        raw_title = self.clean_text(a.get_text())
                        # 댓글수 추출 (예: (10))
                        cmt_count = 0
                        cmt_match = re.search(r'\((\d+)\)$', raw_title)
                        if cmt_match:
                            cmt_count = int(cmt_match.group(1))
                            title = re.sub(r'\(\d+\)$', '', raw_title).strip()
                        else:
                            title = raw_title

                        if len(title) < 2:
                            continue

                        # 추천수 & 조회수
                        vote_val = 50
                        recom_td = tr.select_one("td.recomm, td:nth-child(5)")
                        if recom_td:
                            vote_text = recom_td.get_text(strip=True)
                            if vote_text.isdigit():
                                vote_val = int(vote_text)

                        view_val = 5000
                        view_td = tr.select_one("td.count, td:nth-child(6)")
                        if view_td:
                            view_text = view_td.get_text(strip=True)
                            if view_text.isdigit():
                                view_val = int(view_text)

                        author_td = tr.select_one("span.author, td.author, td:nth-child(3)")
                        author = self.clean_text(author_td.get_text()) if author_td else "보배회원"
                        full_url = self.base_url + href if not href.startswith("http") else href
                        cid_match = re.search(r'No=(\d+)', href)
                        cid = cid_match.group(1) if cid_match else str(len(posts)+1)

                        posts.append({
                            "community_id": self.community_id,
                            "original_id": cid,
                            "title": title,
                            "url": full_url,
                            "author": author,
                            "view_count": view_val,
                            "vote_count": vote_val,
                            "comment_count": cmt_count
                        })
                        if len(posts) >= limit:
                            break
                    page += 1
        except Exception as e:
            print(f"[BobaedreamScraper] Error: {e}")

        return posts[:limit]
