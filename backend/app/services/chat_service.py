from motor.motor_asyncio import AsyncIOMotorDatabase
from .llm_service import LLMService
from .db_enhancement_service import DBEnhancementService
from .conversation_algorithm import ConversationAlgorithm
from .formatting_service import FormattingService
from .model_manager import get_model_manager, ModelType
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio

class ChatService:
    """
    채팅 서비스 - 고객 응대 알고리즘 기반
    
    업무별 메서드 분리:
    - get_conversation_response: 대화 정보 받기 (일상 대화)
    - search_and_enhance_answer: 응답 찾기 (전문 상담)
    - format_and_send_response: 응답 정보 보내기 (포맷팅)
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, llm_service: LLMService = None):
        """
        ChatService 초기화
        
        Args:
            db: MongoDB 데이터베이스 연결
            llm_service: LLM 서비스 인스턴스 (의존성 주입)
        """
        self.db = db
        self.llm_service = llm_service or LLMService(db)
        
        # 모델 매니저 가져오기
        self.model_manager = get_model_manager()
        
        # DB 연계 서비스 (LLM과 분리)
        self.db_enhancement_service = DBEnhancementService(db)
        
        # 고객 응대 알고리즘
        self.conversation_algorithm = ConversationAlgorithm()
        
        # 응답 시간 통계
        self.response_stats = {
            'total_requests': 0,
            'casual_conversations': 0,
            'professional_conversations': 0,
            'db_responses': 0,
            'llm_responses': 0,
            'errors': 0,
            'total_processing_time': 0,
            'min_processing_time': float('inf'),
            'max_processing_time': 0,
            'processing_times': []
        }
        
        logging.info("ChatService 초기화 완료")

    # ===== 업무별 메서드 분리 =====

    async def get_conversation_response(self, message: str) -> str:
        """
        대화 정보 받기 - 일상 대화 처리 (LLM 전용)
        
        Args:
            message: 사용자 메시지
            
        Returns:
            일상 대화 응답
        """
        try:
            logging.info(f"일상 대화 처리 시작: {message[:50]}...")
            
            # LLM 서비스를 통한 일상 대화 처리
            response = await self.llm_service.get_conversation_response(message)
            
            self.response_stats['casual_conversations'] += 1
            self.response_stats['llm_responses'] += 1
            
            logging.info(f"일상 대화 처리 완료: {response[:50]}...")
            return response
            
        except Exception as e:
            logging.error(f"일상 대화 처리 오류: {str(e)}")
            self.response_stats['errors'] += 1
            
            # 기본 응답으로 안정성 확보
            return self.conversation_algorithm._generate_casual_response(message)

    async def search_and_enhance_answer(self, message: str) -> str:
        """
        응답 찾기 - 전문 상담 처리 (LLM 전용)
        
        Args:
            message: 사용자 메시지
            
        Returns:
            전문 상담 응답
        """
        try:
            logging.info(f"전문 상담 처리 시작: {message[:50]}...")
            
            # LLM 서비스를 통한 전문 상담 처리
            response = await self.llm_service.search_and_enhance_answer(message)
            
            self.response_stats['professional_conversations'] += 1
            self.response_stats['llm_responses'] += 1
            
            logging.info(f"전문 상담 처리 완료: {response[:50]}...")
            return response
            
        except Exception as e:
            logging.error(f"전문 상담 처리 오류: {str(e)}")
            self.response_stats['errors'] += 1
            
            # 기본 응답으로 안정성 확보
            return self.conversation_algorithm.generate_no_answer_response(message)

    async def format_and_send_response(self, response: str) -> str:
        """
        응답 정보 보내기 - 응답 포맷팅 (LLM 전용)
        
        Args:
            response: 원본 응답
            
        Returns:
            포맷팅된 응답
        """
        try:
            logging.info("응답 포맷팅 시작")
            
            # LLM 서비스를 통한 포맷팅
            formatted_response = await self.llm_service.format_and_send_response(response)
            
            logging.info(f"응답 포맷팅 완료: {formatted_response[:50]}...")
            return formatted_response
            
        except Exception as e:
            logging.error(f"응답 포맷팅 오류: {str(e)}")
            self.response_stats['errors'] += 1
            
            # 기본 포맷팅으로 안정성 확보
            return FormattingService.format_response(response)

    # ===== 통합 메서드 =====

    async def process_message(self, message: str, conversation_id: str = None) -> str:
        """
        메시지 처리 - 업무별 메서드 통합 호출
        
        Args:
            message: 사용자 메시지
            conversation_id: 대화 ID
            
        Returns:
            처리된 응답
        """
        start_time = time.time()
        self.response_stats['total_requests'] += 1
        
        try:
            logging.info(f"메시지 처리 시작: {message[:50]}...")
            
            # 1. 대화 유형 분류
            conversation_type = self.conversation_algorithm.classify_conversation_type(message)
            logging.info(f"대화 유형: {conversation_type}")
            
            # 2. 업무별 메서드 호출
            if conversation_type == "casual":
                response = await self.get_conversation_response(message)
            else:
                response = await self.search_and_enhance_answer(message)
            
            # 3. 응답 포맷팅
            formatted_response = await self.format_and_send_response(response)
            
            # 처리 시간 계산
            processing_time = (time.time() - start_time) * 1000
            self.response_stats['total_processing_time'] += processing_time
            self.response_stats['processing_times'].append(processing_time)
            
            if processing_time < self.response_stats['min_processing_time']:
                self.response_stats['min_processing_time'] = processing_time
            if processing_time > self.response_stats['max_processing_time']:
                self.response_stats['max_processing_time'] = processing_time
            
            # 로깅
            logging.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] 상담사 응답 완료")
            logging.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] 처리 시간: {processing_time:.2f}ms")
            logging.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] 응답 내용: {formatted_response[:100]}...")
            
            return formatted_response
            
        except Exception as e:
            error_time = (time.time() - start_time) * 1000
            self.response_stats['errors'] += 1
            
            logging.error(f"메시지 처리 오류: {str(e)}")
            return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    # ===== 기존 메서드들 (호환성 유지) =====

    def switch_model(self, model_type: str) -> bool:
        """모델 전환 (호환성 유지)"""
        try:
            success = self.model_manager.switch_model(model_type)
            if success and self.llm_service:
                self.llm_service.model_type = model_type
            return success
        except Exception as e:
            logging.error(f"모델 전환 오류: {str(e)}")
            return False

    def get_current_model(self):
        """현재 모델 반환 (호환성 유지)"""
        return self.model_manager.get_current_model()

    def get_current_model_config(self):
        """현재 모델 설정 반환 (호환성 유지)"""
        return self.model_manager.get_current_model_config()

    def get_response_stats(self) -> Dict:
        """응답 통계 반환"""
        stats = self.response_stats.copy()
        
        if stats['total_requests'] > 0:
            stats['avg_processing_time'] = stats['total_processing_time'] / stats['total_requests']
            if stats['db_responses'] > 0:
                stats['avg_db_processing_time'] = stats['total_processing_time'] / stats['db_responses']
            if stats['llm_responses'] > 0:
                stats['avg_llm_processing_time'] = stats['total_processing_time'] / stats['llm_responses']
            else:
                stats['avg_llm_processing_time'] = 0
            
            # 중간값 계산
            if stats['processing_times']:
                sorted_times = sorted(stats['processing_times'])
                stats['median_processing_time'] = sorted_times[len(sorted_times) // 2]
        else:
            stats['avg_processing_time'] = 0
            stats['avg_db_processing_time'] = 0
            stats['avg_llm_processing_time'] = 0
            stats['median_processing_time'] = 0
        
        return stats

    def log_response_stats(self):
        """응답 통계를 로그로 출력"""
        stats = self.get_response_stats()
        
        logging.info("=== ChatService 응답 통계 ===")
        logging.info(f"총 요청 수: {stats['total_requests']}")
        logging.info(f"일상 대화: {stats['casual_conversations']}")
        logging.info(f"전문 상담: {stats['professional_conversations']}")
        logging.info(f"DB 응답: {stats['db_responses']}")
        logging.info(f"LLM 응답: {stats['llm_responses']}")
        logging.info(f"오류: {stats['errors']}")
        logging.info(f"평균 처리 시간: {stats['avg_processing_time']:.2f}ms")
        logging.info(f"최소 처리 시간: {stats['min_processing_time']:.2f}ms")
        logging.info(f"최대 처리 시간: {stats['max_processing_time']:.2f}ms")
        logging.info(f"중간값 처리 시간: {stats['median_processing_time']:.2f}ms")
        logging.info("=============================")

    def set_db_priority_mode(self, enabled: bool):
        """DB 우선 모드 설정 (호환성 유지)"""
        if self.llm_service:
            self.llm_service.set_db_priority_mode(enabled)

    def get_model_status(self) -> Dict[str, Any]:
        """모델 상태 반환 (호환성 유지)"""
        return {
            "current_model": self.model_manager.current_model,
            "available_models": self.model_manager.get_available_models(),
            "loaded_models": self.model_manager.get_loaded_models()
        }