import asyncio
import json
import os
from typing import Any, Dict, List, Tuple

from ..config import GEMINI_API_KEY
from . import heuristic

try:
    import google.generativeai as genai
    HAS_GENAI = True
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
except ImportError:
    HAS_GENAI = False

METHOD_GEMINI = "gemini"
METHOD_HEURISTIC = "heuristic"

# 프롬프트에 넣을 커뮤니티당 게시물 수 (수집 자체는 30개를 모두 저장한다)
PROMPT_POSTS_PER_COMMUNITY = 18


def _engagement(post: Dict[str, Any]) -> int:
    return (post.get("vote_count") or 0) * 3 + (post.get("comment_count") or 0)


class LLMAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or GEMINI_API_KEY
        self.model_name = "gemini-2.5-flash"

    def is_available(self) -> bool:
        return bool(HAS_GENAI and self.api_key)

    async def analyze_issues_and_stances(
        self, posts_by_community: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[List[Dict[str, Any]], str, str]:
        """(현안 목록, 사용한 분석 엔진, 비고) 를 반환한다.

        Gemini 호출이 실패하면 수집된 게시글 기반 휴리스틱으로 내려간다.
        어느 경로를 탔는지 호출자에게 알려 UI 에 표시할 수 있게 한다.
        """
        if self.is_available():
            try:
                # 게시물 120개를 한 번에 넣으면 gemini-2.5-flash 가 50초 안팎 걸린다.
                # UI 가 '분석 중' 을 계속 보여주므로 넉넉하게 잡는다.
                issues = await asyncio.wait_for(
                    self._call_gemini_analysis(posts_by_community), timeout=120.0
                )
                if issues:
                    return issues, METHOD_GEMINI, ""
                note = "Gemini 응답이 비어 있어 휴리스틱으로 대체했습니다."
            except Exception as e:
                note = f"Gemini 호출 실패({type(e).__name__})로 휴리스틱으로 대체했습니다."
            print(f"[LLMAnalyzer] {note}")
        elif not HAS_GENAI:
            note = "google-generativeai 패키지가 없어 휴리스틱으로 분석했습니다."
        else:
            note = "GEMINI_API_KEY 가 설정되지 않아 휴리스틱으로 분석했습니다."

        return heuristic.analyze(posts_by_community), METHOD_HEURISTIC, note

    async def _call_gemini_analysis(
        self, posts_by_community: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        context_lines = []
        for comm_id, posts in posts_by_community.items():
            if not posts:
                continue
            # 수집분 전체(30개)를 넣으면 응답이 50초를 넘겨 SDK 기본 데드라인(60초)에
            # 걸린다. 반응이 큰 글 위주로 추려 넣는다. 원문 목록은 전량 보존된다.
            ranked = sorted(posts, key=_engagement, reverse=True)[:PROMPT_POSTS_PER_COMMUNITY]
            context_lines.append(
                f"\n### [커뮤니티: {comm_id} (수집 {len(posts)}개 중 반응 상위 {len(ranked)}개)]"
            )
            for idx, p in enumerate(ranked, 1):
                context_lines.append(
                    f"{idx}. {p['title']} (추천 {p.get('vote_count', 0)}, 댓글 {p.get('comment_count', 0)})"
                )

        community_ids = [cid for cid, posts in posts_by_community.items() if posts]
        prompt = f"""당신은 대한민국 온라인 커뮤니티 여론 분석 전문가입니다.
아래는 방금 수집된 각 커뮤니티 인기 게시판의 실제 최신 게시글 목록입니다.

{chr(10).join(context_lines)}

위 목록만을 근거로 분석하세요. 목록에 없는 사건이나 발언을 추측해 넣지 마세요.
근거가 부족하면 현안 수를 줄여도 됩니다.

지금 실제로 가장 활발히 다뤄지는 핵심 정치/사회 현안 2~3개를 뽑고,
각 커뮤니티가 그 현안을 어떻게 다루는지 JSON 으로 출력하세요.
representative_posts 에는 반드시 위 목록에 실제로 있는 제목만 그대로 쓰세요.
해당 현안을 다루지 않은 커뮤니티는 post_count 0, stance_label "언급 없음" 으로 두세요.

마크다운 코드블록 없이 순수 JSON 배열만 출력하세요:
[
  {{
    "title": "현안 제목",
    "category": "정치/사법 | 정책/경제 | 정당/선거 | 사회/이슈",
    "summary": "수집된 글에 근거한 배경 요약 2-3문장",
    "key_dispute": "커뮤니티 간 핵심 시각차",
    "stances": [
      {{
        "community_id": {json.dumps(community_ids, ensure_ascii=False)} 중 하나,
        "stance_label": "짧은 스탠스 라벨",
        "sentiment_score": -1.0 ~ 1.0 사이 실수,
        "summary_points": ["관측된 반응 1", "관측된 반응 2", "관측된 반응 3"],
        "keywords": ["키워드1", "키워드2", "키워드3"],
        "representative_posts": ["위 목록에 실제로 있는 제목"],
        "post_count": 해당 현안을 다룬 글 수
      }}
    ]
  }}
]"""

        def _generate() -> str:
            model = genai.GenerativeModel(self.model_name)
            # request_options 는 google-generativeai 0.5+ 에서만 받는다.
            # 설치본이 0.3.x 면 즉시 ValueError 가 나므로 인자 없이 다시 부른다.
            try:
                return model.generate_content(
                    prompt, request_options={"timeout": 110}
                ).text.strip()
            except (TypeError, ValueError):
                return model.generate_content(prompt).text.strip()

        # google-generativeai 는 동기 API 라 이벤트 루프를 막지 않도록 스레드로 넘긴다.
        text = await asyncio.to_thread(_generate)

        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        issues = json.loads(text.strip())
        return self._drop_unknown_communities(issues, set(community_ids))

    @staticmethod
    def _drop_unknown_communities(issues: List[Dict[str, Any]],
                                  valid: set) -> List[Dict[str, Any]]:
        """모델이 지어낸 커뮤니티 id 가 섞여 들어오는 것을 막는다."""
        for issue in issues:
            issue["stances"] = [
                s for s in issue.get("stances", []) if s.get("community_id") in valid
            ]
        return [i for i in issues if i.get("stances")]
