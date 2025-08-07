#!/usr/bin/env python3
"""
최적화된 패턴 매칭 서비스
MongoDB Text Search + 벡터 검색 조합으로 속도와 정확도 최적화
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Set
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import asyncio

logger = logging.getLogger(__name__)

class OptimizedPatternMatcher:
    """최적화된 패턴 매칭기"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.pattern_collection = db.context_patterns
        self.cache = {}  # 간단한 메모리 캐시
        self.cache_ttl = 300  # 5분 캐시 TTL
        self.last_cache_update = 0
        
        # TF-IDF 벡터라이저 (한국어 최적화)
        self.vectorizer = TfidfVectorizer(
            analyzer='word',
            ngram_range=(1, 3),  # 1-3그램으로 단어 조합 캐치
            min_df=1,
            max_df=0.9,
            stop_words=None,  # 한국어는 불용어 처리가 복잡하므로 제외
            lowercase=True
        )
        
        # 패턴 벡터 캐시
        self.pattern_vectors = None
        self.pattern_texts = []
        self.pattern_docs = []
        
        # 성능 통계
        self.stats = {
            'text_search_count': 0,
            'vector_search_count': 0,
            'cache_hits': 0,
            'total_queries': 0,
            'avg_response_time': 0
        }
    
    async def initialize(self):
        """패턴 매칭기 초기화"""
        try:
            logger.info("🔧 최적화된 패턴 매칭기 초기화 시작")
            
            # 1. MongoDB Text Index 생성 (한 번만)
            await self._ensure_text_index()
            
            # 2. 패턴 데이터 로드 및 벡터화
            await self._load_and_vectorize_patterns()
            
            logger.info(f"✅ 패턴 매칭기 초기화 완료 - {len(self.pattern_docs)}개 패턴 로드")
            
        except Exception as e:
            logger.error(f"패턴 매칭기 초기화 실패: {e}")
            raise
    
    async def _ensure_text_index(self):
        """MongoDB Text Index 생성"""
        try:
            # 기존 인덱스 확인
            indexes = await self.pattern_collection.list_indexes().to_list()
            has_text_index = any(idx.get('name') == 'pattern_text' for idx in indexes)
            
            if not has_text_index:
                # Text Index 생성 (한국어 지원)
                await self.pattern_collection.create_index([
                    ("pattern", "text")
                ], name="pattern_text", default_language="none")
                
                logger.info("✅ MongoDB Text Index 생성 완료")
            else:
                logger.info("✅ MongoDB Text Index 이미 존재")
                
        except Exception as e:
            logger.error(f"Text Index 생성 실패: {e}")
    
    async def _load_and_vectorize_patterns(self):
        """패턴 데이터 로드 및 벡터화"""
        try:
            # 모든 패턴 로드
            cursor = self.pattern_collection.find({})
            self.pattern_docs = await cursor.to_list(length=None)
            
            if not self.pattern_docs:
                logger.warning("⚠️ 로드할 패턴이 없습니다")
                return
            
            # 패턴 텍스트 추출
            self.pattern_texts = [doc['pattern'] for doc in self.pattern_docs]
            
            # TF-IDF 벡터화
            self.pattern_vectors = self.vectorizer.fit_transform(self.pattern_texts)
            
            logger.info(f"✅ {len(self.pattern_docs)}개 패턴 벡터화 완료")
            
        except Exception as e:
            logger.error(f"패턴 로드 및 벡터화 실패: {e}")
            raise
    
    async def find_best_match(self, user_input: str, threshold: float = 0.3) -> Optional[Tuple[Dict, float, str]]:
        """
        사용자 입력에 대한 최적 패턴 매칭
        
        Returns:
            Tuple[pattern_doc, similarity_score, method_used] or None
        """
        start_time = datetime.now()
        
        try:
            self.stats['total_queries'] += 1
            
            # 1. 캐시 체크
            cache_key = user_input.lower().strip()
            if cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                if (datetime.now() - cache_entry['timestamp']).seconds < self.cache_ttl:
                    self.stats['cache_hits'] += 1
                    return cache_entry['result']
            
            # 2. 1단계: MongoDB Text Search (빠른 필터링)
            text_candidates = await self._text_search(user_input)
            
            if not text_candidates:
                # Text Search 결과가 없으면 벡터 검색으로 확장
                vector_result = await self._vector_search(user_input, threshold)
                if vector_result:
                    pattern_doc, score, method = vector_result
                    result = (pattern_doc, score, method)
                    self._update_cache(cache_key, result)
                    return result
                return None
            
            # 3. 2단계: Text Search 후보들에 대해 벡터 검색으로 정확도 향상
            best_match = None
            best_score = 0
            best_method = "text_search"
            
            for pattern_doc in text_candidates:
                vector_score = await self._calculate_similarity(user_input, pattern_doc['pattern'])
                
                # Text Search 결과에 가중치 부여 (빠른 매칭 우선)
                weighted_score = vector_score * 1.2 if vector_score > threshold else vector_score
                
                if weighted_score > best_score:
                    best_score = weighted_score
                    best_match = pattern_doc
                    best_method = "hybrid"
            
            # 4. 결과 반환
            if best_match and best_score >= threshold:
                result = (best_match, best_score, best_method)
                self._update_cache(cache_key, result)
                
                # 성능 통계 업데이트
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                self._update_stats(response_time)
                
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"패턴 매칭 중 오류: {e}")
            return None
    
    async def _text_search(self, user_input: str) -> List[Dict]:
        """MongoDB Text Search 수행"""
        try:
            self.stats['text_search_count'] += 1
            
            # Text Search 쿼리 (한국어 최적화)
            query = {
                "$text": {
                    "$search": user_input,
                    "$language": "none"  # 한국어는 언어 감지 비활성화
                }
            }
            
            # Text Score로 정렬하여 상위 결과만 반환
            cursor = self.pattern_collection.find(query).sort([
                ("score", {"$meta": "textScore"})
            ]).limit(10)  # 상위 10개만
            
            results = await cursor.to_list(length=10)
            
            # Text Score가 1.0 이상인 결과만 반환 (의미있는 매칭)
            filtered_results = [
                doc for doc in results 
                if doc.get('score', 0) >= 1.0
            ]
            
            logger.debug(f"Text Search 결과: {len(filtered_results)}개")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Text Search 실패: {e}")
            return []
    
    async def _vector_search(self, user_input: str, threshold: float) -> Optional[Tuple[Dict, float, str]]:
        """벡터 검색 수행"""
        try:
            self.stats['vector_search_count'] += 1
            
            if not self.pattern_vectors or not self.pattern_texts:
                return None
            
            # 사용자 입력 벡터화
            user_vector = self.vectorizer.transform([user_input])
            
            # 코사인 유사도 계산
            similarities = cosine_similarity(user_vector, self.pattern_vectors).flatten()
            
            # 최고 유사도 패턴 찾기
            best_idx = np.argmax(similarities)
            best_score = similarities[best_idx]
            
            if best_score >= threshold:
                pattern_doc = self.pattern_docs[best_idx]
                logger.debug(f"벡터 검색 결과: {pattern_doc['pattern']} (유사도: {best_score:.3f})")
                return pattern_doc, best_score, "vector_search"
            
            return None
            
        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            return None
    
    async def _calculate_similarity(self, user_input: str, pattern: str) -> float:
        """두 텍스트 간의 유사도 계산"""
        try:
            if not self.pattern_vectors or not self.pattern_texts:
                return 0.0
            
            # 벡터화
            user_vector = self.vectorizer.transform([user_input])
            pattern_vector = self.vectorizer.transform([pattern])
            
            # 코사인 유사도
            similarity = cosine_similarity(user_vector, pattern_vector)[0][0]
            return float(similarity)
            
        except Exception as e:
            logger.error(f"유사도 계산 실패: {e}")
            return 0.0
    
    def _update_cache(self, key: str, result: Tuple):
        """캐시 업데이트"""
        self.cache[key] = {
            'result': result,
            'timestamp': datetime.now()
        }
        
        # 캐시 크기 제한 (메모리 관리)
        if len(self.cache) > 1000:
            # 가장 오래된 항목 제거
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]
    
    def _update_stats(self, response_time: float):
        """성능 통계 업데이트"""
        current_avg = self.stats['avg_response_time']
        total_queries = self.stats['total_queries']
        
        # 이동 평균 계산
        self.stats['avg_response_time'] = (
            (current_avg * (total_queries - 1) + response_time) / total_queries
        )
    
    async def refresh_patterns(self):
        """패턴 데이터 새로고침"""
        try:
            logger.info("🔄 패턴 데이터 새로고침 시작")
            
            # 캐시 클리어
            self.cache.clear()
            self.last_cache_update = datetime.now().timestamp()
            
            # 패턴 재로드 및 벡터화
            await self._load_and_vectorize_patterns()
            
            logger.info("✅ 패턴 데이터 새로고침 완료")
            
        except Exception as e:
            logger.error(f"패턴 새로고침 실패: {e}")
    
    def get_performance_stats(self) -> Dict:
        """성능 통계 반환"""
        return {
            **self.stats,
            'cache_size': len(self.cache),
            'pattern_count': len(self.pattern_docs),
            'cache_hit_rate': (
                self.stats['cache_hits'] / max(self.stats['total_queries'], 1)
            )
        }
    
    async def add_pattern(self, pattern: str, context: str, description: str = ""):
        """새 패턴 추가"""
        try:
            # MongoDB에 패턴 추가
            pattern_doc = {
                "pattern": pattern,
                "context": context,
                "description": description,
                "created_at": datetime.utcnow(),
                "usage_count": 0,
                "accuracy": 0.9
            }
            
            await self.pattern_collection.insert_one(pattern_doc)
            
            # 패턴 데이터 새로고침
            await self.refresh_patterns()
            
            logger.info(f"✅ 새 패턴 추가: {pattern}")
            
        except Exception as e:
            logger.error(f"패턴 추가 실패: {e}")
    
    async def optimize_patterns(self):
        """패턴 최적화 (사용 빈도 기반)"""
        try:
            logger.info("🔧 패턴 최적화 시작")
            
            # 사용 빈도가 낮은 패턴들 찾기
            low_usage_patterns = await self.pattern_collection.find({
                "usage_count": {"$lt": 5}
            }).to_list(length=None)
            
            logger.info(f"사용 빈도 낮은 패턴: {len(low_usage_patterns)}개")
            
            # 정확도가 낮은 패턴들 찾기
            low_accuracy_patterns = await self.pattern_collection.find({
                "accuracy": {"$lt": 0.7}
            }).to_list(length=None)
            
            logger.info(f"정확도 낮은 패턴: {len(low_accuracy_patterns)}개")
            
            # 최적화 제안
            optimization_suggestions = []
            
            for pattern in low_usage_patterns:
                optimization_suggestions.append({
                    "pattern_id": str(pattern["_id"]),
                    "pattern": pattern["pattern"],
                    "issue": "low_usage",
                    "suggestion": "패턴을 더 구체적으로 수정하거나 제거 고려"
                })
            
            for pattern in low_accuracy_patterns:
                optimization_suggestions.append({
                    "pattern_id": str(pattern["_id"]),
                    "pattern": pattern["pattern"],
                    "issue": "low_accuracy",
                    "suggestion": "패턴을 더 정확하게 수정"
                })
            
            logger.info(f"✅ 패턴 최적화 완료 - {len(optimization_suggestions)}개 제안")
            return optimization_suggestions
            
        except Exception as e:
            logger.error(f"패턴 최적화 실패: {e}")
            return [] 