import re
import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum
import random
import torch

class IntentType(Enum):
    """사용자 의도 타입"""
    CASUAL = "casual"  # 일상 대화
    PROFESSIONAL = "professional"  # 전문 상담
    GREETING = "greeting"  # 인사
    QUESTION = "question"  # 질문
    COMPLAINT = "complaint"  # 불만/문제
    REQUEST = "request"  # 요청
    THANKS = "thanks"  # 감사
    UNKNOWN = "unknown"  # 알 수 없음

class ConversationAlgorithm:
    """고객 응대 알고리즘 관리 클래스"""
    
    def __init__(self):
        # 일상 대화 패턴 (LLaMA 3.1 8B가 처리)
        self.casual_patterns = [
            r"안녕하세요", r"안녕", r"하이", r"반갑습니다", r"좋은 하루", r"좋은 날씨",
            r"좋아요", r"좋습니다", r"좋네요", r"좋아", r"좋다", r"좋은", r"좋은데",
            r"오늘", r"날씨", r"날씨가", r"날씨는", r"날씨도", r"날씨를",
            r"감사합니다", r"고맙습니다", r"고마워요", r"감사해요", r"고마워", r"감사",
            r"고생하세요", r"수고하세요", r"수고해요", r"고생해요", r"고생", r"수고",
            r"잘가요", r"안녕히가세요", r"안녕히계세요", r"잘있어요", r"잘있어",
            r"그래요", r"그래", r"네", r"응", r"어", r"아", r"오", r"우",
            r"재미있어요", r"재미있네요", r"재미있어", r"재미있다", r"재미있는",
            r"힘내세요", r"힘내요", r"힘내", r"화이팅", r"파이팅", r"화이팅!", r"파이팅!"
        ]
        
        # 전문 상담 패턴 (MongoDB 검색 후 LLaMA 정리)
        self.professional_patterns = [
            r"프린터", r"인쇄", r"영수증", r"출력", r"프린트", r"단말기", r"카드", r"카드단말기",
            r"포스", r"POS", r"키오스크", r"터치", r"터치스크린", r"화면", r"버튼",
            r"설치", r"재설치", r"설정", r"설정법", r"설정방법", r"설치법", r"설치방법",
            r"오류", r"에러", r"문제", r"고장", r"작동안함", r"안됨", r"안돼", r"안되",
            r"느린데", r"느려요", r"느립니다", r"느려", r"속도", r"해결", r"해결해줘",
            r"도와주세요", r"도움", r"부탁", r"요청", r"원해요", r"하고 싶어요",
            r"상품", r"제품", r"물건", r"아이템", r"상품검색", r"상품 조회", r"상품 찾기",
            r"인터넷", r"네트워크", r"연결", r"와이파이", r"WiFi", r"통신", r"접속",
            r"DB", r"데이터베이스", r"데이터", r"저장", r"백업", r"복원", r"삭제",
            r"로그인", r"로그아웃", r"회원가입", r"비밀번호", r"아이디", r"계정",
            r"결제", r"결제오류", r"결제실패", r"결제안됨", r"결제안돼", r"결제안되",
            r"환불", r"취소", r"교환", r"반품", r"환불요청", r"취소요청",
            r"업데이트", r"업그레이드", r"다운로드", r"업로드", r"동기화",
            r"메뉴", r"기능", r"사용법", r"사용방법", r"이용법", r"이용방법",
            r"매뉴얼", r"매뉴얼", r"가이드", r"도움말", r"헬프", r"help"
        ]
        
        # 질문 패턴
        self.question_patterns = [
            r"어떻게", r"무엇", r"언제", r"어디서", r"왜", r"어떤", r"몇", r"얼마",
            r"무엇인가요", r"어떻게 하나요", r"어떻게 해요", r"어떻게 하죠",
            r"무엇입니까", r"어떻게 됩니까", r"어떻게 됩니다", r"어떻게 됩니다까"
        ]
        
        # 불만/문제 패턴
        self.complaint_patterns = [
            r"안되요", r"안돼요", r"안됩니다", r"문제", r"오류", r"에러", r"고장", 
            r"작동안함", r"안됨", r"안돼", r"안되", r"안돼", r"안됨", r"안되", r"안돼",
            r"느린데", r"느려요", r"느립니다", r"느려", r"속도", r"해결해줘", r"해결해주세요",
            r"도와주세요", r"도움", r"부탁", r"요청", r"원해요", r"하고 싶어요"
        ]
        
        # 요청 패턴
        self.request_patterns = [
            r"도와주세요", r"도움", r"부탁", r"요청", r"원해요", r"하고 싶어요"
        ]
        
        # 감사 패턴
        self.thanks_patterns = [
            r"감사합니다", r"고맙습니다", r"고마워요", r"감사해요", r"고마워", r"감사"
        ]

    def classify_conversation_type(self, message: str) -> str:
        """
        고객 입력을 일상 대화와 전문 상담으로 분류합니다.
        
        Args:
            message: 고객 메시지
            
        Returns:
            "casual" (일상 대화) 또는 "professional" (전문 상담)
        """
        message_lower = message.lower().strip()
        
        # 전문 상담 패턴 확인 (우선순위 높음)
        for pattern in self.professional_patterns:
            if re.search(pattern, message_lower):
                logging.info(f"Professional conversation detected: {message[:50]}...")
                return "professional"
        
        # 일상 대화 패턴 확인
        for pattern in self.casual_patterns:
            if re.search(pattern, message_lower):
                logging.info(f"Casual conversation detected: {message[:50]}...")
                return "casual"
        
        # 질문 패턴이 있으면 전문 상담으로 분류
        for pattern in self.question_patterns:
            if re.search(pattern, message_lower):
                logging.info(f"Question pattern detected - Professional: {message[:50]}...")
                return "professional"
        
        # 기본값: 전문 상담 (안전한 선택)
        logging.info(f"Default to professional conversation: {message[:50]}...")
        return "professional"

    def analyze_intent(self, message: str) -> IntentType:
        """사용자 메시지의 의도를 분석합니다."""
        message_lower = message.lower().strip()
        
        # 숫자 응답 확인 (1, 2, 3, 4 등)
        if message_lower in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']:
            return IntentType.QUESTION  # 질문에 대한 답변으로 분류
        
        # 인사 패턴 확인
        for pattern in self.casual_patterns:
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
        
        # 전문 상담 키워드 추출
        for pattern in self.professional_patterns:
            if re.search(pattern, message_lower):
                keywords.append(pattern)
        
        return keywords[:5]  # 상위 5개만 반환

    def _generate_casual_response(self, message: str) -> str:
        """일상 대화에 대한 응답을 생성합니다."""
        message_lower = message.lower()
        
        # AI/사람 관련 질문 응답
        if any(word in message_lower for word in ['ai', '사람', '인간', '봇', '봇이', '봇인', '봇이야', '봇이에요']):
            responses = [
                "안녕하세요! 저는 AI 상담사입니다. 알파문구 포스 시스템과 관련된 질문에 답변해드릴 수 있어요. 어떤 도움이 필요하신가요?",
                "안녕하세요! 저는 AI 상담사입니다. 포스 시스템 사용 중 궁금한 점이나 문제가 있으시면 언제든 말씀해 주세요.",
                "안녕하세요! 저는 AI 상담사입니다. 알파문구 포스 프로그램과 관련된 상담을 도와드리고 있어요. 무엇을 도와드릴까요?"
            ]
            return random.choice(responses)
        
        # 인사 응답
        if any(word in message_lower for word in ['안녕', '하이', '반갑']):
            responses = [
                "안녕하세요! 반갑습니다. 어떻게 도와드릴까요?",
                "안녕하세요! 어떤 도움이 필요하신가요?",
                "안녕하세요! 궁금한 점이 있으시면 언제든 말씀해 주세요."
            ]
            return random.choice(responses)
        
        # 감사 응답
        if any(word in message_lower for word in ['감사', '고맙', '고마워']):
            responses = [
                "천만에요! 다른 도움이 필요하시면 언제든 말씀해 주세요.",
                "별 말씀을요! 더 궁금한 거 있으세요?",
                "도움이 되어서 기쁩니다! 다른 질문이 있으시면 언제든 말씀해 주세요."
            ]
            return random.choice(responses)
        
        # 긍정적 반응
        if any(word in message_lower for word in ['좋아', '좋은', '좋다', '좋네']):
            responses = [
                "좋은 소식이에요! 더 궁금한 거 있으세요?",
                "다행이네요! 다른 도움이 필요하시면 언제든 말씀해 주세요.",
                "기쁘네요! 더 도움이 될 수 있는 게 있나요?"
            ]
            return random.choice(responses)
        
        # 기본 응답
        responses = [
            "무엇을 도와드릴까요?",
            "어떤 도움이 필요하신가요?",
            "궁금한 점이 있으시면 언제든 말씀해 주세요."
        ]
        return random.choice(responses)

    def _generate_professional_response(self, message: str, db_answers: List[str] = None) -> str:
        """전문 상담에 대한 응답을 생성합니다."""
        if not db_answers or len(db_answers) == 0:
            return "상담사에게 문의하시겠습니까? 저희 상담사에게 연락하여 도움을 받을 수 있습니다."
        
        if len(db_answers) == 1:
            # 단일 답변이 있는 경우
            return f"{db_answers[0]}\n\n도움이 되셨나요? 다른 질문이 있으시면 언제든 말씀해 주세요."
        
        # 여러 답변이 있는 경우 - LLaMA가 정리하도록 안내
        response = f"관련 답변을 찾았습니다. 구체적으로 어떤 상황인지 알려주시면 더 정확한 답변을 드릴 수 있습니다:\n\n"
        
        for i, answer in enumerate(db_answers[:3], 1):  # 최대 3개까지만
            response += f"{i}. {answer[:100]}...\n"
        
        response += "\n위 중에서 어떤 상황에 해당하시나요? 번호를 말씀해 주시거나 구체적으로 설명해 주시면 더 정확한 답변을 드리겠습니다."
        
        return response

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
        고객 응대 알고리즘에 따른 응답을 생성합니다.
        
        Args:
            user_message: 사용자 메시지
            db_answer: DB에서 찾은 답변
            model: LLaMA 3.1 8B 모델
            tokenizer: 토크나이저
            
        Returns:
            생성된 응답
        """
        try:
            # 1. 대화 유형 분류
            conversation_type = self.classify_conversation_type(user_message)
            
            # 2. 일상 대화 처리 (LLaMA 3.1 8B)
            if conversation_type == "casual":
                logging.info("Processing casual conversation with LLaMA")
                if model and tokenizer:
                    return await self._generate_llama_casual_response(user_message, model, tokenizer)
                else:
                    return self._generate_casual_response(user_message)
            
            # 3. 전문 상담 처리 (MongoDB + LLaMA 정리)
            else:
                logging.info("Processing professional conversation with MongoDB + LLaMA")
                if db_answer:
                    # DB 답변이 있는 경우 LLaMA로 친절하게 정리
                    if model and tokenizer:
                        return await self._generate_llama_professional_response(user_message, db_answer, model, tokenizer)
                    else:
                        return self._format_db_answer(db_answer, user_message)
                else:
                    # DB 답변이 없는 경우 상담사 연락 안내
                    return self.generate_no_answer_response(user_message)
                    
        except Exception as e:
            logging.error(f"Error in generate_response: {str(e)}")
            return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    async def _generate_llama_casual_response(self, message: str, model, tokenizer, config=None) -> str:
        """LLaMA 3.1 8B로 일상 대화 응답 생성"""
        try:
            # 토크나이저 설정
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # 모델 설정 가져오기
            max_tokens = config.max_tokens if config else 20
            temperature = config.temperature if config else 0.3
            
            # 간단한 입력 형식 사용
            conversation_text = message
            
            # 모델에 직접 입력 (attention_mask 명시적 설정)
            inputs = tokenizer(
                conversation_text, 
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=64  # 128에서 64로 더 줄임
            )
            
            # 생성 (토큰 수 줄이고 파라미터 최적화)
            with torch.no_grad():
                outputs = model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.7,  # 0.8에서 0.7로 줄임
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    repetition_penalty=1.02,  # 1.05에서 1.02로 줄임
                    early_stopping=True,
                    num_beams=1,  # 빔 서치 비활성화로 속도 향상
                    use_cache=True  # 캐시 사용으로 속도 향상
                )
            
            # 응답 후처리 (간단하게)
            response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            response = response.strip()
            
            # 응답 클리닝 (간단하게)
            response = self._clean_llama_response(response)
            
            return response if response else self._generate_casual_response(message)
            
        except Exception as e:
            logging.error(f"Error in LLaMA casual response: {str(e)}")
            return self._generate_casual_response(message)

    async def _generate_llama_professional_response(self, message: str, db_answer: str, model, tokenizer, config=None) -> str:
        """LLaMA 3.1 8B로 전문 상담 응답 생성"""
        try:
            # 토크나이저 설정
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # 모델 설정 가져오기
            max_tokens = config.max_tokens if config else 20
            temperature = config.temperature if config else 0.3
            
            # 간단한 입력 형식 사용
            conversation_text = message
            
            # 모델에 직접 입력 (attention_mask 명시적 설정)
            inputs = tokenizer(
                conversation_text, 
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=64  # 128에서 64로 더 줄임
            )
            
            # 생성 (토큰 수 줄이고 파라미터 최적화)
            with torch.no_grad():
                outputs = model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.7,  # 0.8에서 0.7로 줄임
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    repetition_penalty=1.02,  # 1.05에서 1.02로 줄임
                    early_stopping=True,
                    num_beams=1,  # 빔 서치 비활성화로 속도 향상
                    use_cache=True  # 캐시 사용으로 속도 향상
                )
            
            # 응답 후처리 (간단하게)
            response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            response = response.strip()
            
            # 응답 클리닝 (간단하게)
            response = self._clean_llama_response(response)
            
            return response if response else self._format_db_answer(db_answer, message)
            
        except Exception as e:
            logging.error(f"Error in LLaMA professional response: {str(e)}")
            return self._format_db_answer(db_answer, message)

    def _clean_llama_response(self, response: str) -> str:
        """LLaMA 응답을 간단하게 클리닝합니다."""
        try:
            # 특수 태그 제거
            response = response.replace("<|im_end|>", "").replace("<|im_start|>", "")
            response = response.replace("<|endoftext|>", "")
            
            # 앞뒤 공백 제거
            response = response.strip()
            
            # 빈 응답 체크
            if not response or response.isspace():
                return ""
            
            # 응답 길이 제한 (150자)
            if len(response) > 150:
                response = response[:150] + "..."
            
            return response
            
        except Exception as e:
            logging.error(f"Error cleaning LLaMA response: {str(e)}")
            return response

    def _format_db_answer(self, db_answer: str, user_message: str) -> str:
        """DB 답변을 사용자 친화적으로 포맷팅합니다."""
        try:
            # 기본 포맷팅
            formatted = db_answer.strip()
            
            # 사용자 질문과 연결
            response = f"{formatted}\n\n도움이 되셨나요? 다른 질문이 있으시면 언제든 말씀해 주세요."
            
            return response
            
        except Exception as e:
            logging.error(f"Error formatting DB answer: {str(e)}")
            return db_answer 