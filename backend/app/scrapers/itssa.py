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
                while len(posts) < limit and page <= 4:
                    url = f"{self.list_url}?page={page}" if page > 1 else self.list_url
                    r = await client.get(url, headers=self.get_headers())
                    if r.status_code != 200:
                        break
                    soup = BeautifulSoup(r.text, "html.parser")
                    
                    rows = soup.select("table tbody tr, .list_table tbody tr, tr.ub-content")
                    for tr in rows:
                        # 1. 공지/고정글 체크 (class 또는 번호 영역 확인)
                        tr_class = str(tr.get("class", []))
                        if "notice" in tr_class or "pinned" in tr_class:
                            continue
                        
                        num_td = tr.select_one("td.num, .num, td:nth-child(1)")
                        if num_td and ("공지" in num_td.get_text() or "notice" in num_td.get_text().lower()):
                            continue

                        a = tr.select_one("td.title a, .title a, a")
                        if not a:
                            continue
                        href = a.get("href", "")
                        if not href or "#" in href:
                            continue
                        
                        # 잇싸 hot_politics 게시판 글만 수집 (공지나 타 게시판 링크 배제)
                        if "/hot_politics/" not in href:
                            continue
                            
                        cid = href.split("?")[0].split("/")[-1]
                        if not cid.isdigit() or href in seen_urls:
                            continue
                        
                        title = self.clean_text(a.get_text())
                        # 공지성 타이틀 필터
                        if len(title) < 2 or "멤버십" in title or "리뉴얼" in title or "공지" in title:
                            continue

                        seen_urls.add(href)

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
