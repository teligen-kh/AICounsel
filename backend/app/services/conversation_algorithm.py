import re
import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum
import random

class IntentType(Enum):
    """사용자 의도 타입"""
    GREETING = "greeting"  # 인사
    QUESTION = "question"  # 질문
    COMPLAINT = "complaint"  # 불만/문제
    REQUEST = "request"  # 요청
    THANKS = "thanks"  # 감사
    UNKNOWN = "unknown"  # 알 수 없음

class ConversationAlgorithm:
    """대화 알고리즘 관리 클래스"""
    
    def __init__(self):
        self.greeting_patterns = [
            r"안녕하세요", r"안녕", r"하이", r"반갑습니다", r"좋은 하루", r"좋은 날씨"
        ]
        
        self.question_patterns = [
            r"어떻게", r"무엇", r"언제", r"어디서", r"왜", r"어떤", r"몇", r"얼마"
        ]
        
        self.complaint_patterns = [
            r"안되요", r"안돼요", r"안됩니다", r"문제", r"오류", r"에러", r"고장", 
            r"작동안함", r"안됨", r"안돼", r"안되", r"안돼", r"안됨", r"안되", r"안돼",
            r"느린데", r"느려요", r"느립니다", r"느려", r"속도", r"해결해줘", r"해결해주세요",
            r"도와주세요", r"도움", r"부탁", r"요청", r"원해요", r"하고 싶어요"
        ]
        
        self.thanks_patterns = [
            r"감사합니다", r"고맙습니다", r"고마워요", r"감사해요", r"고마워", r"감사"
        ]
        
        self.request_patterns = [
            r"도와주세요", r"도움", r"부탁", r"요청", r"원해요", r"하고 싶어요"
        ]
        
        # 상품 관련 키워드
        self.product_keywords = [
            "상품", "제품", "물건", "아이템", "상품검색", "상품 조회", "상품 찾기", "상품코드", "코드"
        ]
        
        # 포스 관련 키워드
        self.pos_keywords = [
            "포스", "POS", "키오스크", "터치", "터치스크린", "화면", "버튼"
        ]
        
        # 프린터 관련 키워드
        self.printer_keywords = [
            "프린터", "인쇄", "영수증", "출력", "프린트", "단말기", "카드", "카드단말기", "카드 영수증"
        ]
        
        # 네트워크 관련 키워드
        self.network_keywords = [
            "인터넷", "네트워크", "연결", "와이파이", "WiFi", "통신", "접속"
        ]

    def analyze_intent(self, message: str) -> IntentType:
        """사용자 메시지의 의도를 분석합니다."""
        message_lower = message.lower().strip()
        
        # 숫자 응답 확인 (1, 2, 3, 4 등)
        if message_lower in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']:
            return IntentType.QUESTION  # 질문에 대한 답변으로 분류
        
        # 인사 패턴 확인
        for pattern in self.greeting_patterns:
            if re.search(pattern, message_lower):
                return IntentType.GREETING
        
        # 감사 패턴 확인
        for pattern in self.thanks_patterns:
            if re.search(pattern, message_lower):
                return IntentType.THANKS
        
        # 불만/문제 패턴 확인 (가장 우선순위가 높음)
        complaint_found = False
        for pattern in self.complaint_patterns:
            if re.search(pattern, message_lower):
                complaint_found = True
                break
        
        if complaint_found:
            return IntentType.COMPLAINT
        
        # 질문 패턴 확인
        for pattern in self.question_patterns:
            if re.search(pattern, message_lower):
                return IntentType.QUESTION
        
        # 요청 패턴 확인
        for pattern in self.request_patterns:
            if re.search(pattern, message_lower):
                return IntentType.REQUEST
        
        return IntentType.UNKNOWN

    def extract_keywords(self, message: str) -> List[str]:
        """메시지에서 키워드를 추출합니다."""
        keywords = []
        message_lower = message.lower()
        
        # 각 카테고리별 키워드 확인
        for keyword in self.product_keywords:
            if keyword in message_lower:
                keywords.append("상품")
                break
        
        for keyword in self.pos_keywords:
            if keyword in message_lower:
                keywords.append("포스")
                break
        
        for keyword in self.printer_keywords:
            if keyword in message_lower:
                keywords.append("프린터")
                break
        
        for keyword in self.network_keywords:
            if keyword in message_lower:
                keywords.append("네트워크")
                break
        
        return keywords

    def _generate_greeting_response(self) -> str:
        """인사에 대한 응답을 생성합니다."""
        responses = [
            "안녕하세요! 무엇을 도와드릴까요?",
            "안녕하세요! 어떤 도움이 필요하신가요?",
            "안녕하세요! 궁금한 점이 있으시면 언제든 말씀해 주세요."
        ]
        return random.choice(responses)

    def _generate_complaint_response(self, message: str, keywords: List[str]) -> str:
        """불만에 대한 응답을 생성합니다."""
        if keywords:
            return f"'{', '.join(keywords[:3])}' 관련 문제를 해결해드리겠습니다. 구체적으로 어떤 상황인지 알려주시면 더 정확한 도움을 드릴 수 있습니다."
        else:
            return "문제 상황을 구체적으로 설명해 주시면 해결 방법을 찾아드리겠습니다."

    def _generate_question_response(self, message: str, keywords: List[str]) -> str:
        """질문에 대한 응답을 생성합니다."""
        if keywords:
            return f"'{', '.join(keywords[:3])}'에 대해 답변드리겠습니다. 더 자세한 정보가 필요하시면 말씀해 주세요."
        else:
            return "질문하신 내용에 대해 답변드리겠습니다. 추가로 궁금한 점이 있으시면 언제든 말씀해 주세요."

    def _generate_thanks_response(self) -> str:
        """감사에 대한 응답을 생성합니다."""
        return "천만에요! 다른 도움이 필요하시면 언제든 말씀해 주세요."

    def _generate_request_response(self, message: str, keywords: List[str]) -> str:
        """요청에 대한 응답을 생성합니다."""
        if keywords:
            return f"'{', '.join(keywords[:3])}' 관련 요청을 처리해드리겠습니다. 구체적인 내용을 알려주시면 더 정확하게 도와드릴 수 있습니다."
        else:
            return "요청하신 내용을 처리해드리겠습니다. 추가 정보가 필요하시면 말씀해 주세요."

    def _generate_general_response(self, message: str, keywords: List[str]) -> str:
        """일반적인 응답을 생성합니다."""
        if keywords:
            return f"'{', '.join(keywords[:3])}'에 대해 도움을 드리겠습니다. 더 구체적으로 말씀해 주시면 정확한 답변을 드릴 수 있습니다."
        else:
            return "무엇을 도와드릴까요? 구체적으로 말씀해 주시면 정확한 답변을 드리겠습니다."

    def generate_unknown_response(self, message: str) -> str:
        """알 수 없는 의도에 대한 응답을 생성합니다."""
        return """죄송합니다. 말씀하신 내용을 정확히 이해하지 못했습니다.

다시 한 번 구체적으로 말씀해 주세요:

1. "포스 문제가 있어요"
2. "상품 검색이 안돼요"
3. "프린터가 안돼요"
4. "인터넷 연결이 안돼요"
5. "시스템 사용법을 알려주세요"

어떤 도움이 필요하신지 말씀해 주시면 정확한 답변을 드리겠습니다.

만약 제가 도움을 드릴 수 없는 문제라면, 전문 상담사분들께 전달해서 연락 드리도록 하겠습니다."""

    def generate_no_answer_response(self, message: str) -> str:
        """답변을 찾지 못했을 때의 응답을 생성합니다."""
        return """죄송합니다. 현재 제가 도움을 드릴 수 없을 것 같습니다.

전문 상담사분들께 전달해서 연락 드리도록 하겠습니다.

연락처와 업체명을 남겨 주시겠습니까?

또는 다른 문제가 있으시면 언제든 말씀해 주세요."""

    async def generate_response(self, user_message: str, db_answer: str = None, model = None, tokenizer = None) -> str:
        """
        사용자 메시지에 대한 응답을 생성합니다.
        
        Args:
            user_message: 사용자 메시지
            db_answer: DB에서 찾은 답변 (선택사항)
            model: LLM 모델 (선택사항)
            tokenizer: 토크나이저 (선택사항)
            
        Returns:
            생성된 응답
        """
        try:
            # 1. 의도 분석
            intent = self.analyze_intent(user_message)
            
            # 2. 키워드 추출
            keywords = self.extract_keywords(user_message)
            
            # 3. DB 답변이 있는 경우 우선 사용
            if db_answer:
                return self._format_db_answer(db_answer, user_message)
            
            # 4. 의도별 응답 생성
            if intent == IntentType.GREETING:
                return self._generate_greeting_response()
            elif intent == IntentType.COMPLAINT:
                return self._generate_complaint_response(user_message, keywords)
            elif intent == IntentType.QUESTION:
                return self._generate_question_response(user_message, keywords)
            elif intent == IntentType.THANKS:
                return self._generate_thanks_response()
            elif intent == IntentType.REQUEST:
                return self._generate_request_response(user_message, keywords)
            else:
                return self._generate_general_response(user_message, keywords)
                
        except Exception as e:
            logging.error(f"Error in conversation algorithm: {str(e)}")
            return "죄송합니다. 일시적인 오류가 발생했습니다. 다시 한 번 말씀해 주시겠어요?"

    def _format_db_answer(self, db_answer: str, user_message: str) -> str:
        """DB 답변을 포맷팅합니다."""
        try:
            # 기본 정리
            response = db_answer.strip()
            
            # 줄바꿈 개선
            response = response.replace('\\n', '\n')
            response = response.replace('  ', '\n')  # 두 개 이상의 공백을 줄바꿈으로
            response = response.replace('* ', '\n• ')  # 불릿 포인트 개선
            response = response.replace('1. ', '\n1. ')  # 번호 매기기 개선
            response = response.replace('2. ', '\n2. ')
            response = response.replace('3. ', '\n3. ')
            response = response.replace('4. ', '\n4. ')
            
            # 응답 길이 제한 (문자 수 기준)
            if len(response) > 400:  # 400자로 제한
                response = response[:400] + "..."
            
            # 불필요한 줄바꿈 정리
            response = '\n'.join(line.strip() for line in response.split('\n') if line.strip())
            
            return response
            
        except Exception as e:
            logging.error(f"Error formatting DB answer: {str(e)}")
            return db_answer 