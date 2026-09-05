import re
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseScraper

class TheqooScraper(BaseScraper):
    def __init__(self):
        super().__init__("theqoo")
        self.base_url = "https://theqoo.net"
        self.list_url = "https://theqoo.net/square/category/3836759081?filter_mode=hot"

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

                    for tr in soup.select("table tbody tr, .show_normal tbody tr"):
                        tr_class = str(tr.get("class", []))
                        if "notice" in tr_class or "notice_expand" in tr_class:
                            continue
                        
                        # 번호 영역이 '공지'인 경우 제외
                        num_el = tr.select_one("td.m_no, td:nth-child(1)")
                        if num_el and ("공지" in num_el.get_text() or "notice" in num_el.get_text().lower()):
                            continue

                        a = tr.select_one("td.title a")
                        if not a:
                            continue
                        href = a.get("href", "")
                        if not href or "#" in href or "/event/" in href or "/notice/" in href:
                            continue
                        title = self.clean_text(a.get_text())
                        if not title or len(title) < 2:
                            continue
                        
                        # 공지 및 필독 키워드 차단
                        if any(kw in title for kw in ["공지", "필독", "이용 규칙", "보안 강화", "비밀번호 변경", "카테고리 추가"]):
                            continue

                        cid = href.split("?")[0].split("/")[-1]
                        if not cid.isdigit() or cid in seen_ids:
                            continue
                        seen_ids.add(cid)

                        author_el = tr.select_one("td.author")
                        author = self.clean_text(author_el.get_text()) if author_el else "무명의 더쿠"

                        view_el = tr.select_one("td.m_no, td.read")
                        view_val = 8000
                        if view_el:
                            nums = re.findall(r'\d+', view_el.get_text())
                            if nums:
                                view_val = int(nums[0])

                        full_url = self.base_url + href if not href.startswith("http") else href
                        posts.append({
                            "community_id": self.community_id,
                            "original_id": cid,
                            "title": title,
                            "url": full_url,
                            "author": author,
                            "view_count": view_val,
                            "vote_count": 80,
                            "comment_count": 45
                        })
                        if len(posts) >= limit:
                            break
                    page += 1
        except Exception as e:
            print(f"[TheqooScraper] Error: {e}")

        return posts[:limit]
