import re
from typing import Dict, List, Tuple, Optional
from enum import Enum

class InputType(Enum):
    """입력 타입 분류"""
    GREETING = "greeting"           # 인사말
    CASUAL = "casual"              # 일상 대화
    TECHNICAL = "technical"        # 기술적 질문
    NON_COUNSELING = "non_counseling"  # 비상담 질문
    PROFANITY = "profanity"        # 욕설
    UNKNOWN = "unknown"            # 기타

class InputFilter:
    """사용자 입력 필터링 및 분류"""
    
    def __init__(self):
        self._initialize_patterns()
    
    def _initialize_patterns(self):
        """패턴 초기화"""
        # 인사말 패턴
        self.greeting_patterns = [
            r'안녕하세요', r'안녕', r'반갑습니다', r'반가워요',
            r'좋은 아침', r'좋은 오후', r'좋은 저녁', r'하이', r'hi', r'hello'
        ]
        
        # 일상 대화 패턴
        self.casual_patterns = [
            r'바쁘시죠', r'식사', r'점심', r'저녁', r'아침', r'커피', r'차',
            r'날씨', r'기분', r'피곤', r'힘드시', r'어떻게 지내', r'잘 지내',
            r'너는', r'당신은', r'ai', r'인공지능', r'로봇'
        ]
        
        # 기술적 질문 패턴
        self.technical_patterns = [
            r'설치', r'설정', r'오류', r'에러', r'문제', r'해결', r'방법',
            r'프로그램', r'소프트웨어', r'하드웨어', r'기기', r'장비',
            r'스캐너', r'프린터', r'포스', r'pos', r'시스템', r'네트워크',
            r'연결', r'인터넷', r'데이터', r'백업', r'복구', r'업데이트'
        ]
        
        # 비상담 질문 패턴 (역사, 지리, 일반 지식 등)
        self.non_counseling_patterns = [
            r'한국', r'대한민국', r'독도', r'일본', r'중국', r'미국', r'영국',
            r'역사', r'지리', r'수도', r'인구', r'면적', r'언어', r'문화',
            r'정치', r'경제', r'사회', r'과학', r'수학', r'물리', r'화학',
            r'생물', r'천문', r'지구', r'달', r'태양', r'별', r'우주',
            r'음식', r'요리', r'레시피', r'영화', r'드라마', r'음악', r'노래',
            r'운동', r'스포츠', r'축구', r'야구', r'농구', r'테니스',
            r'여행', r'관광', r'호텔', r'항공', r'기차', r'버스',
            r'의학', r'병원', r'약', r'질병', r'건강', r'다이어트',
            r'작가', r'소설', r'책', r'문학', r'시', r'시인', r'화가', r'미술',
            r'연예인', r'배우', r'가수', r'아이돌', r'유명인', r'스타',
            r'날씨', r'기후', r'온도', r'비', r'눈', r'바람', r'습도',
            r'요즘', r'최근', r'트렌드', r'유행', r'인기', r'핫', r'화제',
            r'뉴스', r'신문', r'방송', r'미디어', r'인터넷', r'SNS',
            r'학교', r'대학', r'학생', r'선생님', r'교육', r'공부', r'시험',
            r'직업', r'회사', r'직장', r'사장', r'부장', r'과장', r'대리',
            r'취미', r'관심사', r'좋아하는', r'싫어하는', r'선호', r'취향'
        ]
        
        # 욕설 패턴
        self.profanity_patterns = [
            r'바보', r'멍청', r'똥', r'개', r'새끼', r'씨발', r'병신',
            r'미친', r'미쳤', r'돌았', r'정신', r'빡', r'빡치', r'열받',
            r'짜증', r'화나', r'열받', r'빡돌', r'돌았', r'미쳤',
            r'fuck', r'shit', r'damn', r'bitch', r'ass', r'idiot', r'stupid'
        ]
    
    def classify_input(self, user_input: str) -> Tuple[InputType, Dict[str, any]]:
        """사용자 입력을 분류하고 결과 반환"""
        input_lower = user_input.lower().strip()
        
        # 욕설 체크 (가장 우선순위)
        if self._contains_profanity(input_lower):
            return InputType.PROFANITY, {
                "reason": "욕설 감지",
                "matched_words": self._find_matched_words(input_lower, self.profanity_patterns)
            }
        
        # 비상담 질문 체크
        if self._is_non_counseling(input_lower):
            return InputType.NON_COUNSELING, {
                "reason": "상담 범위 외 질문",
                "matched_words": self._find_matched_words(input_lower, self.non_counseling_patterns)
            }
        
        # 인사말 체크
        if self._is_greeting(input_lower):
            return InputType.GREETING, {
                "reason": "인사말 감지",
                "matched_words": self._find_matched_words(input_lower, self.greeting_patterns)
            }
        
        # 기술적 질문 체크
        if self._is_technical(input_lower):
            return InputType.TECHNICAL, {
                "reason": "기술적 질문",
                "matched_words": self._find_matched_words(input_lower, self.technical_patterns)
            }
        
        # 일상 대화 체크
        if self._is_casual(input_lower):
            return InputType.CASUAL, {
                "reason": "일상 대화",
                "matched_words": self._find_matched_words(input_lower, self.casual_patterns)
            }
        
        # 기타
        return InputType.UNKNOWN, {"reason": "분류 불가"}
    
    def _contains_profanity(self, text: str) -> bool:
        """욕설 포함 여부 확인"""
        return any(re.search(pattern, text) for pattern in self.profanity_patterns)
    
    def _is_non_counseling(self, text: str) -> bool:
        """비상담 질문 여부 확인"""
        return any(re.search(pattern, text) for pattern in self.non_counseling_patterns)
    
    def _is_greeting(self, text: str) -> bool:
        """인사말 여부 확인"""
        return any(re.search(pattern, text) for pattern in self.greeting_patterns)
    
    def _is_technical(self, text: str) -> bool:
        """기술적 질문 여부 확인"""
        return any(re.search(pattern, text) for pattern in self.technical_patterns)
    
    def _is_casual(self, text: str) -> bool:
        """일상 대화 여부 확인"""
        return any(re.search(pattern, text) for pattern in self.casual_patterns)
    
    def _find_matched_words(self, text: str, patterns: List[str]) -> List[str]:
        """매칭된 단어들 찾기"""
        matched = []
        for pattern in patterns:
            if re.search(pattern, text):
                matched.append(pattern)
        return matched
    
    def get_response_template(self, input_type: InputType, company_name: str = "텔리젠") -> str:
        """입력 타입에 따른 응답 템플릿 반환"""
        templates = {
            InputType.GREETING: "안녕하세요! 어떻게 도와드릴까요?",
            InputType.CASUAL: "네, 편안하게 말씀해 주세요. 무엇을 도와드릴까요?",
            InputType.TECHNICAL: "기술적 문제에 대해 도움을 드리겠습니다. 구체적으로 어떤 문제인지 알려주세요.",
            InputType.NON_COUNSELING: f"저는 {company_name} AI 상담사로 해당 질문은 상담 범위를 벗어나 답변 드릴 수 없습니다.",
            InputType.PROFANITY: "욕설을 하시면 응대를 할 수 없습니다. 30분 후 재문의 바랍니다.",
            InputType.UNKNOWN: "어떤 도움이 필요하신가요?"
        }
        return templates.get(input_type, "어떤 도움이 필요하신가요?")

# 전역 인스턴스
_input_filter: Optional[InputFilter] = None

def get_input_filter() -> InputFilter:
    """입력 필터 인스턴스 반환"""
    global _input_filter
    if _input_filter is None:
        _input_filter = InputFilter()
    return _input_filter 