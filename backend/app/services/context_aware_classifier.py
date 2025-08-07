"""
문맥 인식 분류기 (개선된 버전)
키워드 + 문맥 패턴 + 문맥 규칙 + LLM 하이브리드 접근
"""

from enum import Enum
from typing import Dict, List, Tuple, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
import re
from .optimized_pattern_matcher import OptimizedPatternMatcher

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
        
        # 최적화된 패턴 매칭기 초기화
        self.optimized_matcher = OptimizedPatternMatcher(db)
        self.matcher_initialized = False
        
        # 명확한 키워드 정의 (100% 확실한 경우만)
        self.clear_keywords = {
            'casual': [
                '안녕', '반갑', '좋은 아침', '좋은 오후', '좋은 저녁',
                '하이', 'hi', 'hello', '바쁘', '식사', '점심', '저녁',
                '커피', '차', '날씨', '기분', '피곤', '힘드시',
                '감사', '고맙', '잘 지내', '상담사 연결',
                '어', '어?', '아', '아?', '음', '음?', '그래', '그래?', '정말', '정말?'
            ],
            'technical': [
                '프린터', '포스', 'pos', '키오스크', 'kiosk', '스캐너',
                '카드리더기', '영수증', '바코드', 'qr코드', 'qr',
                '프로그램', '소프트웨어', '하드웨어', '드라이버',
                '설치', '재설치', '업데이트', '백업', '복구',
                '시스템', '클라우드', '결제', '오류', '문제', '에러', '실패',
                '매출', '매입', '재고', '회계', '코드관리', '상품', '엑셀',
                '쇼핑몰', '매출작업', '통신', '카드', '영수증', '바코드',
                '법인결재', '결재', '설정', '관리', '작업', '방법', '해결'
            ],
            'non_counseling': [
                '한국', '대한민국', '일본', '중국', '미국', '역사',
                '지리', '수도', '인구', '면적', '언어', '문화',
                '정치', '경제', '사회', '과학', '수학', '물리',
                '요리', '레시피', '운동', '여행', '영화', '음악', '책', '게임', '스포츠'
            ],
            'profanity': [
                '바보', '멍청', '똥', '새끼', '씨발', '병신',
                '미친', '미쳤', '돌았', '정신', '빡치'
            ]
        }
        
        # LLM 서비스 (나중에 주입)
        self.llm_service = None
    
    def inject_llm_service(self, llm_service):
        """LLM 서비스 주입"""
        self.llm_service = llm_service
    
    async def initialize_matcher(self):
        """최적화된 패턴 매칭기 초기화"""
        try:
            if not self.matcher_initialized:
                await self.optimized_matcher.initialize()
                self.matcher_initialized = True
                logging.info("✅ 최적화된 패턴 매칭기 초기화 완료")
        except Exception as e:
            logging.error(f"패턴 매칭기 초기화 실패: {e}")
            # 실패 시 기존 방식으로 fallback
            self.matcher_initialized = False
    
    async def classify_input(self, user_input: str) -> Tuple[InputType, Dict[str, any]]:
        """올바른 하이브리드 문맥 인식 분류"""
        try:
            input_lower = user_input.lower()
            
            # 1단계: casual/profanity 체크 (명확한 키워드만)
            casual_profanity_result = self._check_casual_profanity_keywords(input_lower)
            if casual_profanity_result:
                return casual_profanity_result
            
            # 2단계: context_patterns 매칭 체크
            pattern_result = await self._check_context_patterns(user_input)
            if pattern_result:
                return pattern_result
            
            # 3단계: 기본값 (context_patterns 매칭 안되면 non_counseling)
            return InputType.NON_COUNSELING, {
                "reason": "context_patterns 매칭 없음 - 비상담 질문으로 분류",
                "matched_words": [],
                "source": "default_non_counseling"
            }
            
        except Exception as e:
            logging.error(f"문맥 인식 분류 중 오류: {str(e)}")
            return InputType.UNKNOWN, {
                "reason": "오류 발생",
                "matched_words": [],
                "source": "error"
            }
            
        except Exception as e:
            logging.error(f"문맥 인식 분류 중 오류: {str(e)}")
            return InputType.UNKNOWN, {
                "reason": "오류 발생",
                "matched_words": [],
                "source": "error"
            }
    
    def _check_casual_profanity_keywords(self, input_lower: str) -> Optional[Tuple[InputType, Dict]]:
        """casual/profanity 키워드만 체크"""
        # casual 키워드 체크
        for keyword in self.clear_keywords['casual']:
            if keyword.lower() in input_lower:
                return InputType.CASUAL, {
                    "reason": "명확한 casual 키워드",
                    "matched_words": [keyword],
                    "source": "clear_keywords"
                }
        
        # profanity 키워드 체크
        for keyword in self.clear_keywords['profanity']:
            if keyword.lower() in input_lower:
                return InputType.PROFANITY, {
                    "reason": "명확한 profanity 키워드",
                    "matched_words": [keyword],
                    "source": "clear_keywords"
                }
        
        return None
    
    def _is_word_boundary_match(self, text: str, pattern: str) -> bool:
        """단어 경계를 고려한 패턴 매칭"""
        import re
        
        # 패턴을 단어 단위로 분리
        pattern_words = pattern.split()
        
        # 각 패턴 단어가 텍스트에서 단어 경계와 함께 존재하는지 확인
        for word in pattern_words:
            # 단어 경계를 고려한 정규식 패턴
            word_pattern = r'\b' + re.escape(word) + r'\b'
            if not re.search(word_pattern, text):
                return False
        
        return True
    
    async def _check_context_patterns(self, user_input: str) -> Optional[Tuple[InputType, Dict]]:
        """문맥 패턴 체크 (최적화된 매칭기 사용)"""
        try:
            # 최적화된 매칭기 초기화 확인
            if not self.matcher_initialized:
                await self.initialize_matcher()
            
            # 최적화된 매칭기 사용
            if self.matcher_initialized:
                result = await self.optimized_matcher.find_best_match(user_input, threshold=0.3)
                
                if result:
                    pattern_doc, similarity_score, method = result
                    
                    pattern = pattern_doc["pattern"]
                    context = pattern_doc["context"]
                    input_type = InputType(context)
                    
                    # 사용 통계 업데이트
                    await self._update_pattern_usage(pattern_doc["_id"])
                    
                    return input_type, {
                        "reason": f"최적화된 패턴 매칭: {pattern} (유사도: {similarity_score:.3f}, 방법: {method})",
                        "matched_words": [pattern],
                        "source": "optimized_context_patterns",
                        "pattern_id": str(pattern_doc["_id"]),
                        "accuracy": pattern_doc.get("accuracy", 0.9),
                        "similarity_score": similarity_score,
                        "method": method
                    }
            
            # 최적화된 매칭기 실패 시 기존 방식으로 fallback
            logging.warning("최적화된 매칭기 실패, 기존 방식으로 fallback")
            return await self._fallback_pattern_check(user_input)
            
        except Exception as e:
            logging.error(f"문맥 패턴 체크 중 오류: {str(e)}")
            # 오류 발생 시 기존 방식으로 fallback
            return await self._fallback_pattern_check(user_input)
    
    async def _fallback_pattern_check(self, user_input: str) -> Optional[Tuple[InputType, Dict]]:
        """기존 방식의 패턴 체크 (fallback)"""
        try:
            input_lower = user_input.lower()
            
            # 1. 정확한 매칭 우선 (더 구체적인 패턴)
            exact_matches = []
            async for pattern_doc in self.pattern_collection.find({}):
                pattern = pattern_doc["pattern"]
                pattern_lower = pattern.lower()
                
                if pattern_lower == input_lower:
                    exact_matches.append((pattern_doc, 1.0))  # 정확한 매칭
                elif self._is_word_boundary_match(input_lower, pattern_lower):
                    # 단어 경계 매칭 (더 정확한 부분 매칭)
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
                    "reason": f"기존 패턴 매칭: {pattern} (매칭율: {match_ratio:.2f})",
                    "matched_words": [pattern],
                    "source": "fallback_context_patterns",
                    "pattern_id": str(pattern_doc["_id"]),
                    "accuracy": pattern_doc.get("accuracy", 0.9),
                    "match_ratio": match_ratio
                }
            
            return None
            
        except Exception as e:
            logging.error(f"기존 패턴 체크 중 오류: {str(e)}")
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
            # 기본 키워드 체크 (LLM 호출 전)
            input_lower = message.lower()
            
            # 인사말 체크
            greeting_keywords = ['안녕', '반갑', '좋은', '하이', 'hi', 'hello', '감사', '고맙', '잘 지내', '바쁘', '식사', '점심', '저녁', '커피', '차', '날씨', '기분', '피곤', '힘드시']
            if any(keyword in input_lower for keyword in greeting_keywords):
                return InputType.CASUAL, {
                    "reason": "인사말 키워드 감지",
                    "matched_words": [kw for kw in greeting_keywords if kw in input_lower],
                    "source": "basic_keywords"
                }
            
            # 비상담 키워드 체크
            non_counseling_keywords = ['한국', '대한민국', '일본', '중국', '미국', '역사', '지리', '수도', '인구', '면적', '언어', '문화', '정치', '경제', '사회', '과학', '수학', '물리', '화학', '생물', '요리', '레시피', '운동', '여행', '영화', '음악', '책', '게임', '스포츠']
            if any(keyword in input_lower for keyword in non_counseling_keywords):
                return InputType.NON_COUNSELING, {
                    "reason": "비상담 키워드 감지",
                    "matched_words": [kw for kw in non_counseling_keywords if kw in input_lower],
                    "source": "basic_keywords"
                }
            
            # 욕설 키워드 체크 (더 정확하게)
            profanity_keywords = ['씨발', '병신', '미친', '미쳤', '돌았', '정신', '빡치', '바보', '멍청', '똥', '새끼']
            if any(keyword in input_lower for keyword in profanity_keywords):
                return InputType.PROFANITY, {
                    "reason": "욕설 키워드 감지",
                    "matched_words": [kw for kw in profanity_keywords if kw in input_lower],
                    "source": "basic_keywords"
                }
            
            # LLM 호출 (기본 체크로 분류되지 않은 경우)
            if self.llm_service:
                prompt = f"""다음 메시지를 4가지 카테고리로 분류해주세요. 정확히 하나의 카테고리만 선택하세요:

- casual: 일상 대화, 인사말, AI 관련 질문, 상담사 연결 요청, 감사 인사
- technical: 기술적 문제 해결, 시스템 관련 질문, 하드웨어/소프트웨어 문제, 업무 관련 질문
- non_counseling: 상담 범위를 벗어나는 일반 지식 질문, 역사/지리/과학/요리/운동/여행 등
- profanity: 욕설 및 공격적 표현

메시지: "{message}"

답변은 반드시 다음 중 하나만 입력하세요: casual, technical, non_counseling, profanity

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
    
    async def _pre_classify_with_llm(self, message: str) -> Optional[Tuple[InputType, Dict]]:
        """LLM을 사용한 사전 분류 (technical/non_counseling 구분)"""
        try:
            prompt = f"""다음 메시지가 기술적 상담 질문인지 일반 지식 질문인지 구분해주세요:

기술적 상담 질문 (technical): 
- 포스, 프린터, 키오스크, 카드리더기, 영수증, 바코드, QR코드
- 설치, 설정, 오류, 문제 해결, 드라이버, 재설치, 백업, 복구
- 프로그램, 소프트웨어, 하드웨어, 시스템 설정
- 법인결재, 결재, 매출, 매입, 재고, 회계 관련 기능

일반 지식 질문 (non_counseling): 
- 영화, 드라마, 음악, 예술, 문화
- 역사, 지리, 과학, 수학, 물리, 화학
- 정치, 경제, 사회, 인물, 사건
- 날씨, 요리, 여행, 스포츠, 게임

메시지: "{message}"

답변 형식: technical 또는 non_counseling
답변만 출력하고 다른 설명은 하지 마세요."""

            response = await self.llm_service.get_conversation_response(prompt)
            response_clean = response.strip().lower()
            
            # 응답 파싱
            if 'technical' in response_clean:
                return InputType.TECHNICAL, {
                    "reason": "LLM 사전 분류 - 기술적 질문",
                    "matched_words": [],
                    "source": "llm_pre_classification"
                }
            elif 'non_counseling' in response_clean:
                return InputType.NON_COUNSELING, {
                    "reason": "LLM 사전 분류 - 일반 지식 질문",
                    "matched_words": [],
                    "source": "llm_pre_classification"
                }
            
            return None
            
        except Exception as e:
            logging.error(f"LLM 사전 분류 중 오류: {str(e)}")
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
            stats = await self.pattern_collection.aggregate([
                {"$group": {
                    "_id": "$context",
                    "count": {"$sum": 1},
                    "total_usage": {"$sum": "$usage_count"}
                }}
            ]).to_list(length=None)
            
            # 최적화된 매칭기 성능 통계
            matcher_stats = {}
            if self.matcher_initialized:
                matcher_stats = self.optimized_matcher.get_performance_stats()
            
            return {
                "pattern_stats": stats,
                "optimized_matcher_stats": matcher_stats,
                "matcher_initialized": self.matcher_initialized
            }
        except Exception as e:
            logging.error(f"패턴 통계 조회 중 오류: {str(e)}")
            return {}
    
    def get_response_template(self, input_type: InputType) -> str:
        """입력 타입에 따른 템플릿 응답 반환"""
        templates = {
            InputType.CASUAL: "안녕하세요! 어떻게 도와드릴까요?",
            InputType.TECHNICAL: "전문적인 상담이 필요하시군요. 상담사에게 연결해드리겠습니다.",
            InputType.NON_COUNSELING: "죄송합니다. 저는 텔리젠 AI 상담사로 해당 질문은 답변 드릴 수 없습니다.",
            InputType.PROFANITY: "욕설을 하시면 응대를 할 수 없습니다. 30분 후 재문의 바랍니다.",
            InputType.UNKNOWN: "죄송합니다. 전문 상담사에게 문의해주세요."
        }
        
        return templates.get(input_type, "죄송합니다. 전문 상담사에게 문의해주세요.") 