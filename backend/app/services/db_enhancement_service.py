from motor.motor_asyncio import AsyncIOMotorDatabase
from .mongodb_search_service import MongoDBSearchService
from .conversation_algorithm import ConversationAlgorithm
from .formatting_service import FormattingService
import logging
import time
from typing import Dict, Optional, Tuple
from datetime import datetime

class DBEnhancementService:
    """
    DB 연계 모듈 - LLM과 분리된 독립적인 서비스
    
    역할:
    1. DB 검색 및 답변 찾기
    2. 답변 포맷팅 및 개선
    3. 성능 최적화된 처리
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        DB 연계 서비스 초기화
        
        Args:
            db: MongoDB 데이터베이스 연결
        """
        self.db = db
        self.search_service = MongoDBSearchService(db)
        self.conversation_algorithm = ConversationAlgorithm()
        self.formatting_service = FormattingService()
        
        # 성능 통계
        self.performance_stats = {
            'total_requests': 0,
            'db_search_time': 0,
            'formatting_time': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'avg_response_time': 0,
            'response_times': []
        }
        
        logging.info("DB 연계 서비스 초기화 완료")

    async def process_professional_query(self, message: str) -> str:
        """
        전문 상담 쿼리 처리 (LLM 없이 DB 기반)
        
        Args:
            message: 사용자 메시지
            
        Returns:
            포맷팅된 응답
        """
        start_time = time.time()
        self.performance_stats['total_requests'] += 1
        
        try:
            logging.info(f"DB 연계 처리 시작: {message[:50]}...")
            
            # 1. DB 검색
            db_search_start = time.time()
            db_answer = await self.search_service.search_answer(message)
            db_search_time = (time.time() - db_search_start) * 1000
            self.performance_stats['db_search_time'] += db_search_time
            
            logging.info(f"DB 검색 시간: {db_search_time:.2f}ms")
            
            # 2. 답변 처리
            if db_answer:
                self.performance_stats['successful_responses'] += 1
                response = self._format_db_answer(db_answer)
            else:
                self.performance_stats['failed_responses'] += 1
                response = self.conversation_algorithm.generate_no_answer_response(message)
            
            # 3. 포맷팅
            formatting_start = time.time()
            formatted_response = self.formatting_service.format_response(response)
            formatting_time = (time.time() - formatting_start) * 1000
            self.performance_stats['formatting_time'] += formatting_time
            
            # 처리 시간 계산
            total_time = (time.time() - start_time) * 1000
            self.performance_stats['response_times'].append(total_time)
            
            logging.info(f"DB 연계 처리 완료: {formatted_response[:50]}...")
            logging.info(f"총 처리 시간: {total_time:.2f}ms")
            
            return formatted_response
            
        except Exception as e:
            error_time = (time.time() - start_time) * 1000
            self.performance_stats['failed_responses'] += 1
            
            logging.error(f"DB 연계 처리 오류: {str(e)}")
            return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    def _format_db_answer(self, db_answer: str) -> str:
        """
        DB 답변을 포맷팅합니다.
        
        Args:
            db_answer: DB에서 가져온 원본 답변
            
        Returns:
            포맷팅된 답변
        """
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
            if len(response) > 500:  # 500자로 제한
                response = response[:500] + "..."
            
            # 불필요한 줄바꿈 정리
            response = '\n'.join(line.strip() for line in response.split('\n') if line.strip())
            
            # 친절한 마무리 추가
            response += "\n\n도움이 되셨나요? 다른 질문이 있으시면 언제든 말씀해 주세요."
            
            return response
            
        except Exception as e:
            logging.error(f"DB 답변 포맷팅 오류: {str(e)}")
            return db_answer

    async def process_casual_query(self, message: str) -> str:
        """
        일상 대화 쿼리 처리 (LLM 없이 기본 응답)
        
        Args:
            message: 사용자 메시지
            
        Returns:
            기본 응답
        """
        start_time = time.time()
        self.performance_stats['total_requests'] += 1
        
        try:
            logging.info(f"일상 대화 처리 시작: {message[:50]}...")
            
            # 기본 응답 생성
            response = self.conversation_algorithm._generate_casual_response(message)
            
            # 포맷팅
            formatting_start = time.time()
            formatted_response = self.formatting_service.format_response(response)
            formatting_time = (time.time() - formatting_start) * 1000
            self.performance_stats['formatting_time'] += formatting_time
            
            # 처리 시간 계산
            total_time = (time.time() - start_time) * 1000
            self.performance_stats['response_times'].append(total_time)
            self.performance_stats['successful_responses'] += 1
            
            logging.info(f"일상 대화 처리 완료: {formatted_response[:50]}...")
            logging.info(f"총 처리 시간: {total_time:.2f}ms")
            
            return formatted_response
            
        except Exception as e:
            error_time = (time.time() - start_time) * 1000
            self.performance_stats['failed_responses'] += 1
            
            logging.error(f"일상 대화 처리 오류: {str(e)}")
            return "안녕하세요! 어떤 도움이 필요하신가요?"

    def get_performance_stats(self) -> Dict:
        """성능 통계를 반환합니다."""
        stats = self.performance_stats.copy()
        
        if stats['total_requests'] > 0:
            stats['avg_response_time'] = sum(stats['response_times']) / len(stats['response_times'])
            stats['avg_db_search_time'] = stats['db_search_time'] / stats['total_requests']
            stats['avg_formatting_time'] = stats['formatting_time'] / stats['total_requests']
            stats['success_rate'] = stats['successful_responses'] / stats['total_requests'] * 100
        else:
            stats['avg_response_time'] = 0
            stats['avg_db_search_time'] = 0
            stats['avg_formatting_time'] = 0
            stats['success_rate'] = 0
        
        return stats

    def log_performance_summary(self):
        """성능 요약을 로그로 출력합니다."""
        stats = self.get_performance_stats()
        
        logging.info("=== DB 연계 서비스 성능 요약 ===")
        logging.info(f"총 요청 수: {stats['total_requests']}")
        logging.info(f"성공 응답 수: {stats['successful_responses']}")
        logging.info(f"실패 응답 수: {stats['failed_responses']}")
        logging.info(f"성공률: {stats['success_rate']:.1f}%")
        logging.info(f"평균 응답 시간: {stats['avg_response_time']:.2f}ms")
        logging.info(f"평균 DB 검색 시간: {stats['avg_db_search_time']:.2f}ms")
        logging.info(f"평균 포맷팅 시간: {stats['avg_formatting_time']:.2f}ms")
        logging.info("================================") 