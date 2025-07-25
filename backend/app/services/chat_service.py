from motor.motor_asyncio import AsyncIOMotorDatabase
from .llm_service import LLMService
from .db_enhancement_service import DBEnhancementService
from .conversation_algorithm import ConversationAlgorithm
from .formatting_service import FormattingService
from .model_manager import get_model_manager, ModelType
from .input_filter import InputFilter, InputType as InputFilterType
from ..config import settings, enable_module, disable_module, get_module_status
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
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        채팅 서비스 초기화
        
        Args:
            db: MongoDB 데이터베이스 연결 인스턴스
        """
        self.db = db
        
        # DB 연계 서비스 (LLM과 분리)
        self.db_enhancement_service = DBEnhancementService(db)
        
        # 고객 응대 알고리즘
        self.conversation_algorithm = ConversationAlgorithm()
        
        # 입력 필터 (설정에 따라 선택)
        if settings.ENABLE_CONTEXT_AWARE_CLASSIFICATION:
            from .context_aware_classifier import ContextAwareClassifier, InputType
            self.input_filter = ContextAwareClassifier(db)
            # LLM 서비스 주입 (나중에 주입)
            self.input_filter.inject_llm_service(None)  # 초기화 시에는 None으로 설정
            self.InputType = InputType  # context_aware_classifier의 InputType 사용
            logging.info("✅ 문맥 인식 분류기 활성화")
        else:
            # DB 연동된 InputFilter 사용
            self.input_filter = InputFilter(db)
            self.InputType = InputFilterType  # input_filter의 InputType 사용
            logging.info("✅ DB 연동 키워드 분류기 사용")
        
        # 자동화 서비스 추가
        from .automation_service import AutomationService
        self.automation_service = AutomationService(db)
        
        logging.info("ChatService 초기화 완료")
    
    def _initialize_modules(self):
        """설정에 따라 모듈을 초기화합니다."""
        # DB 연계 서비스 (설정에 따라 활성화/비활성화)
        if settings.ENABLE_MONGODB_SEARCH:
            self.db_enhancement_service = DBEnhancementService(self.db)
            logging.info("✅ MongoDB 검색 모듈 활성화")
        else:
            self.db_enhancement_service = None
            logging.info("❌ MongoDB 검색 모듈 비활성화")
        
        # 고객 응대 알고리즘 (설정에 따라 활성화/비활성화)
        if settings.ENABLE_CONVERSATION_ANALYSIS:
            self.conversation_algorithm = ConversationAlgorithm()
            logging.info("✅ 고객 질문 분석 모듈 활성화")
        else:
            self.conversation_algorithm = None
            logging.info("❌ 고객 질문 분석 모듈 비활성화")
        
        # 입력 필터 (설정에 따라 활성화/비활성화)
        if settings.ENABLE_INPUT_FILTERING:
            self.input_filter = get_input_filter()
            logging.info("✅ 입력 필터링 모듈 활성화")
        else:
            self.input_filter = None
            logging.info("❌ 입력 필터링 모듈 비활성화")
    
    def _log_module_status(self):
        """모듈 상태를 로깅합니다."""
        status = get_module_status()
        logging.info("=== 모듈 활성화 상태 ===")
        for module, enabled in status.items():
            status_str = "✅ 활성화" if enabled else "❌ 비활성화"
            logging.info(f"{module}: {status_str}")
        logging.info("=======================")

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
        사용자 메시지를 처리하고 응답을 생성합니다.
        
        Args:
            message: 사용자 메시지
            conversation_id: 대화 ID
            
        Returns:
            str: AI 응답
        """
        start_time = time.time()
        
        try:
            logging.info(f"메시지 처리 시작: {message[:20]}...")
            
            # 1. 입력 분류
            input_type, details = await self.input_filter.classify_input(message)
            logging.info(f"입력 분류: {input_type.value} - {details.get('reason', '')}")
            
            # 2. 분류에 따른 응답 생성
            if input_type in [self.InputType.PROFANITY, self.InputType.NON_COUNSELING]:
                # 템플릿 응답 사용
                response = self.input_filter.get_response_template(input_type)
                logging.info(f"템플릿 응답 사용: {response}")
            else:
                # LLM 또는 DB 기반 응답
                if input_type in [self.InputType.TECHNICAL, self.InputType.UNKNOWN]:
                    # 전문 상담 처리 (unknown도 포함)
                    logging.info(f"🔍 {input_type.value.upper()} 분류 감지 - 전문 상담 처리 시작")
                    response = await self._handle_technical_conversation(message)
                    logging.info(f"✅ 전문 상담 처리 완료: {response[:100]}...")
                else:
                    # 일상 대화 처리 (casual만)
                    logging.info("🔍 CASUAL 분류 감지 - 일상 대화 처리 시작")
                    response = await self._handle_casual_conversation(message)
                    logging.info(f"✅ 일상 대화 처리 완료: {response[:100]}...")
            
            # 3. 자동화 처리 (대화 저장 및 knowledge_base 업데이트)
            automation_result = await self.automation_service.process_conversation_automation(
                message, response, input_type.value
            )
            
            # 4. 응답 포맷팅
            formatted_response = await self._format_response(response, input_type)
            
            # 5. 처리 시간 기록
            end_time = time.time()
            processing_time = (end_time - start_time) * 1000
            logging.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 상담사 응답 완료")
            logging.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 처리 시간: {processing_time:.2f}ms")
            logging.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 응답 내용:\n{formatted_response}")
            
            return formatted_response
            
        except Exception as e:
            logging.error(f"메시지 처리 중 오류: {str(e)}")
            return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    async def _handle_casual_conversation(self, message: str) -> str:
        """일상 대화 처리"""
        try:
            # 기존 LLM 서비스 사용 (새로 생성하지 않음)
            from ..dependencies import get_llm_service
            llm_service = await get_llm_service()
            response = await llm_service.get_conversation_response(message)
            return response
        except Exception as e:
            logging.error(f"일상 대화 처리 오류: {str(e)}")
            return "안녕하세요! 어떻게 도와드릴까요?"

    async def _handle_technical_conversation(self, message: str) -> str:
        """전문 상담 처리"""
        try:
            logging.info("🔍 전문 상담 처리 시작")
            
            # 기존 LLM 서비스 사용 (새로 생성하지 않음)
            from ..dependencies import get_llm_service
            llm_service = await get_llm_service()
            logging.info("✅ LLM 서비스 가져오기 완료")
            
            # DB 서비스 상태 확인
            if hasattr(llm_service, 'search_service') and llm_service.search_service:
                logging.info("✅ DB 검색 서비스가 주입되어 있습니다.")
            else:
                logging.warning("❌ DB 검색 서비스가 주입되지 않았습니다. DB 모드로 재설정합니다.")
                # DB 서비스 재주입
                from ..dependencies import get_search_service
                search_service = await get_search_service()
                llm_service.inject_db_service(search_service)
                llm_service.set_db_mode(True)
                logging.info("✅ DB 검색 서비스 재주입 완료")
            
            # DB 검색 + LLM 강화
            logging.info("🔍 search_and_enhance_answer 호출 시작")
            response = await llm_service.search_and_enhance_answer(message)
            logging.info(f"✅ search_and_enhance_answer 완료: {response[:100]}...")
            return response
        except Exception as e:
            logging.error(f"전문 상담 처리 오류: {str(e)}")
            return "죄송합니다. 전문 상담사에게 문의해주세요."

    async def _format_response(self, response: str, input_type=None) -> str:
        """응답 포맷팅"""
        try:
            if not response:
                return "죄송합니다. 응답을 생성할 수 없습니다."
            
            # 기본 포맷팅
            formatted = response.strip()
            
            # technical/unknown 분류일 때는 길이 제한 해제 (DB 답변 보존)
            if input_type in [self.InputType.TECHNICAL, self.InputType.UNKNOWN]:
                logging.info(f"✅ {input_type.value.upper()} 분류 - 응답 길이 제한 해제")
                return formatted
            
            # 너무 긴 응답 자르기 (일상 대화에만 적용)
            if len(formatted) > 1000:
                formatted = formatted[:1000] + "..."
            
            return formatted
        except Exception as e:
            logging.error(f"응답 포맷팅 오류: {str(e)}")
            return response

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