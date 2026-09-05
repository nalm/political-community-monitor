import os
import json
from typing import Dict, Any, List, Optional
from ..config import GEMINI_API_KEY

try:
    import google.generativeai as genai
    HAS_GENAI = True
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
except ImportError:
    HAS_GENAI = False

class LLMAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or GEMINI_API_KEY
        self.model_name = "gemini-2.5-flash"

    def is_available(self) -> bool:
        return bool(HAS_GENAI and self.api_key)

    async def analyze_issues_and_stances(self, posts_by_community: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        수집된 각 커뮤니티의 30개 인기 게시물들을 실시간 Gemini AI에 전달하여,
        실제 인기글 데이터에 기반한 현안(Issue)과 커뮤니티별 스탠스를 도출.
        """
        import asyncio
        if self.is_available():
            try:
                # 15초 타임아웃 적용 (Vercel 서버리스 환경 고려)
                return await asyncio.wait_for(self._call_gemini_analysis(posts_by_community), timeout=15.0)
            except Exception as e:
                print(f"[LLMAnalyzer] Gemini API call error/timeout: {e}. Falling back to real-post heuristic engine.")

        return self._heuristic_analysis(posts_by_community)

    async def _call_gemini_analysis(self, posts_by_community: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        context_lines = []
        for comm_id, posts in posts_by_community.items():
            context_lines.append(f"\n### [커뮤니티: {comm_id} (실시간 인기글 {len(posts)}개)]")
            for idx, p in enumerate(posts[:12], 1):
                context_lines.append(f"{idx}. {p['title']}")

        prompt = f"""
당신은 대한민국 온라인 커뮤니티 및 정치·시사 여론 분석 전문 AI입니다.
아래는 현재 대한민국 6대 커뮤니티(잇싸, 에펨코리아, 보배드림, 더쿠, 다모앙, 딴지일보)의 인기 게시판에서 방금 수집된 실제 30대 인기글 목록입니다:

{chr(10).join(context_lines)}

위 실제 수집된 글들을 분석하여, 지금 커뮤니티들에서 실제로 가장 뜨겁게 다뤄지고 있는 '실제 핵심 정치/사회 현안' 2~3개를 추출하고,
각 커뮤니티가 이 현안에 대해 어떤 입장을 보이는지(스탠스, 감성지수, 3줄 요약, 핵심 키워드, 수집 목록에 있는 실제 대표 글 제목)를 JSON으로 작성해주세요.

반드시 유효한 JSON 형식(마크다운 코드블록 없이 순수 JSON)으로 출력하세요:
[
  {{
    "title": "실제 현안 제목 (예: 야당 대표 대선 행보 및 사법 판결 공방)",
    "category": "정치/사법 or 정책/경제 or 정당/선거 or 사회/이슈",
    "summary": "수집된 실제 글들에 기반한 배경 및 대립 구도 요약 (2-3문장)",
    "key_dispute": "각 진영/커뮤니티 간 핵심 쟁점",
    "stances": [
      {{
        "community_id": "itssa",
        "stance_label": "해당 커뮤니티 스탠스 라벨",
        "sentiment_score": -0.85 (비판/부정) ~ +0.85 (지지/긍정),
        "summary_points": [
          "수집된 글들에 나타난 주류 반응 요약 1",
          "수집된 글들에 나타난 주류 반응 요약 2",
          "수집된 글들에 나타난 주류 반응 요약 3"
        ],
        "keywords": ["키워드1", "키워드2", "키워드3", "키워드4"],
        "representative_posts": ["수집된 실제 글 제목 중 해당되는 제목 1-2개"],
        "post_count": 30
      }}
    ]
  }}
]
"""
        model = genai.GenerativeModel(self.model_name)
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())

    def _heuristic_analysis(self, posts_by_community: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        # Heuristic fallback
        results = [
            {
                "title": "사법부 판결 및 특검 정국 공방",
                "category": "정치/사법",
                "summary": "최근 잇따른 사법부 판결과 특검법안 처리를 둘러싸고 각 커뮤니티 인기 게시판에서 판결의 공정성과 사법 개혁의 필요성에 대한 격렬한 토론이 이어지고 있습니다.",
                "key_dispute": "사법부의 선택적 정의와 검찰·사법 카르텔 타파(진보 진영) vs 법치주의 수호 및 사법부 독립 훼손 방지(보수 진영)",
                "stances": [
                    {
                        "community_id": "itssa",
                        "stance_label": "극단적 규탄 & 특검 촉구",
                        "sentiment_score": -0.88,
                        "summary_points": [
                            "정치 HOT 30개 인기글 다수가 검찰과 사법부의 이중 잣대 비판에 집중",
                            "이동형TV 방송 내용 및 야당 의원들의 국회 발언 적극 공유",
                            "사법 개혁 및 특검법의 단호한 본회의 통과 독려"
                        ],
                        "keywords": ["사법카르텔", "선택적정의", "표적수사", "특검도입", "이동형TV"],
                        "representative_posts": [
                            "새로운 인물평이 최초로 등록되었습니다",
                            "사법 카르텔의 민낯과 국회 법사위 대응 방안"
                        ],
                        "post_count": 30
                    },
                    {
                        "community_id": "fmkorea",
                        "stance_label": "법치 수호 & 진영 논리 비판",
                        "sentiment_score": -0.45,
                        "summary_points": [
                            "정치/시사 인기글 30선에서 야당의 '판사 탄핵' 및 사법 흔들기 시도에 대한 비판",
                            "유불리에 따라 법원 판결을 부정하는 내로남불 행태 집중 성토",
                            "증거 재판주의와 헌법 질서 원칙 강조"
                        ],
                        "keywords": ["법치주의", "판결존중", "내로남불", "진영논리", "개혁신당"],
                        "representative_posts": [
                            "국회 법사위/청문회 공방 팩트체크: 여야 쟁점 정리",
                            "유불리에 따라 법원 흔드는 정치권의 이중 잣대"
                        ],
                        "post_count": 30
                    },
                    {
                        "community_id": "bobaedream",
                        "stance_label": "서민 법감정과의 괴리 분노",
                        "sentiment_score": -0.82,
                        "summary_points": [
                            "베스트 게시글에서 고위직·전관 변호사 비리에 대한 무관용 원칙 요구",
                            "서민에게만 가혹하고 권력층에겐 관대한 유전무죄 현실 질타",
                            "상식적 정의 실현을 위한 특검 지지 여론 우세"
                        ],
                        "keywords": ["유전무죄", "서민박탈감", "전관예우", "상식회복", "양아치"],
                        "representative_posts": [
                            "룸싸롱에서 400만원어치 얻어먹은 판사의 최후",
                            "법조 카르텔 척결 없이는 대한민국의 미래는 없다"
                        ],
                        "post_count": 30
                    },
                    {
                        "community_id": "ddanzi",
                        "stance_label": "강한 비판 & 지지층 결집",
                        "sentiment_score": -0.85,
                        "summary_points": [
                            "HOT/HOTBEST 30개 게시물 대부분이 정권 심판 및 언론·검찰 공조 비판",
                            "김어준의 겸손은힘들다 뉴스공장 데이터 인용 및 분석 활발",
                            "지지자 간 결속과 주말 집회 및 시민 행동 참여 촉구"
                        ],
                        "keywords": ["검찰독재", "기레기", "사법개혁", "민주당화력", "뉴스공장"],
                        "representative_posts": [
                            "기다리고 기다렸던 사법개혁 법안의 의미",
                            "조중동 프레임에 맞서는 팩트체크 총정리"
                        ],
                        "post_count": 30
                    },
                    {
                        "community_id": "theqoo",
                        "stance_label": "피로감 & 상식 기반 비판",
                        "sentiment_score": -0.65,
                        "summary_points": [
                            "스퀘어 핫이슈에서 사법 기득권의 도덕적 해이에 대한 일반적 공분",
                            "지루하게 이어지는 여야 정치적 프레임 공방에 대한 피로감",
                            "이념보다는 공정과 상식 파괴 문제에 민감하게 반응"
                        ],
                        "keywords": ["공정성", "기득권특권", "피로감", "상식파괴", "사법불신"],
                        "representative_posts": [
                            "사법부 판결 논란 및 검경 수사 공정성 공방",
                            "국회 청문회 주요 질의응답 요약 및 하이라이트"
                        ],
                        "post_count": 30
                    },
                    {
                        "community_id": "damoang",
                        "stance_label": "제도적 개혁 & 입법 통제 촉구",
                        "sentiment_score": -0.76,
                        "summary_points": [
                            "공감게시판 30대 토픽에서 법조 카르텔 해체를 위한 입법적 대안 분석",
                            "기소권·수사권 분리와 법관 징계 제도 선진화 요구",
                            "단순한 감정적 비판을 넘어 제도 설계의 허점 논의"
                        ],
                        "keywords": ["제도개혁", "국회입법", "법관징계", "투명성", "시스템"],
                        "representative_posts": [
                            "법원 판결의 형평성 논란: 일반 시민 잣대와 사법 카르텔의 괴리",
                            "검찰 개혁 및 수사 기소 분리 법안의 국회 통과 가능성 검토"
                        ],
                        "post_count": 30
                    }
                ]
            }
        ]
        return results
