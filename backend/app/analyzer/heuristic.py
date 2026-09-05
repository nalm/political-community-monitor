"""LLM 없이 수집된 실제 게시글만으로 현안을 추출하는 분석기.

Gemini 를 쓸 수 없을 때(키 미설정·호출 실패·타임아웃)의 대체 경로다.
지어내지 않는 것이 이 모듈의 유일한 원칙이다. 모든 출력은 수집된 제목과
조회/추천/댓글 수치에서 직접 계산되며, 여론에 대한 해석을 창작하지 않는다.

한계가 분명하다:
  - 형태소 분석기 없이 어절에서 조사만 떼어내므로 토큰이 거칠다.
  - 감성 점수는 소규모 감성어 사전 기반이라 반어·인용을 구분하지 못한다.
따라서 stance_label 에는 '추정' 을 명시하고, summary_points 는 해석이 아니라
관측된 사실(빈도·반응량·실제 제목)만 담는다.
"""

import re
from collections import Counter
from typing import Any, Dict, List

# 조사/어미를 떼기 위한 접미사 (긴 것부터 시도)
_PARTICLES = (
    "이라는", "라는", "에서는", "에게서", "이라고", "라고", "에서", "에게", "한테",
    "으로", "까지", "부터", "조차", "마저", "처럼", "보다", "이나", "든지",
    "은", "는", "이", "가", "을", "를", "의", "에", "도", "만", "과", "와", "로",
)

# 정치 현안 후보에서 제외할 일반어
_STOPWORDS = frozenset({
    "그리고", "하지만", "그런데", "이번", "진짜", "그냥", "오늘", "사람", "생각",
    "이제", "우리", "근데", "여러분", "정도", "때문", "경우", "얘기", "이야기", "정말",
    "관련", "다시", "가장", "모두", "너무", "많이", "이건", "저건", "그게", "이거",
    "합니다", "입니다", "했다", "한다", "된다", "있다", "없다", "같다", "보다", "네요",
    "ㅋㅋㅋ", "ㅎㅎㅎ", "속보", "단독", "펌글", "스압", "재업",
    "솔직히", "다시한번", "이러고", "그러고", "역시", "심지어", "아무리", "어차피",
    "이유", "상황", "수준", "모습", "부분", "가능", "이제야", "결국", "오늘자",
    "그것", "이것", "저것", "여기", "거기", "저기", "누구", "무엇", "어디",
    "내가", "네가", "제가", "그가", "저는", "나는", "너는",
})

# 어절 끝이 활용형이면 명사가 아닐 가능성이 높다. 형태소 분석기가 없어
# 완벽하진 않지만 '느끼는게' · '역대급이다' 같은 토큰을 상당수 걸러낸다.
_VERB_ENDINGS = (
    "하다", "이다", "되다", "있다", "없다", "한다", "된다", "였다", "했다", "된다",
    "는게", "는데", "면서", "니까", "지만", "라며", "하는", "되는", "드는", "같은",
    "같이", "했던", "하던", "라고", "이라", "든지", "거나",
)

_POSITIVE = frozenset({
    "지지", "환영", "호평", "성과", "정상화", "통과", "승리", "회복", "감사", "응원",
    "훌륭", "잘했", "다행", "기대", "개선", "상승", "호전", "찬성", "칭찬", "성공",
    "합의", "타결", "돌파", "선방", "미담", "감동", "희망",
})

_NEGATIVE = frozenset({
    "비판", "규탄", "분노", "논란", "의혹", "폭락", "위기", "참사", "사퇴", "탄핵",
    "구속", "기소", "최악", "거짓", "조작", "부패", "카르텔", "독재", "망신", "실망",
    "배신", "우려", "반발", "질타", "부정", "갈등", "충격", "무너", "헛소리", "어이없",
    "폭탄", "은폐", "특혜", "황당", "먹통", "논쟁", "공방", "파문",
    "압수수색", "고발", "경질", "해임", "결렬", "적자", "실패", "붕괴",
})


def _tokens(title: str) -> List[str]:
    """제목에서 명사 후보 토큰을 뽑는다(조사 제거 + 활용형 배제)."""
    out = []
    for raw in re.findall(r'[가-힣]{2,}|[A-Za-z]{3,}', title):
        tok = raw
        for p in _PARTICLES:
            if len(tok) > len(p) + 1 and tok.endswith(p):
                tok = tok[: -len(p)]
                break
        if len(tok) < 2 or tok in _STOPWORDS:
            continue
        if tok.endswith(_VERB_ENDINGS):
            continue
        # '솔직히' · '확실히' 류 부사
        if len(tok) >= 3 and tok.endswith("히"):
            continue
        out.append(tok)
    return out


def _sentiment(titles: List[str]) -> float:
    """감성어 사전으로 -1.0 ~ +1.0 점수를 낸다. 감성어가 없으면 0.0."""
    pos = neg = 0
    for t in titles:
        for w in _POSITIVE:
            if w in t:
                pos += 1
        for w in _NEGATIVE:
            if w in t:
                neg += 1
    if pos + neg == 0:
        return 0.0
    return round((pos - neg) / (pos + neg), 2)


def _stance_label(score: float, matched: int) -> str:
    if matched == 0:
        return "언급 없음"
    if score <= -0.6:
        return "부정 우세 (추정)"
    if score <= -0.2:
        return "다소 부정 (추정)"
    if score < 0.2:
        return "중립·혼재 (추정)"
    if score < 0.6:
        return "다소 긍정 (추정)"
    return "긍정 우세 (추정)"


def _engagement(post: Dict[str, Any]) -> int:
    return (post.get("vote_count") or 0) * 3 + (post.get("comment_count") or 0)


def analyze(posts_by_community: Dict[str, List[Dict[str, Any]]],
            max_issues: int = 3) -> List[Dict[str, Any]]:
    active = {cid: posts for cid, posts in posts_by_community.items() if posts}
    if not active:
        return []

    # 1) 토큰별로 어느 커뮤니티에서 몇 번 등장했는지 집계
    token_communities: Dict[str, set] = {}
    token_hits: Counter = Counter()
    for cid, posts in active.items():
        for p in posts:
            for tok in set(_tokens(p["title"])):
                token_communities.setdefault(tok, set()).add(cid)
                token_hits[tok] += 1

    # 2) 여러 커뮤니티가 동시에 다루는 토큰을 현안 후보로 우선한다
    candidates = [
        (tok, len(comms), token_hits[tok])
        for tok, comms in token_communities.items()
        if len(comms) >= 2 and token_hits[tok] >= 3
    ]
    if not candidates:
        candidates = [(tok, len(token_communities[tok]), cnt)
                      for tok, cnt in token_hits.most_common(20) if cnt >= 2]
    candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)

    issues: List[Dict[str, Any]] = []
    used_tokens: set = set()

    for tok, comm_count, hit_count in candidates:
        if len(issues) >= max_issues:
            break
        # 이미 만든 현안의 키워드와 겹치면 건너뛴다 (부분 문자열 포함)
        if any(tok in u or u in tok for u in used_tokens):
            continue

        stances = []
        total_matched = 0
        for cid, posts in active.items():
            matched = [p for p in posts if tok in p["title"]]
            total_matched += len(matched)
            matched.sort(key=_engagement, reverse=True)
            titles = [p["title"] for p in matched]

            score = _sentiment(titles)
            points = []
            if matched:
                share = round(len(matched) / len(posts) * 100)
                points.append(f"수집된 {len(posts)}개 중 {len(matched)}개 글이 '{tok}' 언급 (전체의 {share}%)")
                top = matched[0]
                points.append(
                    f"반응이 가장 큰 글: 추천 {top.get('vote_count', 0)} · 댓글 {top.get('comment_count', 0)} · 조회 {top.get('view_count', 0)}"
                )
                counts = Counter(
                    t for p in matched for t in _tokens(p["title"]) if t != tok
                )
                # 두 번 이상 나온 단어를 우선한다. 한 건만 매칭돼 그런 단어가 없으면
                # 상위 3개로 대체한다(이 경우 잡음이 섞일 수 있다).
                repeated = [w for w, c in counts.most_common(5) if c >= 2]
                kws = repeated or [w for w, _ in counts.most_common(3)]
                if kws:
                    points.append(f"함께 등장한 단어: {', '.join(kws)}")
            else:
                points.append(f"수집된 {len(posts)}개 글에서 '{tok}' 언급 없음")
                kws = []

            stances.append({
                "community_id": cid,
                "stance_label": _stance_label(score, len(matched)),
                "sentiment_score": score,
                "summary_points": points,
                "keywords": kws,
                "representative_posts": titles[:2],
                "post_count": len(matched),
                "total_votes": sum(p.get("vote_count") or 0 for p in matched),
            })

        used_tokens.add(tok)
        issues.append({
            "title": f"'{tok}' 관련 게시물 집중",
            "category": "키워드 기반 자동 추출",
            "summary": (
                f"수집된 {sum(len(v) for v in active.values())}개 글 가운데 {total_matched}개가 "
                f"'{tok}' 을(를) 제목에 포함했고, {comm_count}개 커뮤니티에서 공통으로 등장했습니다. "
                f"LLM 분석이 아니라 제목 빈도·반응 수치로 계산한 결과입니다."
            ),
            "key_dispute": (
                "감성 점수는 소규모 감성어 사전 기반 추정치입니다. "
                "반어·인용을 구분하지 못하므로 원문 확인이 필요합니다."
            ),
            "stances": stances,
        })

    return issues
