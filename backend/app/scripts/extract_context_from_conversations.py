"""
conversations 테이블에서 문맥 패턴 추출
실제 대화 데이터를 기반으로 context_patterns에 패턴 추가
"""

import asyncio
import motor.motor_asyncio
from datetime import datetime
import logging
import re
from typing import List, Dict, Set

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextPatternExtractor:
    """대화 데이터에서 문맥 패턴을 추출하는 클래스"""
    
    def __init__(self, db):
        self.db = db
        self.conversations_collection = db.conversations
        self.patterns_collection = db.context_patterns
        self.rules_collection = db.context_rules
        
        # 기술적 문제 키워드 (요청내용에서 추출)
        self.technical_keywords = {
            '포스', 'pos', '카드', '결제', '결재', '프린터', '스캐너', '키오스크', 'kiosk',
            '설치', '재설치', '업데이트', '오류', '에러', '문제', '안됨', '안돼요',
            '검색', '조회', '연결', '인터넷', '네트워크', '백업', '복구', '드라이버',
            '설정', '관리', '데이터', 'db', '데이터베이스', '바코드', 'qr', 'qr코드',
            '영수증', '출력', '단말기', '리더기', '카드리더기', '포트', 'usb'
        }
        
        # 일상 대화 키워드
        self.casual_keywords = {
            '안녕', '반갑', '하이', 'hi', 'hello', '감사', '고마워', '고맙습니다',
            '상담사', '사람', '대화', '연결해줘', '연결해 주세요', '도움', '도와주세요',
            'ai', '인공지능', '로봇', '봇', '봇인가요', '사람인가요'
        }
        
        # 비상담 키워드
        self.non_counseling_keywords = {
            '한국', '대한민국', '일본', '중국', '미국', '역사', '지리', '수도',
            '정치', '경제', '사회', '과학', '수학', '물리', '화학', '생물',
            '음식', '요리', '영화', '드라마', '음악', '운동', '스포츠'
        }
    
    async def extract_patterns_from_conversations(self):
        """conversations에서 문맥 패턴 추출"""
        try:
            logger.info("conversations에서 문맥 패턴 추출 시작...")
            
            # 기존 패턴 백업
            existing_patterns = set()
            async for pattern in self.patterns_collection.find({}):
                existing_patterns.add(pattern["pattern"])
            
            logger.info(f"기존 패턴 수: {len(existing_patterns)}")
            
            # conversations에서 messages 추출
            new_patterns = []
            technical_patterns = []
            casual_patterns = []
            
            async for conv in self.conversations_collection.find({}):
                messages = conv.get("messages", [])
                if not messages:
                    continue
                
                # 사용자 메시지만 추출
                user_messages = []
                for msg in messages:
                    if msg.get("role") == "user":
                        content = msg.get("content", "").strip()
                        if content:
                            user_messages.append(content)
                
                if not user_messages:
                    continue
                
                # 첫 번째 사용자 메시지를 요청내용으로 사용
                request_content = user_messages[0]
                
                # 패턴 정규화
                normalized_pattern = self._normalize_pattern(request_content)
                if not normalized_pattern or normalized_pattern in existing_patterns:
                    continue
                
                # 문맥 분류
                context = self._classify_context(request_content)
                
                if context == "technical":
                    technical_patterns.append({
                        "pattern": normalized_pattern,
                        "original": request_content,
                        "context": context
                    })
                elif context == "casual":
                    casual_patterns.append({
                        "pattern": normalized_pattern,
                        "original": request_content,
                        "context": context
                    })
                
                new_patterns.append({
                    "pattern": normalized_pattern,
                    "original": request_content,
                    "context": context
                })
            
            logger.info(f"추출된 패턴 수: {len(new_patterns)}")
            logger.info(f"  - technical: {len(technical_patterns)}")
            logger.info(f"  - casual: {len(casual_patterns)}")
            
            # 우선순위가 높은 패턴들만 선택 (길이와 정확도 기준)
            selected_patterns = self._select_best_patterns(new_patterns)
            
            # context_patterns에 추가
            added_count = await self._add_patterns_to_db(selected_patterns)
            
            # 키워드 조합 규칙 생성
            rules_count = await self._generate_keyword_rules(technical_patterns, casual_patterns)
            
            logger.info(f"✅ 패턴 추출 완료!")
            logger.info(f"   - 추가된 패턴: {added_count}개")
            logger.info(f"   - 생성된 규칙: {rules_count}개")
            
            return {
                "total_patterns": len(new_patterns),
                "added_patterns": added_count,
                "generated_rules": rules_count
            }
            
        except Exception as e:
            logger.error(f"패턴 추출 중 오류: {str(e)}")
            raise
    
    def _normalize_pattern(self, text: str) -> str:
        """텍스트를 패턴으로 정규화"""
        if not text:
            return ""
        
        # 기본 정규화
        normalized = text.lower().strip()
        
        # 특수문자 제거 (하지만 한글은 유지)
        normalized = re.sub(r'[^\w\s가-힣]', '', normalized)
        
        # 연속된 공백을 하나로
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # 너무 짧거나 긴 패턴 제외
        if len(normalized) < 3 or len(normalized) > 50:
            return ""
        
        return normalized
    
    def _classify_context(self, text: str) -> str:
        """텍스트의 문맥을 분류"""
        text_lower = text.lower()
        
        # 기술적 문제 키워드 체크
        technical_count = sum(1 for keyword in self.technical_keywords if keyword in text_lower)
        
        # 일상 대화 키워드 체크
        casual_count = sum(1 for keyword in self.casual_keywords if keyword in text_lower)
        
        # 비상담 키워드 체크
        non_counseling_count = sum(1 for keyword in self.non_counseling_keywords if keyword in text_lower)
        
        # 분류 결정
        if technical_count > 0:
            return "technical"
        elif casual_count > 0:
            return "casual"
        elif non_counseling_count > 0:
            return "non_counseling"
        else:
            # 기본적으로 technical로 분류 (상담 데이터이므로)
            return "technical"
    
    def _select_best_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """가장 좋은 패턴들 선택"""
        selected = []
        
        for pattern_info in patterns:
            pattern = pattern_info["pattern"]
            context = pattern_info["context"]
            
            # 선택 기준
            score = 0
            
            # 길이 점수 (적당한 길이 선호)
            if 5 <= len(pattern) <= 20:
                score += 3
            elif 3 <= len(pattern) <= 30:
                score += 1
            
            # 키워드 포함 점수
            if context == "technical":
                tech_keywords = sum(1 for kw in self.technical_keywords if kw in pattern)
                score += tech_keywords * 2
            elif context == "casual":
                casual_keywords = sum(1 for kw in self.casual_keywords if kw in pattern)
                score += casual_keywords * 2
            
            # 특정 패턴 선호
            if any(keyword in pattern for keyword in ["안됨", "안돼요", "오류", "에러", "문제"]):
                score += 2
            
            if any(keyword in pattern for keyword in ["상담사", "연결", "대화"]):
                score += 2
            
            # 점수가 높은 패턴만 선택
            if score >= 2:
                pattern_info["score"] = score
                selected.append(pattern_info)
        
        # 점수 순으로 정렬
        selected.sort(key=lambda x: x["score"], reverse=True)
        
        # 상위 50개만 선택
        return selected[:50]
    
    async def _add_patterns_to_db(self, patterns: List[Dict]) -> int:
        """패턴을 DB에 추가"""
        added_count = 0
        
        for pattern_info in patterns:
            try:
                # 중복 체크
                existing = await self.patterns_collection.find_one({"pattern": pattern_info["pattern"]})
                if existing:
                    continue
                
                # 패턴 추가
                pattern_doc = {
                    "pattern": pattern_info["pattern"],
                    "context": pattern_info["context"],
                    "description": f"conversations에서 추출: {pattern_info['original'][:50]}...",
                    "priority": 2,  # 추출된 패턴은 우선순위 2
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "usage_count": 0,
                    "accuracy": 0.85,  # 추출된 패턴은 정확도 0.85
                    "is_active": True,
                    "source": "conversations_extraction"
                }
                
                await self.patterns_collection.insert_one(pattern_doc)
                added_count += 1
                
            except Exception as e:
                logger.error(f"패턴 추가 중 오류: {str(e)}")
                continue
        
        return added_count
    
    async def _generate_keyword_rules(self, technical_patterns: List[Dict], casual_patterns: List[Dict]) -> int:
        """키워드 조합 규칙 생성"""
        rules_count = 0
        
        # 기술적 문제 키워드 조합 규칙
        tech_keywords = set()
        for pattern_info in technical_patterns:
            pattern = pattern_info["pattern"]
            for keyword in self.technical_keywords:
                if keyword in pattern:
                    tech_keywords.add(keyword)
        
        # 상담사 관련 키워드 조합 규칙
        casual_keywords = set()
        for pattern_info in casual_patterns:
            pattern = pattern_info["pattern"]
            for keyword in self.casual_keywords:
                if keyword in pattern:
                    casual_keywords.add(keyword)
        
        # 규칙 생성
        rules_to_add = []
        
        # 기술적 문제 키워드 조합 (2개씩)
        tech_keywords_list = list(tech_keywords)
        for i in range(len(tech_keywords_list)):
            for j in range(i+1, len(tech_keywords_list)):
                rule = {
                    "rule_type": "keyword_combination",
                    "keywords": [tech_keywords_list[i], tech_keywords_list[j]],
                    "context": "technical",
                    "description": f"기술적 문제 키워드 조합: {tech_keywords_list[i]} + {tech_keywords_list[j]}",
                    "priority": 2,
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "source": "conversations_extraction"
                }
                rules_to_add.append(rule)
        
        # 일상 대화 키워드 조합
        casual_keywords_list = list(casual_keywords)
        for i in range(len(casual_keywords_list)):
            for j in range(i+1, len(casual_keywords_list)):
                rule = {
                    "rule_type": "keyword_combination",
                    "keywords": [casual_keywords_list[i], casual_keywords_list[j]],
                    "context": "casual",
                    "description": f"일상 대화 키워드 조합: {casual_keywords_list[i]} + {casual_keywords_list[j]}",
                    "priority": 2,
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "source": "conversations_extraction"
                }
                rules_to_add.append(rule)
        
        # DB에 규칙 추가
        for rule in rules_to_add:
            try:
                # 중복 체크
                existing = await self.rules_collection.find_one({
                    "rule_type": rule["rule_type"],
                    "keywords": rule["keywords"]
                })
                if existing:
                    continue
                
                await self.rules_collection.insert_one(rule)
                rules_count += 1
                
            except Exception as e:
                logger.error(f"규칙 추가 중 오류: {str(e)}")
                continue
        
        return rules_count

async def main():
    """메인 함수"""
    # MongoDB 연결
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.aicounsel
    
    try:
        extractor = ContextPatternExtractor(db)
        result = await extractor.extract_patterns_from_conversations()
        
        print(f"\n✅ 추출 완료!")
        print(f"   - 총 패턴: {result['total_patterns']}개")
        print(f"   - 추가된 패턴: {result['added_patterns']}개")
        print(f"   - 생성된 규칙: {result['generated_rules']}개")
        
    except Exception as e:
        logger.error(f"실행 중 오류: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main()) 