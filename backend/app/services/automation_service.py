"""
자동화 서비스 모듈
대화 저장 후 knowledge_base와 input_keywords에 자동 업데이트하는 시스템
"""

import logging
from typing import Dict, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import re
from difflib import SequenceMatcher

class AutomationService:
    """자동화 서비스 클래스"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        자동화 서비스 초기화
        
        Args:
            db: MongoDB 데이터베이스 연결 인스턴스
        """
        self.db = db
        self.conversations_collection = db.conversations
        self.knowledge_collection = db.knowledge_base
        self.keyword_collection = db.input_keywords
        
    async def process_conversation_automation(self, user_message: str, ai_response: str, classification: str) -> Dict:
        """
        대화 자동화 처리
        
        Args:
            user_message: 사용자 메시지
            ai_response: AI 응답
            classification: 입력 분류
            
        Returns:
            Dict: 처리 결과
        """
        try:
            result = {
                "conversation_saved": False,
                "knowledge_updated": False,
                "keywords_updated": False,
                "details": {}
            }
            
            # 1. 대화 저장
            conversation_saved = await self._save_conversation(user_message, ai_response, classification)
            result["conversation_saved"] = conversation_saved
            
            # 2. 기술적 질문인 경우 knowledge_base 업데이트
            if classification == "technical":
                knowledge_updated = await self._update_knowledge_base(user_message, ai_response)
                result["knowledge_updated"] = knowledge_updated
                
                # 3. 키워드 추출 및 업데이트
                keywords_updated = await self._extract_and_update_keywords(user_message)
                result["keywords_updated"] = keywords_updated
            
            logging.info(f"자동화 처리 완료: {result}")
            return result
            
        except Exception as e:
            logging.error(f"자동화 처리 중 오류: {str(e)}")
            return {"error": str(e)}
    
    async def _save_conversation(self, user_message: str, ai_response: str, classification: str) -> bool:
        """대화를 conversations 테이블에 저장"""
        try:
            conversation = {
                "user_message": user_message,
                "ai_response": ai_response,
                "classification": classification,
                "timestamp": datetime.now(),
                "created_at": datetime.now()
            }
            
            await self.conversations_collection.insert_one(conversation)
            logging.info(f"대화 저장 완료: {classification}")
            return True
            
        except Exception as e:
            logging.error(f"대화 저장 실패: {str(e)}")
            return False
    
    async def _update_knowledge_base(self, user_message: str, ai_response: str) -> bool:
        """knowledge_base 업데이트 (중복 체크 포함)"""
        try:
            # 유사성 체크로 중복 방지
            is_duplicate = await self._check_similarity(user_message)
            
            if not is_duplicate:
                # 키워드 추출
                keywords = self._extract_keywords_soynlp(user_message)
                
                knowledge_item = {
                    "question": user_message,
                    "answer": ai_response,
                    "keywords": keywords,
                    "category": "technical",
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                
                await self.knowledge_collection.insert_one(knowledge_item)
                logging.info(f"knowledge_base 업데이트 완료: {user_message[:50]}...")
                return True
            else:
                logging.info(f"중복 질문 감지: {user_message[:50]}...")
                return False
                
        except Exception as e:
            logging.error(f"knowledge_base 업데이트 실패: {str(e)}")
            return False
    
    async def _check_similarity(self, user_message: str, threshold: float = 0.8) -> bool:
        """유사성 체크로 중복 방지"""
        try:
            # 기존 질문들과 유사도 비교
            existing_questions = await self.knowledge_collection.find({}).to_list(None)
            
            for item in existing_questions:
                existing_question = item.get('question', '')
                similarity = SequenceMatcher(None, user_message.lower(), existing_question.lower()).ratio()
                
                if similarity >= threshold:
                    logging.info(f"유사도 {similarity:.2f}로 중복 감지: {existing_question[:50]}...")
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"유사성 체크 실패: {str(e)}")
            return False
    
    def _extract_keywords_soynlp(self, text: str) -> List[str]:
        """soynlp를 사용한 키워드 추출"""
        try:
            # soynlp가 설치되어 있지 않을 경우를 대비한 기본 추출
            import re
            
            # 한글, 영문, 숫자로 구성된 단어 추출
            words = re.findall(r'[가-힣a-zA-Z0-9]+', text.lower())
            
            # 2글자 이상, 10글자 이하 단어만 선택
            keywords = [word for word in words if 2 <= len(word) <= 10]
            
            # 도메인 관련 키워드 우선 선택
            domain_keywords = ["포스", "키오스크", "프린터", "설치", "설정", "오류", "프로그램", "시스템", "네트워크", "연결", "데이터", "백업", "복구", "업데이트", "영수증", "결제", "카드", "모니터", "포트", "장치관리자", "재연결", "출력", "정상출력", "다운로드", "드라이버", "재부팅", "인터페이스", "매뉴얼", "설명서", "가이드", "도움말"]
            
            # 도메인 키워드가 포함된 경우 우선 선택
            priority_keywords = [word for word in keywords if word in domain_keywords]
            other_keywords = [word for word in keywords if word not in domain_keywords]
            
            # 우선순위 키워드 + 기타 키워드 (최대 10개)
            result = priority_keywords + other_keywords[:10-len(priority_keywords)]
            
            return result[:10]  # 최대 10개로 제한
            
        except Exception as e:
            logging.error(f"키워드 추출 실패: {str(e)}")
            return []
    
    async def _extract_and_update_keywords(self, user_message: str) -> bool:
        """키워드 추출 및 input_keywords 업데이트 (도메인 키워드 자동 추출 포함)"""
        try:
            # 1. 현재 메시지에서 키워드 추출
            extracted_keywords = self._extract_keywords_soynlp(user_message)
            
            # 2. knowledge_base에서 도메인 키워드 자동 추출
            domain_keywords = await self._extract_domain_keywords_from_knowledge_base()
            
            # 3. 모든 키워드 통합
            all_keywords = list(set(extracted_keywords + domain_keywords))
            
            if all_keywords:
                # technical 카테고리에 키워드 추가
                await self.keyword_collection.update_one(
                    {"category": "technical"},
                    {"$set": {
                        "keywords": all_keywords,
                        "updated_at": datetime.now()
                    }},
                    upsert=True
                )
                
                logging.info(f"키워드 업데이트 완료: {len(all_keywords)}개 키워드")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"키워드 업데이트 실패: {str(e)}")
            return False
    
    async def _extract_domain_keywords_from_knowledge_base(self) -> List[str]:
        """knowledge_base에서 도메인 키워드 자동 추출"""
        try:
            # knowledge_base의 모든 키워드 수집
            all_keywords = []
            async for item in self.knowledge_collection.find({}):
                if 'keywords' in item and item['keywords']:
                    all_keywords.extend(item['keywords'])
            
            # 도메인 키워드 필터링
            domain_keywords = self._filter_domain_keywords(all_keywords)
            
            return domain_keywords
            
        except Exception as e:
            logging.error(f"도메인 키워드 추출 실패: {str(e)}")
            return []
    
    def _filter_domain_keywords(self, keywords: List[str]) -> List[str]:
        """도메인 관련 키워드만 필터링"""
        # 도메인 관련 키워드 패턴
        domain_patterns = [
            r'.*설치.*', r'.*설정.*', r'.*오류.*', r'.*에러.*', r'.*문제.*', r'.*해결.*', r'.*방법.*',
            r'.*프로그램.*', r'.*소프트웨어.*', r'.*하드웨어.*', r'.*기기.*', r'.*장비.*',
            r'.*스캐너.*', r'.*프린터.*', r'.*포스.*', r'.*pos.*', r'.*시스템.*', r'.*네트워크.*',
            r'.*연결.*', r'.*인터넷.*', r'.*데이터.*', r'.*백업.*', r'.*복구.*', r'.*업데이트.*',
            r'.*영수증.*', r'.*결제.*', r'.*카드.*', r'.*키오스크.*', r'.*kiosk.*',
            r'.*듀얼모니터.*', r'.*모니터.*', r'.*화면.*', r'.*디스플레이.*',
            r'.*포트.*', r'.*장치관리자.*', r'.*디바이스.*', r'.*device.*',
            r'.*재연결.*', r'.*출력.*', r'.*정상출력.*', r'.*정상작동.*',
            r'.*다운로드.*', r'.*업로드.*', r'.*설치파일.*', r'.*드라이버.*',
            r'.*재부팅.*', r'.*리부팅.*', r'.*부팅.*', r'.*인터페이스.*',
            r'.*ui.*', r'.*ux.*', r'.*사용자.*', r'.*사용법.*', r'.*매뉴얼.*',
            r'.*설명서.*', r'.*가이드.*', r'.*도움말.*', r'.*help.*',
            r'.*거래명세서.*', r'.*직인.*', r'.*계좌번호.*', r'.*로그인.*', r'.*단말기.*',
            r'.*클라우드.*', r'.*재설치.*', r'.*설치요구.*', r'.*작동.*', r'.*재시작.*'
        ]
        
        # 비도메인 키워드 제외
        exclude_keywords = [
            '고객님', '팀장', '아침', '커피', '감사', '안녕', '반갑', '좋은', '하이', 'hello',
            '바쁘', '식사', '점심', '저녁', '차', '날씨', '기분', '피곤', '힘드시', '지내',
            '너는', '당신은', 'ai', '인공지능', '로봇'
        ]
        
        # 도메인 키워드 필터링
        domain_keywords = []
        for keyword in keywords:
            if (keyword not in exclude_keywords and 
                any(re.match(pattern, keyword, re.IGNORECASE) for pattern in domain_patterns)):
                domain_keywords.append(keyword)
        
        return list(set(domain_keywords))  # 중복 제거
    
    async def get_automation_stats(self) -> Dict:
        """자동화 통계 조회"""
        try:
            stats = {
                "total_conversations": await self.conversations_collection.count_documents({}),
                "total_knowledge_items": await self.knowledge_collection.count_documents({}),
                "technical_conversations": await self.conversations_collection.count_documents({"classification": "technical"}),
                "casual_conversations": await self.conversations_collection.count_documents({"classification": "casual"}),
                "non_counseling_conversations": await self.conversations_collection.count_documents({"classification": "non_counseling"}),
                "profanity_conversations": await self.conversations_collection.count_documents({"classification": "profanity"})
            }
            
            return stats
            
        except Exception as e:
            logging.error(f"통계 조회 실패: {str(e)}")
            return {} 