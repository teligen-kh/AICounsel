"""
하이브리드 응답 생성기 모듈
DB 정확성과 LLM 자연스러움을 결합한 고품질 응답 생성 시스템
"""

import logging
from typing import Dict, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
import re

class HybridResponseGenerator:
    """
    하이브리드 응답 생성기 클래스
    MongoDB DB 검색과 LLM 강화를 결합하여 최적의 응답 생성
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        하이브리드 응답 생성기 초기화
        
        Args:
            db: MongoDB 데이터베이스 연결 인스턴스
        """
        self.db = db
        self.knowledge_collection = db.knowledge_base  # 지식 베이스 컬렉션
        self._initialize_llm()  # LLM 모델 초기화
        
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
                logging.info("✅ 하이브리드 응답 생성기 LLM 모델 로딩 완료")
            else:
                self.llm_available = False
                logging.warning("❌ LLM 모델을 찾을 수 없습니다. DB 응답만 사용합니다.")
                
        except Exception as e:
            self.llm_available = False
            logging.error(f"하이브리드 응답 생성기 LLM 초기화 실패: {str(e)}")
    
    async def search_db_answer(self, query: str) -> Optional[Dict]:
        """MongoDB에서 답변 검색"""
        try:
            # 정확한 매치 검색
            pipeline = [
                {
                    "$match": {
                        "$or": [
                            {"question": {"$regex": query, "$options": "i"}},
                            {"keywords": {"$in": [query.lower()]}}
                        ]
                    }
                },
                {"$limit": 1}
            ]
            
            result = await self.knowledge_collection.aggregate(pipeline).to_list(1)
            
            if result:
                return {
                    "answer": result[0]['answer'],
                    "question": result[0]['question'],
                    "keywords": result[0].get('keywords', []),
                    "source": "exact_match"
                }
            
            # 키워드 기반 검색
            keywords = self._extract_keywords(query)
            if keywords:
                keyword_pipeline = [
                    {
                        "$match": {
                            "keywords": {"$in": keywords}
                        }
                    },
                    {"$limit": 1}
                ]
                
                keyword_result = await self.knowledge_collection.aggregate(keyword_pipeline).to_list(1)
                
                if keyword_result:
                    return {
                        "answer": keyword_result[0]['answer'],
                        "question": keyword_result[0]['question'],
                        "keywords": keyword_result[0].get('keywords', []),
                        "source": "keyword_match"
                    }
            
            return None
            
        except Exception as e:
            logging.error(f"DB 검색 실패: {str(e)}")
            return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 키워드 추출"""
        # 한글, 영문, 숫자로 구성된 단어 추출
        words = re.findall(r'[가-힣a-zA-Z0-9]+', text.lower())
        # 2글자 이상, 10글자 이하 단어만 선택
        keywords = [word for word in words if 2 <= len(word) <= 10]
        return keywords[:5]
    
    async def enhance_with_llm(self, db_answer: str, user_query: str) -> str:
        """LLM으로 DB 답변을 친절하게 풀어서 설명"""
        if not self.llm_available:
            return self._format_db_answer_basic(db_answer, user_query)
        
        try:
            # LLM 프롬프트 구성
            prompt = f"""다음 DB에서 찾은 답변을 사용자에게 친절하고 자연스럽게 설명해주세요.

사용자 질문: {user_query}
DB 답변: {db_answer}

요구사항:
1. 친절하고 이해하기 쉽게 설명
2. 사용자 질문에 직접적으로 답변
3. 필요시 추가 정보나 팁 제공
4. 자연스러운 대화체 사용
5. 200자 이내로 간결하게

답변:"""

            # LLM 응답 생성
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=150,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response.replace(prompt, "").strip()
            
            # 응답 정리
            response = self._clean_llm_response(response)
            
            logging.info(f"LLM 강화 응답 생성 완료: {response[:50]}...")
            return response
            
        except Exception as e:
            logging.error(f"LLM 강화 실패: {str(e)}")
            return self._format_db_answer_basic(db_answer, user_query)
    
    def _format_db_answer_basic(self, db_answer: str, user_query: str) -> str:
        """기본 DB 답변 포맷팅"""
        # 간단한 포맷팅
        formatted = db_answer.strip()
        
        # URL이 있으면 링크 형태로 변환
        if "smart.arumnet.com" in formatted:
            formatted = formatted.replace("smart.arumnet.com", "smart.arumnet.com에서 다운로드하세요.")
        
        return formatted
    
    def _clean_llm_response(self, response: str) -> str:
        """LLM 응답 정리"""
        # 불필요한 문자 제거
        response = re.sub(r'^\s*["\']\s*', '', response)
        response = re.sub(r'\s*["\']\s*$', '', response)
        
        # 줄바꿈 정리
        response = re.sub(r'\n+', ' ', response)
        response = re.sub(r'\s+', ' ', response)
        
        return response.strip()
    
    async def generate_response(self, user_query: str) -> Tuple[str, Dict]:
        """하이브리드 응답 생성"""
        try:
            logging.info(f"하이브리드 응답 생성 시작: {user_query[:50]}...")
            
            # 1. DB 검색
            db_result = await self.search_db_answer(user_query)
            
            if db_result:
                # 2. DB 답변이 있으면 LLM으로 강화
                enhanced_response = await self.enhance_with_llm(
                    db_result["answer"], 
                    user_query
                )
                
                result_info = {
                    "response_type": "db_enhanced",
                    "db_source": db_result["source"],
                    "original_answer": db_result["answer"],
                    "enhanced": True,
                    "llm_used": self.llm_available
                }
                
                logging.info(f"DB 답변 + LLM 강화 완료")
                return enhanced_response, result_info
            else:
                # 3. DB 답변이 없으면 상담사 연결 안내
                consultant_response = self._get_consultant_contact_response(user_query)
                
                result_info = {
                    "response_type": "consultant_contact",
                    "db_source": "no_match",
                    "enhanced": False,
                    "llm_used": False
                }
                
                logging.info(f"DB 답변 없음, 상담사 연결 안내")
                return consultant_response, result_info
                
        except Exception as e:
            logging.error(f"하이브리드 응답 생성 실패: {str(e)}")
            
            # 오류 시 기본 응답
            error_response = "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
            result_info = {
                "response_type": "error",
                "error": str(e),
                "enhanced": False,
                "llm_used": False
            }
            
            return error_response, result_info
    
    def _get_consultant_contact_response(self, query: str) -> str:
        """상담사 연결 안내 응답"""
        responses = [
            f"해당 질문에 대한 답변을 찾을 수 없습니다. 상담사를 통해 연락 드리겠습니다. 연락처를 알려주세요.",
            f"죄송합니다. 해당 내용은 상담사가 도움을 드릴 수 있습니다. 연락처를 알려주시면 상담사가 연락드리겠습니다.",
            f"해당 질문은 상담사가 더 정확한 답변을 드릴 수 있습니다. 연락처를 알려주시면 상담사가 연락드리겠습니다."
        ]
        
        import random
        return random.choice(responses)
    
    async def generate_technical_response(self, user_query: str) -> str:
        """전문 상담 응답 생성 (DB 우선)"""
        try:
            # DB 검색
            db_result = await self.search_db_answer(user_query)
            
            if db_result:
                # DB 답변이 있으면 LLM으로 강화
                if self.llm_available:
                    return await self.enhance_with_llm(db_result["answer"], user_query)
                else:
                    return self._format_db_answer_basic(db_result["answer"], user_query)
            else:
                # DB 답변이 없으면 상담사 연결
                return self._get_consultant_contact_response(user_query)
                
        except Exception as e:
            logging.error(f"전문 상담 응답 생성 실패: {str(e)}")
            return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
    
    async def generate_casual_response(self, user_query: str) -> str:
        """일상 대화 응답 생성 (LLM 우선)"""
        if not self.llm_available:
            return "안녕하세요! 포스 시스템과 관련된 질문에 답변해드릴 수 있어요."
        
        try:
            # LLM으로 일상 대화 응답 생성
            prompt = f"""사용자와의 일상적인 대화에 친절하게 응답해주세요.

사용자: {user_query}

요구사항:
1. 친절하고 자연스러운 대화체
2. 포스 시스템 상담사임을 언급
3. 도움을 제공할 수 있음을 안내
4. 100자 이내로 간결하게

답변:"""

            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=100,
                    temperature=0.8,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response.replace(prompt, "").strip()
            
            return self._clean_llm_response(response)
            
        except Exception as e:
            logging.error(f"일상 대화 응답 생성 실패: {str(e)}")
            return "안녕하세요! 포스 시스템과 관련된 질문에 답변해드릴 수 있어요."

def get_hybrid_response_generator(db: AsyncIOMotorDatabase) -> HybridResponseGenerator:
    """하이브리드 응답 생성기 인스턴스 반환"""
    return HybridResponseGenerator(db) 