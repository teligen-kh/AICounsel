"""
강화된 채팅 서비스 모듈
키워드+LLM 의도 분석과 DB+LLM 하이브리드 응답을 통합한 완전한 채팅 시스템
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from .enhanced_input_classifier import EnhancedInputClassifier, EnhancedInputType, get_enhanced_input_classifier
from .hybrid_response_generator import HybridResponseGenerator, get_hybrid_response_generator

class EnhancedChatService:
    """
    강화된 채팅 서비스 클래스
    키워드+LLM 의도 분석과 DB+LLM 하이브리드 응답을 통합한 완전한 채팅 시스템
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        강화된 채팅 서비스 초기화
        
        Args:
            db: MongoDB 데이터베이스 연결 인스턴스
        """
        self.db = db
        
        # 강화된 입력 분류기 (키워드 + LLM 의도 분석)
        self.input_classifier = get_enhanced_input_classifier()
        
        # 하이브리드 응답 생성기 (DB + LLM 조합 응답)
        self.response_generator = get_hybrid_response_generator(db)
        
        # 응답 통계 초기화 (성능 모니터링용)
        self.response_stats = {
            'total_requests': 0,           # 총 요청 수
            'greeting_casual': 0,          # 인사/일상 대화 수
            'technical': 0,                # 전문 상담 수
            'non_counseling': 0,           # 비상담 질문 수
            'profanity': 0,                # 욕설 감지 수
            'unknown': 0,                  # 기타 분류 수
            'db_enhanced': 0,              # DB 강화 응답 수
            'consultant_contact': 0,       # 상담사 연결 수
            'errors': 0,                   # 오류 발생 수
            'total_processing_time': 0,    # 총 처리 시간
            'min_processing_time': float('inf'),  # 최소 처리 시간
            'max_processing_time': 0,      # 최대 처리 시간
            'processing_times': []         # 처리 시간 기록 리스트
        }
        
        logging.info("✅ 강화된 채팅 서비스 초기화 완료")
    
    async def process_message(self, message: str, conversation_id: str = None) -> str:
        """강화된 메시지 처리"""
        start_time = time.time()
        self.response_stats['total_requests'] += 1
        
        try:
            logging.info(f"=== 강화된 메시지 처리 시작 ===")
            logging.info(f"입력 메시지: {message[:100]}...")
            
            # 1. 강화된 입력 분류 (키워드 + LLM 의도 분석)
            classification_start = time.time()
            input_type, classification_info = await self.input_classifier.classify_input(message)
            classification_time = (time.time() - classification_start) * 1000
            
            logging.info(f"분류 결과: {input_type.value}")
            logging.info(f"분류 방법: {classification_info.get('classification_method', 'unknown')}")
            logging.info(f"분류 시간: {classification_time:.2f}ms")
            
            # 2. 분류에 따른 응답 생성
            response_start = time.time()
            
            if input_type == EnhancedInputType.PROFANITY:
                # 욕설: 템플릿 응답
                response = self.input_classifier.get_response_template(input_type)
                self.response_stats['profanity'] += 1
                logging.info("욕설 감지 - 템플릿 응답 사용")
                
            elif input_type == EnhancedInputType.NON_COUNSELING:
                # 비상담: 템플릿 응답
                response = self.input_classifier.get_response_template(input_type)
                self.response_stats['non_counseling'] += 1
                logging.info("비상담 질문 감지 - 템플릿 응답 사용")
                
            elif input_type == EnhancedInputType.GREETING_CASUAL:
                # 인사/일상: LLM 응답
                response = await self.response_generator.generate_casual_response(message)
                self.response_stats['greeting_casual'] += 1
                logging.info("인사/일상 대화 - LLM 응답 생성")
                
            elif input_type == EnhancedInputType.TECHNICAL:
                # 전문: DB + LLM 하이브리드
                response, response_info = await self.response_generator.generate_response(message)
                self.response_stats['technical'] += 1
                
                if response_info.get('response_type') == 'db_enhanced':
                    self.response_stats['db_enhanced'] += 1
                    logging.info("전문 질문 - DB + LLM 하이브리드 응답")
                else:
                    self.response_stats['consultant_contact'] += 1
                    logging.info("전문 질문 - 상담사 연결 안내")
                    
            else:
                # 기타: 기본 응답
                response = self.input_classifier.get_response_template(EnhancedInputType.UNKNOWN)
                self.response_stats['unknown'] += 1
                logging.info("기타 분류 - 기본 응답 사용")
            
            response_time = (time.time() - response_start) * 1000
            
            # 3. 처리 시간 계산
            total_time = (time.time() - start_time) * 1000
            self.response_stats['total_processing_time'] += total_time
            self.response_stats['processing_times'].append(total_time)
            
            if total_time < self.response_stats['min_processing_time']:
                self.response_stats['min_processing_time'] = total_time
            if total_time > self.response_stats['max_processing_time']:
                self.response_stats['max_processing_time'] = total_time
            
            # 4. 로깅
            logging.info(f"=== 강화된 메시지 처리 완료 ===")
            logging.info(f"전체 처리 시간: {total_time:.2f}ms")
            logging.info(f"분류 시간: {classification_time:.2f}ms")
            logging.info(f"응답 생성 시간: {response_time:.2f}ms")
            logging.info(f"응답 길이: {len(response)}")
            logging.info(f"응답 내용: {response[:100]}...")
            
            return response
            
        except Exception as e:
            error_time = (time.time() - start_time) * 1000
            self.response_stats['errors'] += 1
            
            logging.error(f"=== 강화된 메시지 처리 오류 ===")
            logging.error(f"오류 발생 시간: {error_time:.2f}ms")
            logging.error(f"오류 내용: {str(e)}")
            import traceback
            logging.error(f"상세 오류: {traceback.format_exc()}")
            
            # 오류 시 기본 응답
            return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
    
    async def process_message_detailed(self, message: str, conversation_id: str = None) -> Dict[str, Any]:
        """상세 정보와 함께 메시지 처리"""
        start_time = time.time()
        
        try:
            # 1. 입력 분류
            input_type, classification_info = await self.input_classifier.classify_input(message)
            
            # 2. 응답 생성
            if input_type in [EnhancedInputType.PROFANITY, EnhancedInputType.NON_COUNSELING]:
                response = self.input_classifier.get_response_template(input_type)
                response_info = {
                    "response_type": "template",
                    "template_type": input_type.value
                }
            elif input_type == EnhancedInputType.GREETING_CASUAL:
                response = await self.response_generator.generate_casual_response(message)
                response_info = {
                    "response_type": "llm_casual",
                    "llm_used": True
                }
            elif input_type == EnhancedInputType.TECHNICAL:
                response, response_info = await self.response_generator.generate_response(message)
            else:
                response = self.input_classifier.get_response_template(EnhancedInputType.UNKNOWN)
                response_info = {
                    "response_type": "template",
                    "template_type": "unknown"
                }
            
            # 3. 상세 정보 구성
            total_time = (time.time() - start_time) * 1000
            
            detailed_result = {
                "response": response,
                "input_type": input_type.value,
                "classification_info": classification_info,
                "response_info": response_info,
                "processing_time_ms": total_time,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
            
            return detailed_result
            
        except Exception as e:
            error_time = (time.time() - start_time) * 1000
            
            return {
                "response": "죄송합니다. 일시적인 오류가 발생했습니다.",
                "input_type": "error",
                "error": str(e),
                "processing_time_ms": error_time,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_response_stats(self) -> Dict[str, Any]:
        """응답 통계 반환"""
        stats = self.response_stats.copy()
        
        # 평균 처리 시간 계산
        if stats['processing_times']:
            stats['avg_processing_time'] = sum(stats['processing_times']) / len(stats['processing_times'])
            stats['median_processing_time'] = sorted(stats['processing_times'])[len(stats['processing_times'])//2]
        else:
            stats['avg_processing_time'] = 0
            stats['median_processing_time'] = 0
        
        # 성공률 계산
        total_requests = stats['total_requests']
        if total_requests > 0:
            stats['success_rate'] = ((total_requests - stats['errors']) / total_requests) * 100
        else:
            stats['success_rate'] = 0
        
        return stats
    
    def log_response_stats(self):
        """응답 통계 로깅"""
        stats = self.get_response_stats()
        
        logging.info("=== 강화된 채팅 서비스 통계 ===")
        logging.info(f"총 요청 수: {stats['total_requests']}")
        logging.info(f"인사/일상: {stats['greeting_casual']}")
        logging.info(f"전문 상담: {stats['technical']}")
        logging.info(f"비상담: {stats['non_counseling']}")
        logging.info(f"욕설: {stats['profanity']}")
        logging.info(f"기타: {stats['unknown']}")
        logging.info(f"DB 강화: {stats['db_enhanced']}")
        logging.info(f"상담사 연결: {stats['consultant_contact']}")
        logging.info(f"오류: {stats['errors']}")
        logging.info(f"성공률: {stats['success_rate']:.1f}%")
        logging.info(f"평균 처리 시간: {stats['avg_processing_time']:.2f}ms")
        logging.info(f"최소 처리 시간: {stats['min_processing_time']:.2f}ms")
        logging.info(f"최대 처리 시간: {stats['max_processing_time']:.2f}ms")
        logging.info("================================")

def get_enhanced_chat_service(db: AsyncIOMotorDatabase) -> EnhancedChatService:
    """강화된 채팅 서비스 인스턴스 반환"""
    return EnhancedChatService(db) 