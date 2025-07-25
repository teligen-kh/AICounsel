"""
문맥 인식 분류기 (개선된 버전)
키워드 + 문맥 패턴 + 문맥 규칙 + LLM 하이브리드 접근
"""

from enum import Enum
from typing import Dict, List, Tuple, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
import re

class InputType(Enum):
    """입력 타입 분류"""
    CASUAL = "casual"              # 일상 대화 (인사말 포함)
    TECHNICAL = "technical"        # 기술적 질문
    NON_COUNSELING = "non_counseling"  # 비상담 질문
    PROFANITY = "profanity"        # 욕설
    UNKNOWN = "unknown"            # 기타

class ContextAwareClassifier:
    """개선된 문맥 인식 분류기"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.pattern_collection = db.context_patterns
        self.rule_collection = db.context_rules
        
        # 명확한 키워드 정의 (100% 확실한 경우만)
        self.clear_keywords = {
            'casual': [
                '안녕', '반갑', '좋은 아침', '좋은 오후', '좋은 저녁',
                '하이', 'hi', 'hello', '바쁘', '식사', '점심', '저녁',
                '커피', '차', '날씨', '기분', '피곤', '힘드시'
            ],
            'technical': [
                '프린터', '포스', 'pos', '키오스크', 'kiosk', '스캐너',
                '카드리더기', '영수증', '바코드', 'qr코드', 'qr',
                '프로그램', '소프트웨어', '하드웨어', '드라이버',
                '설치', '재설치', '업데이트', '백업', '복구'
            ],
            'non_counseling': [
                '한국', '대한민국', '일본', '중국', '미국', '역사',
                '지리', '수도', '인구', '면적', '언어', '문화',
                '정치', '경제', '사회', '과학', '수학', '물리'
            ],
            'profanity': [
                '바보', '멍청', '똥', '개', '새끼', '씨발', '병신',
                '미친', '미쳤', '돌았', '정신', '빡', '빡치'
            ]
        }
        
        # LLM 서비스 (나중에 주입)
        self.llm_service = None
    
    def inject_llm_service(self, llm_service):
        """LLM 서비스 주입"""
        self.llm_service = llm_service
    
    async def classify_input(self, user_input: str) -> Tuple[InputType, Dict[str, any]]:
        """순수 문맥 인식 분류 (키워드 제거)"""
        try:
            input_lower = user_input.lower()
            
            # 1단계: 명확한 키워드 체크 (기본 인사말만)
            clear_result = self._check_clear_keywords(input_lower)
            if clear_result:
                return clear_result
            
            # 2단계: 문맥 패턴 체크
            pattern_result = await self._check_context_patterns(user_input)
            if pattern_result:
                return pattern_result
            
            # 3단계: 문맥 규칙 체크
            rule_result = await self._check_context_rules(user_input)
            if rule_result:
                return rule_result
            
            # 4단계: LLM 분석 (최후 수단)
            if self.llm_service:
                llm_result = await self._classify_with_llm(user_input)
                if llm_result:
                    return llm_result
            
            # 5단계: 기본값
            return InputType.UNKNOWN, {
                "reason": "분류 불가",
                "matched_words": [],
                "source": "unknown"
            }
            
        except Exception as e:
            logging.error(f"문맥 인식 분류 중 오류: {str(e)}")
            return InputType.UNKNOWN, {
                "reason": "오류 발생",
                "matched_words": [],
                "source": "error"
            }
    
    def _check_clear_keywords(self, input_lower: str) -> Optional[Tuple[InputType, Dict]]:
        """명확한 키워드 체크"""
        for category, keywords in self.clear_keywords.items():
            for keyword in keywords:
                if keyword.lower() in input_lower:
                    input_type = InputType(category)
                    return input_type, {
                        "reason": f"명확한 {category} 키워드",
                        "matched_words": [keyword],
                        "source": "clear_keywords"
                    }
        return None
    
    async def _check_context_patterns(self, user_input: str) -> Optional[Tuple[InputType, Dict]]:
        """문맥 패턴 체크"""
        try:
            input_lower = user_input.lower()
            
            # 1. 정확한 매칭 우선 (더 구체적인 패턴)
            exact_matches = []
            async for pattern_doc in self.pattern_collection.find({"is_active": True}):
                pattern = pattern_doc["pattern"]
                if pattern.lower() == input_lower:
                    exact_matches.append((pattern_doc, 1.0))  # 정확한 매칭
                elif pattern.lower() in input_lower:
                    # 부분 매칭의 경우 패턴 길이로 우선순위 결정
                    match_ratio = len(pattern) / len(input_lower)
                    exact_matches.append((pattern_doc, match_ratio))
            
            if exact_matches:
                # 매칭 비율이 높은 순으로 정렬
                exact_matches.sort(key=lambda x: x[1], reverse=True)
                best_match = exact_matches[0]
                pattern_doc = best_match[0]
                match_ratio = best_match[1]
                
                pattern = pattern_doc["pattern"]
                context = pattern_doc["context"]
                input_type = InputType(context)
                
                # 사용 통계 업데이트
                await self._update_pattern_usage(pattern_doc["_id"])
                
                return input_type, {
                    "reason": f"문맥 패턴 매칭: {pattern} (매칭율: {match_ratio:.2f})",
                    "matched_words": [pattern],
                    "source": "context_patterns",
                    "pattern_id": str(pattern_doc["_id"]),
                    "accuracy": pattern_doc.get("accuracy", 0.9),
                    "match_ratio": match_ratio
                }
            
            return None
            
        except Exception as e:
            logging.error(f"문맥 패턴 체크 중 오류: {str(e)}")
            return None
    
    async def _check_context_rules(self, user_input: str) -> Optional[Tuple[InputType, Dict]]:
        """문맥 규칙 체크"""
        try:
            input_lower = user_input.lower()
            
            # 활성화된 규칙들을 우선순위 순으로 조회
            cursor = self.rule_collection.find(
                {"is_active": True}
            ).sort("priority", 1)
            
            async for rule_doc in cursor:
                rule_type = rule_doc["rule_type"]
                context = rule_doc["context"]
                
                if rule_type == "keyword_combination":
                    # 키워드 조합 규칙 체크
                    keywords = rule_doc["keywords"]
                    if all(keyword.lower() in input_lower for keyword in keywords):
                        input_type = InputType(context)
                        return input_type, {
                            "reason": f"키워드 조합 규칙: {' + '.join(keywords)}",
                            "matched_words": keywords,
                            "source": "context_rules",
                            "rule_id": str(rule_doc["_id"])
                        }
                
                elif rule_type == "sentence_pattern":
                    # 문장 패턴 규칙 체크
                    pattern = rule_doc["pattern"]
                    if pattern.lower() in input_lower:
                        input_type = InputType(context)
                        return input_type, {
                            "reason": f"문장 패턴 규칙: {pattern}",
                            "matched_words": [pattern],
                            "source": "context_rules",
                            "rule_id": str(rule_doc["_id"])
                        }
            
            return None
            
        except Exception as e:
            logging.error(f"문맥 규칙 체크 중 오류: {str(e)}")
            return None
    
    async def _classify_with_llm(self, message: str) -> Optional[Tuple[InputType, Dict]]:
        """LLM을 사용한 문맥 분석 (최후 수단)"""
        try:
            prompt = f"""다음 메시지를 4가지 카테고리로 분류해주세요:

- casual: 일상 대화, 인사말, AI 관련 질문, 상담사 연결 요청
- technical: 기술적 문제 해결, 시스템 관련 질문, 하드웨어/소프트웨어 문제
- non_counseling: 상담 범위를 벗어나는 일반 지식 질문, 역사/지리/과학 등
- profanity: 욕설 및 공격적 표현

메시지: "{message}"

답변 형식: casual 또는 technical 또는 non_counseling 또는 profanity
답변만 출력하고 다른 설명은 하지 마세요."""

            response = await self.llm_service.get_conversation_response(prompt)
            response_clean = response.strip().lower()
            
            # 응답 파싱
            if 'casual' in response_clean:
                return InputType.CASUAL, {
                    "reason": "LLM 문맥 분석 - 일상 대화",
                    "matched_words": [],
                    "source": "llm_analysis"
                }
            elif 'technical' in response_clean:
                return InputType.TECHNICAL, {
                    "reason": "LLM 문맥 분석 - 기술적 질문",
                    "matched_words": [],
                    "source": "llm_analysis"
                }
            elif 'non_counseling' in response_clean:
                return InputType.NON_COUNSELING, {
                    "reason": "LLM 문맥 분석 - 비상담 질문",
                    "matched_words": [],
                    "source": "llm_analysis"
                }
            elif 'profanity' in response_clean:
                return InputType.PROFANITY, {
                    "reason": "LLM 문맥 분석 - 욕설",
                    "matched_words": [],
                    "source": "llm_analysis"
                }
            
            return None
            
        except Exception as e:
            logging.error(f"LLM 분류 중 오류: {str(e)}")
            return None
    

    
    async def _update_pattern_usage(self, pattern_id):
        """패턴 사용 통계 업데이트"""
        try:
            await self.pattern_collection.update_one(
                {"_id": pattern_id},
                {"$inc": {"usage_count": 1}}
            )
        except Exception as e:
            logging.error(f"패턴 사용 통계 업데이트 중 오류: {str(e)}")
    
    # ===== 관리 메서드들 =====
    
    async def add_context_pattern(self, pattern: str, context: str, description: str, priority: int = 2):
        """새로운 문맥 패턴 추가"""
        try:
            from datetime import datetime
            pattern_doc = {
                "pattern": pattern,
                "context": context,
                "description": description,
                "priority": priority,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "usage_count": 0,
                "accuracy": 0.9,
                "is_active": True
            }
            result = await self.pattern_collection.insert_one(pattern_doc)
            logging.info(f"새로운 문맥 패턴 추가: {pattern} -> {context}")
            return result.inserted_id
        except Exception as e:
            logging.error(f"문맥 패턴 추가 중 오류: {str(e)}")
            return None
    
    async def add_context_rule(self, rule_type: str, keywords: List[str], context: str, description: str, priority: int = 2):
        """새로운 문맥 규칙 추가"""
        try:
            from datetime import datetime
            rule_doc = {
                "rule_type": rule_type,
                "keywords": keywords if rule_type == "keyword_combination" else None,
                "pattern": keywords[0] if rule_type == "sentence_pattern" else None,
                "context": context,
                "description": description,
                "priority": priority,
                "is_active": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            result = await self.rule_collection.insert_one(rule_doc)
            logging.info(f"새로운 문맥 규칙 추가: {rule_type} -> {context}")
            return result.inserted_id
        except Exception as e:
            logging.error(f"문맥 규칙 추가 중 오류: {str(e)}")
            return None
    
    async def get_pattern_stats(self):
        """패턴 사용 통계 조회"""
        try:
            stats = []
            async for pattern in self.pattern_collection.find({}).sort("usage_count", -1):
                stats.append({
                    "pattern": pattern["pattern"],
                    "context": pattern["context"],
                    "usage_count": pattern["usage_count"],
                    "accuracy": pattern.get("accuracy", 0.9)
                })
            return stats
        except Exception as e:
            logging.error(f"패턴 통계 조회 중 오류: {str(e)}")
            return [] 