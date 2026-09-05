"""수집된 게시물에서 정치 현안을 추출하는 분석기.

Claude API(Anthropic 공식 SDK)를 사용한다. 호출에 실패하면 게시물 제목·반응 수치만으로
집계하는 휴리스틱(`heuristic.py`)으로 내려가고, 어느 경로를 탔는지 호출자에게 알려준다.

응답 형식은 structured outputs(`output_config.format`)로 스키마를 강제하므로
마크다운 코드블록을 벗겨내거나 JSON 파싱 실패를 재시도할 필요가 없다.
"""

import asyncio
import json
from typing import Any, Dict, List, Tuple

from . import heuristic

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

METHOD_CLAUDE = "claude"
METHOD_HEURISTIC = "heuristic"

MODEL = "claude-opus-4-8"

# 품질·지연 조절 손잡이. high 기준 4개 커뮤니티 × 18개 게시물에 약 47초 걸린다.
# 지연이 문제면 medium 으로 낮춘다.
EFFORT = "high"

# 프롬프트에 넣을 커뮤니티당 게시물 수 (수집 자체는 30개를 모두 보관한다)
PROMPT_POSTS_PER_COMMUNITY = 18

# 응답 대기 상한. 사고(thinking) 시간을 포함한다.
REQUEST_TIMEOUT_SECONDS = 180.0


def _engagement(post: Dict[str, Any]) -> int:
    return (post.get("vote_count") or 0) * 3 + (post.get("comment_count") or 0)


def _issues_schema(community_ids: List[str]) -> Dict[str, Any]:
    """structured outputs 용 JSON 스키마.

    모든 객체에 additionalProperties: false 와 전체 required 가 필요하다.
    최소/최대 같은 수치 제약은 지원되지 않으므로 sentiment_score 범위는 프롬프트로 지시한다.
    """
    stance = {
        "type": "object",
        "properties": {
            "community_id": {"type": "string", "enum": community_ids},
            "stance_label": {"type": "string"},
            "sentiment_score": {"type": "number"},
            "summary_points": {"type": "array", "items": {"type": "string"}},
            "keywords": {"type": "array", "items": {"type": "string"}},
            "representative_posts": {"type": "array", "items": {"type": "string"}},
            "post_count": {"type": "integer"},
        },
        "required": [
            "community_id", "stance_label", "sentiment_score",
            "summary_points", "keywords", "representative_posts", "post_count",
        ],
        "additionalProperties": False,
    }
    issue = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "category": {"type": "string"},
            "summary": {"type": "string"},
            "key_dispute": {"type": "string"},
            "stances": {"type": "array", "items": stance},
        },
        "required": ["title", "category", "summary", "key_dispute", "stances"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {"issues": {"type": "array", "items": issue}},
        "required": ["issues"],
        "additionalProperties": False,
    }


SYSTEM_PROMPT = """당신은 대한민국 온라인 커뮤니티 여론 분석 전문가입니다.

주어진 게시물 목록만을 근거로 분석하세요. 목록에 없는 사건·발언·인물을 추측해 넣지 마세요.
근거가 부족하면 현안 수를 줄이십시오.

- sentiment_score 는 -1.0(강한 비판) ~ +1.0(강한 지지) 사이의 실수입니다.
- representative_posts 에는 제시된 목록에 실제로 있는 제목만 그대로 인용하세요.
- 해당 현안을 다루지 않은 커뮤니티는 post_count 0, stance_label "언급 없음" 으로 두세요.
- 특정 진영을 옹호하거나 폄하하지 말고, 관측된 반응을 그대로 기술하세요."""


class LLMAnalyzer:
    def __init__(self):
        self._client = anthropic.AsyncAnthropic() if HAS_ANTHROPIC else None

    def is_available(self) -> bool:
        """SDK 가 있고 자격 증명을 찾을 수 있는지."""
        if not HAS_ANTHROPIC or self._client is None:
            return False
        return bool(self._client.api_key or self._client.auth_token)

    async def analyze_issues_and_stances(
        self, posts_by_community: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[List[Dict[str, Any]], str, str]:
        """(현안 목록, 사용한 분석 엔진, 비고) 를 반환한다."""
        if self.is_available():
            try:
                issues = await asyncio.wait_for(
                    self._call_claude(posts_by_community), timeout=REQUEST_TIMEOUT_SECONDS
                )
                if issues:
                    return issues, METHOD_CLAUDE, ""
                note = "Claude 응답에 현안이 없어 휴리스틱으로 대체했습니다."
            except asyncio.TimeoutError:
                note = "Claude 응답이 지연되어 휴리스틱으로 대체했습니다."
            except anthropic.AuthenticationError:
                note = "ANTHROPIC_API_KEY 가 유효하지 않아 휴리스틱으로 분석했습니다."
            except anthropic.RateLimitError:
                note = "Claude API 사용량 한도를 초과해 휴리스틱으로 대체했습니다."
            except anthropic.APIStatusError as e:
                note = f"Claude API 오류(HTTP {e.status_code})로 휴리스틱으로 대체했습니다."
            except anthropic.APIConnectionError:
                note = "Claude API 에 연결하지 못해 휴리스틱으로 대체했습니다."
            except Exception as e:
                note = f"Claude 호출 실패({type(e).__name__})로 휴리스틱으로 대체했습니다."
            print(f"[LLMAnalyzer] {note}")
        elif not HAS_ANTHROPIC:
            note = "anthropic 패키지가 없어 휴리스틱으로 분석했습니다."
        else:
            note = "ANTHROPIC_API_KEY 가 설정되지 않아 휴리스틱으로 분석했습니다."

        return heuristic.analyze(posts_by_community), METHOD_HEURISTIC, note

    async def _call_claude(
        self, posts_by_community: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        community_ids = [cid for cid, posts in posts_by_community.items() if posts]
        if not community_ids:
            return []

        lines = []
        for comm_id in community_ids:
            posts = posts_by_community[comm_id]
            # 반응이 큰 글 위주로 추린다. 원문 목록은 전량 보존된다.
            ranked = sorted(posts, key=_engagement, reverse=True)[:PROMPT_POSTS_PER_COMMUNITY]
            lines.append(f"\n### 커뮤니티: {comm_id} (수집 {len(posts)}개 중 반응 상위 {len(ranked)}개)")
            for idx, p in enumerate(ranked, 1):
                lines.append(
                    f"{idx}. {p['title']} "
                    f"(추천 {p.get('vote_count', 0)}, 댓글 {p.get('comment_count', 0)})"
                )

        prompt = (
            "아래는 방금 수집된 각 커뮤니티 인기 게시판의 실제 최신 게시물입니다.\n"
            f"{chr(10).join(lines)}\n\n"
            "지금 실제로 가장 활발히 다뤄지는 핵심 정치·사회 현안 2~3개를 뽑고, "
            "각 커뮤니티가 그 현안을 어떻게 다루는지 정리하세요."
        )

        response = await self._client.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive"},
            output_config={
                "effort": EFFORT,
                "format": {"type": "json_schema", "schema": _issues_schema(community_ids)},
            },
            messages=[{"role": "user", "content": prompt}],
        )

        if response.stop_reason == "refusal":
            raise RuntimeError("모델이 응답을 거부했습니다.")

        # structured outputs 를 쓰면 text 블록에 스키마를 만족하는 JSON 이 담겨 온다.
        text = next((b.text for b in response.content if b.type == "text"), "")
        if not text:
            return []

        issues = json.loads(text).get("issues", [])
        return self._drop_unknown_communities(issues, set(community_ids))

    @staticmethod
    def _drop_unknown_communities(
        issues: List[Dict[str, Any]], valid: set
    ) -> List[Dict[str, Any]]:
        """스키마 enum 을 우회해 들어온 커뮤니티 id 가 있으면 걸러낸다."""
        for issue in issues:
            issue["stances"] = [
                s for s in issue.get("stances", []) if s.get("community_id") in valid
            ]
        return [i for i in issues if i.get("stances")]
