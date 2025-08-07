#!/usr/bin/env python3
"""
최적화된 패턴 매칭 테스트 모듈
MongoDB Text Search + 벡터 검색 조합의 성능과 정확도 테스트
"""

import asyncio
import motor.motor_asyncio
import logging
from typing import List, Dict, Optional
import sys
import os
from datetime import datetime
import time

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, backend_dir)

from app.database import get_database
from app.services.optimized_pattern_matcher import OptimizedPatternMatcher
from app.services.context_aware_classifier import ContextAwareClassifier, InputType

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizedPatternMatchingTester:
    """최적화된 패턴 매칭 테스트기"""
    
    def __init__(self, db):
        self.db = db
        self.optimized_matcher = OptimizedPatternMatcher(db)
        self.classifier = ContextAwareClassifier(db)
        
    async def setup_test_data(self):
        """테스트용 패턴 데이터 설정"""
        try:
            logger.info("🔧 테스트 패턴 데이터 설정 시작")
            
            # 기존 테스트 데이터 정리
            await self.db.context_patterns.delete_many({"description": "test_pattern"})
            
            # 테스트 패턴들 추가
            test_patterns = [
                ("견적서 단위 변경", "technical", "견적서 단위 변경 관련 질문"),
                ("견적서 단위 바꾸고 싶어", "technical", "견적서 단위 변경 요청"),
                ("견적서 단위 수정", "technical", "견적서 단위 수정 관련"),
                ("직인 설정", "technical", "직인 설정 관련 질문"),
                ("직인 등록", "technical", "직인 등록 관련"),
                ("직인 관리", "technical", "직인 관리 관련"),
                ("프린터 설정", "technical", "프린터 설정 관련"),
                ("프린터 설치", "technical", "프린터 설치 관련"),
                ("프린터 드라이버", "technical", "프린터 드라이버 관련"),
                ("매출 작업", "technical", "매출 작업 관련"),
                ("매출 관리", "technical", "매출 관리 관련"),
                ("매출 통계", "technical", "매출 통계 관련"),
                ("상품코드 관리", "technical", "상품코드 관리 관련"),
                ("상품코드 등록", "technical", "상품코드 등록 관련"),
                ("상품코드 수정", "technical", "상품코드 수정 관련")
            ]
            
            for pattern, context, description in test_patterns:
                await self.optimized_matcher.add_pattern(pattern, context, description + " (test_pattern)")
            
            logger.info(f"✅ {len(test_patterns)}개 테스트 패턴 추가 완료")
            
        except Exception as e:
            logger.error(f"테스트 데이터 설정 실패: {e}")
    
    async def test_optimized_matcher(self, test_questions: List[str]):
        """최적화된 매칭기 테스트"""
        logger.info("=== 최적화된 패턴 매칭기 테스트 시작 ===")
        
        results = []
        
        for i, question in enumerate(test_questions, 1):
            logger.info(f"\n--- 테스트 {i}: {question} ---")
            
            try:
                start_time = time.time()
                
                # 최적화된 매칭기로 검색
                result = await self.optimized_matcher.find_best_match(question, threshold=0.3)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                if result:
                    pattern_doc, similarity_score, method = result
                    logger.info(f"✅ 매칭 성공: {pattern_doc['pattern']}")
                    logger.info(f"   유사도: {similarity_score:.3f}")
                    logger.info(f"   방법: {method}")
                    logger.info(f"   응답시간: {response_time:.2f}ms")
                    
                    results.append({
                        "question": question,
                        "matched_pattern": pattern_doc['pattern'],
                        "similarity_score": similarity_score,
                        "method": method,
                        "response_time": response_time,
                        "success": True
                    })
                else:
                    logger.info("❌ 매칭 실패")
                    results.append({
                        "question": question,
                        "matched_pattern": None,
                        "similarity_score": 0,
                        "method": None,
                        "response_time": response_time,
                        "success": False
                    })
                
            except Exception as e:
                logger.error(f"테스트 {i} 실행 중 오류: {e}")
                results.append({
                    "question": question,
                    "error": str(e),
                    "success": False
                })
        
        logger.info("\n=== 최적화된 패턴 매칭기 테스트 완료 ===")
        return results
    
    async def test_classifier_integration(self, test_questions: List[str]):
        """분류기 통합 테스트"""
        logger.info("=== 분류기 통합 테스트 시작 ===")
        
        results = []
        
        for i, question in enumerate(test_questions, 1):
            logger.info(f"\n--- 테스트 {i}: {question} ---")
            
            try:
                start_time = time.time()
                
                # 분류기로 분류
                input_type, details = await self.classifier.classify_input(question)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                logger.info(f"✅ 분류 결과: {input_type.value}")
                logger.info(f"   이유: {details.get('reason', 'N/A')}")
                logger.info(f"   소스: {details.get('source', 'N/A')}")
                logger.info(f"   응답시간: {response_time:.2f}ms")
                
                if 'similarity_score' in details:
                    logger.info(f"   유사도: {details['similarity_score']:.3f}")
                if 'method' in details:
                    logger.info(f"   방법: {details['method']}")
                
                results.append({
                    "question": question,
                    "input_type": input_type.value,
                    "reason": details.get('reason', 'N/A'),
                    "source": details.get('source', 'N/A'),
                    "similarity_score": details.get('similarity_score', 0),
                    "method": details.get('method', 'N/A'),
                    "response_time": response_time,
                    "success": True
                })
                
            except Exception as e:
                logger.error(f"분류기 테스트 {i} 실행 중 오류: {e}")
                results.append({
                    "question": question,
                    "error": str(e),
                    "success": False
                })
        
        logger.info("\n=== 분류기 통합 테스트 완료 ===")
        return results
    
    async def performance_benchmark(self, test_questions: List[str], iterations: int = 10):
        """성능 벤치마크"""
        logger.info(f"=== 성능 벤치마크 시작 (반복: {iterations}회) ===")
        
        # 최적화된 매칭기 성능 측정
        optimized_times = []
        optimized_success_count = 0
        
        for iteration in range(iterations):
            logger.info(f"반복 {iteration + 1}/{iterations}")
            
            for question in test_questions:
                start_time = time.time()
                result = await self.optimized_matcher.find_best_match(question, threshold=0.3)
                end_time = time.time()
                
                optimized_times.append((end_time - start_time) * 1000)
                if result:
                    optimized_success_count += 1
        
        # 통계 계산
        total_queries = len(test_questions) * iterations
        avg_response_time = sum(optimized_times) / len(optimized_times)
        success_rate = optimized_success_count / total_queries
        
        logger.info(f"=== 성능 벤치마크 결과 ===")
        logger.info(f"총 쿼리 수: {total_queries}")
        logger.info(f"성공률: {success_rate:.2%}")
        logger.info(f"평균 응답시간: {avg_response_time:.2f}ms")
        logger.info(f"최소 응답시간: {min(optimized_times):.2f}ms")
        logger.info(f"최대 응답시간: {max(optimized_times):.2f}ms")
        
        # 성능 통계 반환
        performance_stats = self.optimized_matcher.get_performance_stats()
        logger.info(f"캐시 히트율: {performance_stats.get('cache_hit_rate', 0):.2%}")
        logger.info(f"Text Search 사용률: {performance_stats.get('text_search_count', 0)}")
        logger.info(f"벡터 검색 사용률: {performance_stats.get('vector_search_count', 0)}")
        
        return {
            "total_queries": total_queries,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "min_response_time": min(optimized_times),
            "max_response_time": max(optimized_times),
            "performance_stats": performance_stats
        }
    
    def print_results_summary(self, matcher_results: List[Dict], classifier_results: List[Dict]):
        """결과 요약 출력"""
        logger.info("\n" + "="*60)
        logger.info("📊 테스트 결과 요약")
        logger.info("="*60)
        
        # 매칭기 결과 분석
        matcher_success = sum(1 for r in matcher_results if r.get('success', False))
        matcher_total = len(matcher_results)
        matcher_success_rate = matcher_success / matcher_total if matcher_total > 0 else 0
        
        logger.info(f"🔍 최적화된 매칭기:")
        logger.info(f"   성공률: {matcher_success_rate:.2%} ({matcher_success}/{matcher_total})")
        
        # 방법별 분포
        method_counts = {}
        for result in matcher_results:
            if result.get('success') and result.get('method'):
                method = result['method']
                method_counts[method] = method_counts.get(method, 0) + 1
        
        for method, count in method_counts.items():
            logger.info(f"   {method}: {count}회")
        
        # 분류기 결과 분석
        classifier_success = sum(1 for r in classifier_results if r.get('success', False))
        classifier_total = len(classifier_results)
        classifier_success_rate = classifier_success / classifier_total if classifier_total > 0 else 0
        
        logger.info(f"\n🎯 분류기 통합:")
        logger.info(f"   성공률: {classifier_success_rate:.2%} ({classifier_success}/{classifier_total})")
        
        # 분류 타입별 분포
        type_counts = {}
        for result in classifier_results:
            if result.get('success') and result.get('input_type'):
                input_type = result['input_type']
                type_counts[input_type] = type_counts.get(input_type, 0) + 1
        
        for input_type, count in type_counts.items():
            logger.info(f"   {input_type}: {count}회")
        
        logger.info("="*60)

async def main():
    """메인 함수"""
    try:
        # 데이터베이스 연결
        db = await get_database()
        logger.info("데이터베이스 연결 완료")
        
        # 테스트기 생성
        tester = OptimizedPatternMatchingTester(db)
        
        # 테스트 데이터 설정
        await tester.setup_test_data()
        
        # 최적화된 매칭기 초기화
        await tester.optimized_matcher.initialize()
        await tester.classifier.initialize_matcher()
        
        # 테스트 질문들 (다양한 패턴)
        test_questions = [
            # 정확한 매칭 테스트
            "견적서 단위 변경",
            "직인 설정",
            "프린터 설정",
            
            # 유사한 표현 테스트
            "견적서 단위 바꾸고 싶어",
            "견적서 단위 수정하고 싶어",
            "직인 등록하고 싶어",
            "프린터 설치하고 싶어",
            
            # 부분 매칭 테스트
            "견적서 단위",
            "직인",
            "프린터",
            
            # 어려운 케이스 테스트
            "이거 견적서 단위 바꾸고 싶은데",
            "직인 설정하는 방법 알려주세요",
            "프린터 설정이 안돼요",
            
            # 매칭되지 않아야 하는 케이스
            "안녕하세요",
            "날씨가 좋네요",
            "한국 역사에 대해 알려주세요"
        ]
        
        # 1. 최적화된 매칭기 테스트
        matcher_results = await tester.test_optimized_matcher(test_questions)
        
        # 2. 분류기 통합 테스트
        classifier_results = await tester.test_classifier_integration(test_questions)
        
        # 3. 성능 벤치마크
        performance_results = await tester.performance_benchmark(test_questions[:10], iterations=5)
        
        # 4. 결과 요약
        tester.print_results_summary(matcher_results, classifier_results)
        
        logger.info("🎉 최적화된 패턴 매칭 테스트가 성공적으로 완료되었습니다!")
        
    except Exception as e:
        logger.error(f"메인 함수 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 