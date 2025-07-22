"""
강화된 입력 분류기 모듈
키워드 추출 + LLM 의도 분석을 결합한 고정확도 입력 분류 시스템
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum
import asyncio
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os

# soynlp 키워드 추출 라이브러리 임포트 (선택적)
try:
    from soynlp.word import WordExtractor
    from soynlp.tokenizer import LTokenizer
    SOYNLP_AVAILABLE = True
except ImportError:
    SOYNLP_AVAILABLE = False
    logging.warning("soynlp가 설치되지 않았습니다. 기본 키워드 추출을 사용합니다.")

class EnhancedInputType(Enum):
    """
    강화된 입력 타입 분류 열거형
    사용자 입력을 5가지 카테고리로 분류
    """
    GREETING_CASUAL = "greeting_casual"    # 인사/일상 대화
    TECHNICAL = "technical"                # 전문 상담 질문
    NON_COUNSELING = "non_counseling"      # 비상담 범위 질문
    PROFANITY = "profanity"                # 욕설/비속어
    UNKNOWN = "unknown"                    # 기타/분류 불가

class EnhancedInputClassifier:
    """
    강화된 입력 분류기 클래스
    키워드 추출과 LLM 의도 분석을 결합하여 높은 정확도의 입력 분류 제공
    """
    
    def __init__(self):
        """
        강화된 입력 분류기 초기화
        패턴, LLM 모델, 키워드 추출기를 순차적으로 초기화
        """
        self._initialize_patterns()      # 키워드 패턴 초기화
        self._initialize_llm()           # LLM 모델 초기화
        self._initialize_keyword_extractor()  # 키워드 추출기 초기화
        
    def _initialize_patterns(self):
        """
        기본 키워드 패턴 초기화
        각 분류별 키워드 리스트를 설정하여 기본 분류 기준 제공
        """
        # 인사/일상 대화 관련 키워드
        self.greeting_casual_keywords = [
            "안녕", "반갑", "하이", "hello", "hi",
            "바쁘", "식사", "점심", "저녁", "아침", "커피", "차",
            "날씨", "기분", "피곤", "힘드", "어떻게 지내", "잘 지내",
            "너는", "당신은", "ai", "인공지능", "로봇"
        ]
        
        # 전문 상담 키워드
        self.technical_keywords = [
            "포스", "pos", "설치", "설정", "오류", "에러", "문제", "해결", "방법",
            "프로그램", "소프트웨어", "하드웨어", "기기", "장비",
            "스캐너", "프린터", "시스템", "네트워크", "연결", "인터넷",
            "데이터", "백업", "복구", "업데이트", "단말기", "카드", "결제"
        ]
        
        # 비상담 키워드
        self.non_counseling_keywords = [
            "한국", "대한민국", "독도", "일본", "중국", "미국", "영국",
            "역사", "지리", "수도", "인구", "면적", "언어", "문화",
            "정치", "경제", "사회", "과학", "수학", "물리", "화학",
            "생물", "천문", "지구", "달", "태양", "별", "우주",
            "음식", "요리", "레시피", "영화", "드라마", "음악", "노래",
            "운동", "스포츠", "축구", "야구", "농구", "테니스",
            "여행", "관광", "호텔", "항공", "기차", "버스",
            "의학", "병원", "약", "질병", "건강", "다이어트"
        ]
        
        # 욕설 키워드
        self.profanity_keywords = [
            "바보", "멍청", "똥", "개", "새끼", "씨발", "병신",
            "미친", "미쳤", "돌았", "정신", "빡", "빡치", "열받",
            "짜증", "화나", "열받", "빡돌", "돌았", "미쳤",
            "fuck", "shit", "damn", "bitch", "ass", "idiot", "stupid"
        ]
    
    def _initialize_llm(self):
        """LLM 모델 초기화"""
        try:
            # 모델 경로 설정
            model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                    "models", "Llama-3.1-8B-Instruct")
            
            if os.path.exists(model_path):
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True
                )
                self.llm_available = True
                logging.info("✅ LLM 모델 로딩 완료")
            else:
                self.llm_available = False
                logging.warning("❌ LLM 모델을 찾을 수 없습니다. 키워드 기반 분류만 사용합니다.")
                
        except Exception as e:
            self.llm_available = False
            logging.error(f"LLM 모델 초기화 실패: {str(e)}")
    
    def _initialize_keyword_extractor(self):
        """키워드 추출기 초기화"""
        if SOYNLP_AVAILABLE:
            try:
                self.word_extractor = WordExtractor()
                self.tokenizer_l = LTokenizer()
                self.soynlp_available = True
                logging.info("✅ soynlp 키워드 추출기 초기화 완료")
            except Exception as e:
                self.soynlp_available = False
                logging.error(f"soynlp 초기화 실패: {str(e)}")
        else:
            self.soynlp_available = False
    
    def extract_keywords_soynlp(self, text: str) -> List[str]:
        """soynlp를 사용한 키워드 추출"""
        if not self.soynlp_available:
            return self.extract_keywords_basic(text)
        
        try:
            # soynlp 키워드 추출
            words = self.word_extractor.extract(text)
            scores = {word: score for word, score in words.items() if len(word) > 1}
            
            # 상위 키워드 추출
            sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            keywords = [word for word, score in sorted_words[:10]]
            
            return keywords
        except Exception as e:
            logging.error(f"soynlp 키워드 추출 실패: {str(e)}")
            return self.extract_keywords_basic(text)
    
    def extract_keywords_basic(self, text: str) -> List[str]:
        """기본 키워드 추출 (정규식 기반)"""
        # 한글, 영문, 숫자로 구성된 단어 추출
        words = re.findall(r'[가-힣a-zA-Z0-9]+', text.lower())
        # 2글자 이상, 10글자 이하 단어만 선택
        keywords = [word for word in words if 2 <= len(word) <= 10]
        return keywords[:10]
    
    async def classify_with_llm(self, text: str, keywords: List[str]) -> EnhancedInputType:
        """LLM을 사용한 의도 분류"""
        if not self.llm_available:
            return self.classify_with_keywords(text, keywords)
        
        try:
            # LLM 프롬프트 구성
            prompt = f"""다음 사용자 메시지를 분석하여 의도를 분류해주세요.

사용자 메시지: {text}
추출된 키워드: {', '.join(keywords[:5])}

분류 기준:
1. 인사/일상: 인사말, 일상적인 대화, AI/로봇 관련 질문
2. 전문: 포스, 설치, 설정, 오류, 문제 해결 등 기술적 질문
3. 비상담: 역사, 지리, 정치, 일반 지식 등 상담 범위 외 질문
4. 욕설: 비속어, 욕설, 공격적 표현

분류 결과만 출력하세요 (인사/일상, 전문, 비상담, 욕설 중 하나):"""

            # LLM 응답 생성
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=10,
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response.replace(prompt, "").strip()
            
            # 응답 파싱
            if "인사" in response or "일상" in response:
                return EnhancedInputType.GREETING_CASUAL
            elif "전문" in response:
                return EnhancedInputType.TECHNICAL
            elif "비상담" in response:
                return EnhancedInputType.NON_COUNSELING
            elif "욕설" in response:
                return EnhancedInputType.PROFANITY
            else:
                return EnhancedInputType.UNKNOWN
                
        except Exception as e:
            logging.error(f"LLM 분류 실패: {str(e)}")
            return self.classify_with_keywords(text, keywords)
    
    def classify_with_keywords(self, text: str, keywords: List[str]) -> EnhancedInputType:
        """키워드 기반 분류"""
        text_lower = text.lower()
        
        # 욕설 체크 (가장 우선순위)
        for keyword in self.profanity_keywords:
            if keyword in text_lower:
                return EnhancedInputType.PROFANITY
        
        # 비상담 체크
        for keyword in self.non_counseling_keywords:
            if keyword in text_lower:
                return EnhancedInputType.NON_COUNSELING
        
        # 전문 상담 체크
        for keyword in self.technical_keywords:
            if keyword in text_lower:
                return EnhancedInputType.TECHNICAL
        
        # 인사/일상 체크
        for keyword in self.greeting_casual_keywords:
            if keyword in text_lower:
                return EnhancedInputType.GREETING_CASUAL
        
        return EnhancedInputType.UNKNOWN
    
    async def classify_input(self, text: str) -> Tuple[EnhancedInputType, Dict[str, any]]:
        """강화된 입력 분류"""
        try:
            # 1. 키워드 추출
            keywords = self.extract_keywords_soynlp(text)
            logging.info(f"추출된 키워드: {keywords[:5]}")
            
            # 2. LLM 의도 분석
            input_type = await self.classify_with_llm(text, keywords)
            
            # 3. 결과 구성
            result = {
                "keywords": keywords[:5],
                "classification_method": "llm" if self.llm_available else "keywords",
                "confidence": "high" if self.llm_available else "medium"
            }
            
            logging.info(f"분류 결과: {input_type.value} (방법: {result['classification_method']})")
            
            return input_type, result
            
        except Exception as e:
            logging.error(f"입력 분류 실패: {str(e)}")
            # 기본 분류로 폴백
            input_type = self.classify_with_keywords(text, [])
            return input_type, {
                "keywords": [],
                "classification_method": "fallback",
                "confidence": "low",
                "error": str(e)
            }
    
    def get_response_template(self, input_type: EnhancedInputType, company_name: str = "텔리젠") -> str:
        """분류에 따른 응답 템플릿"""
        templates = {
            EnhancedInputType.GREETING_CASUAL: [
                f"안녕하세요! 저는 {company_name} AI 상담사입니다. 포스 시스템과 관련된 질문에 답변해드릴 수 있어요. 어떤 도움이 필요하신가요?",
                f"안녕하세요! {company_name} AI 상담사입니다. 포스 시스템 사용 중 궁금한 점이나 문제가 있으시면 언제든 말씀해 주세요.",
                f"안녕하세요! {company_name} AI 상담사입니다. 포스 프로그램과 관련된 상담을 도와드리고 있어요. 무엇을 도와드릴까요?"
            ],
            EnhancedInputType.TECHNICAL: [
                f"포스 시스템 관련 질문이시군요. 자세히 알아보겠습니다. 구체적으로 어떤 문제가 있으신가요?",
                f"기술적인 문제를 해결해드리겠습니다. 어떤 부분에서 어려움을 겪고 계신가요?",
                f"포스 시스템 사용 중 문제가 발생하셨군요. 정확한 상황을 알려주시면 도움을 드리겠습니다."
            ],
            EnhancedInputType.NON_COUNSELING: [
                f"죄송합니다. 저는 {company_name} AI 상담사로 해당 질문은 답변 드릴 수 없습니다. 포스 시스템과 관련된 질문에 답변해드릴 수 있어요.",
                f"해당 질문은 제가 답변할 수 있는 범위가 아닙니다. 포스 시스템 관련 상담을 도와드리고 있습니다.",
                f"죄송하지만 해당 주제에 대해서는 답변을 드릴 수 없습니다. 포스 시스템과 관련된 질문이 있으시면 언제든 말씀해 주세요."
            ],
            EnhancedInputType.PROFANITY: [
                f"욕설을 하시면 응대를 할 수 없습니다. 30분 후 재문의 바랍니다.",
                f"비속어나 욕설 사용 시 상담이 제한됩니다. 30분 후 다시 문의해 주세요.",
                f"공손한 언어로 대화해 주시기 바랍니다. 30분 후 재문의 바랍니다."
            ],
            EnhancedInputType.UNKNOWN: [
                f"안녕하세요! {company_name} AI 상담사입니다. 포스 시스템과 관련된 질문에 답변해드릴 수 있어요.",
                f"어떤 도움이 필요하신지 구체적으로 말씀해 주시면 더 정확한 답변을 드릴 수 있습니다.",
                f"포스 시스템 사용 중 궁금한 점이나 문제가 있으시면 언제든 말씀해 주세요."
            ]
        }
        
        import random
        return random.choice(templates.get(input_type, templates[EnhancedInputType.UNKNOWN]))

def get_enhanced_input_classifier() -> EnhancedInputClassifier:
    """강화된 입력 분류기 인스턴스 반환"""
    return EnhancedInputClassifier() 