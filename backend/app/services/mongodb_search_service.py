from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Optional, Tuple
import re
from datetime import datetime
import logging

class MongoDBSearchService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.conversations_collection = db.conversations
        self.knowledge_collection = db.knowledge_base  # 지식 베이스 컬렉션
        
    async def search_relevant_answers(self, query: str, limit: int = 5) -> List[Dict]:
        """
        사용자 질문과 관련된 답변을 MongoDB에서 검색합니다.
        
        Args:
            query: 사용자 질문
            limit: 반환할 최대 결과 수
            
        Returns:
            관련 답변 목록
        """
        try:
            # 1단계: 정확한 키워드 매칭 시도
            exact_matches = await self._search_exact_matches(query, limit)
            
            if exact_matches:
                logging.info(f"Found {len(exact_matches)} exact matches")
                return exact_matches
            
            # 2단계: 개선된 키워드 기반 검색
            logging.info("No exact matches found, using improved keyword search")
            return await self._search_improved_keywords(query, limit)
            
        except Exception as e:
            logging.error(f"Error searching MongoDB: {str(e)}")
            return []
    
    async def _search_exact_matches(self, query: str, limit: int) -> List[Dict]:
        """정확한 키워드 매칭을 시도합니다."""
        try:
            # 질문에서 공백을 .*로 변환하여 유연한 매칭
            pattern = query.replace(' ', '.*')
            
            exact_matches = await self.knowledge_collection.find({
                'question': {'$regex': pattern, '$options': 'i'}
            }).limit(limit).to_list(length=limit)
            
            results = []
            for item in exact_matches:
                results.append({
                    'content': item.get('answer', ''),
                    'source': 'knowledge_base',
                    'question': item.get('question', ''),
                    'keywords': item.get('keywords', []),
                    'score': 10.0,  # 정확한 매칭은 높은 점수
                    'match_type': 'exact'
                })
            
            return results
            
        except Exception as e:
            logging.error(f"Error in exact search: {str(e)}")
            return []
    
    async def _search_improved_keywords(self, query: str, limit: int) -> List[Dict]:
        """개선된 키워드 기반 검색을 수행합니다."""
        try:
            # 키워드 추출
            keywords = self._extract_improved_keywords(query)
            logging.info(f"Extracted keywords: {keywords}")
            
            if not keywords:
                return []
            
            # 모든 지식 베이스 항목을 가져와서 점수 계산
            all_items = await self.knowledge_collection.find({}).to_list(length=None)
            
            scored_results = []
            for item in all_items:
                score = self._calculate_relevance_score(item, keywords)
                if score > 0:
                    scored_results.append({
                        'content': item.get('answer', ''),
                        'source': 'knowledge_base',
                        'question': item.get('question', ''),
                        'keywords': item.get('keywords', []),
                        'score': score,
                        'match_type': 'keyword'
                    })
            
            # 점수순으로 정렬
            scored_results.sort(key=lambda x: x['score'], reverse=True)
            
            return scored_results[:limit]
            
        except Exception as e:
            logging.error(f"Error in improved keyword search: {str(e)}")
            return []

    def _extract_improved_keywords(self, text: str) -> List[str]:
        """개선된 키워드 추출 로직"""
        # 불용어 목록 확장 - 더 구체적으로
        stop_words = {
            '어떻게', '해요', '돼요', '있어요', '하나요', '오류', '발생', '했어요', '안돼요',
            '이', '가', '을', '를', '의', '에', '에서', '로', '으로', '와', '과', '도', '만', 
            '은', '는', '그', '저', '어떤', '무엇', '왜', '언제', '어디서', '잘', '못', '안',
            '문제', '해결', '방법', '알려', '주세요', '요청', '문의', '도움', '코드', '설치방법'
        }
        
        # 특수문자 제거 및 소문자 변환
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        words = text.split()
        
        # 불용어 제거 및 2글자 이상만 선택
        keywords = [word for word in words if word not in stop_words and len(word) >= 2]
        
        return keywords

    def _calculate_relevance_score(self, result: Dict, keywords: List[str]) -> float:
        """검색 결과와 키워드 간의 관련성 점수 계산 - 개선된 버전"""
        score = 0.0
        question = result.get('question', '').lower()
        answer = result.get('answer', '').lower()
        
        # 키워드별 가중치 설정
        keyword_weights = {
            '포스': 5.0,
            '키오스크': 5.0,
            '프린터': 5.0,
            '백업': 4.0,
            'sql': 4.0,
            '재설치': 4.0,
            '설치': 3.0,
            '프로그램': 3.0,
            '클라우드': 4.0,
            '6버전': 5.0,
            '오류': 3.0,
            '연결': 2.0,
            '설정': 2.0
        }
        
        for keyword in keywords:
            weight = keyword_weights.get(keyword, 1.0)  # 기본 가중치 1.0
            
            # 질문에 키워드가 있으면 높은 점수
            if keyword in question:
                score += 3.0 * weight
            # 답변에 키워드가 있으면 중간 점수
            if keyword in answer:
                score += 1.0 * weight
        
        # 연속된 키워드 매칭에 추가 점수
        for i in range(len(keywords) - 1):
            phrase = f"{keywords[i]} {keywords[i+1]}"
            if phrase in question:
                score += 4.0
            if phrase in answer:
                score += 1.0
        
        # 문맥 기반 추가 점수
        context_bonus = self._calculate_context_bonus(question, answer, keywords)
        score += context_bonus
        
        return score

    def _calculate_context_bonus(self, question: str, answer: str, keywords: List[str]) -> float:
        """문맥 기반 추가 점수 계산"""
        bonus = 0.0
        
        # 특정 키워드 조합에 대한 보너스
        if '포스' in keywords and '재설치' in keywords:
            if '포스' in question and '재설치' in question:
                bonus += 5.0
        
        if '클라우드' in keywords and '설치' in keywords:
            if '클라우드' in question and '설치' in question:
                bonus += 5.0
        
        if '키오스크' in keywords and '터치' in keywords:
            if '키오스크' in question and '터치' in question:
                bonus += 5.0
        
        if '프린터' in keywords and '오류' in keywords:
            if '프린터' in question and '오류' in question:
                bonus += 5.0
        
        # 질문의 길이가 짧을 때 더 정확한 매칭에 높은 점수
        if len(question.split()) <= 5:  # 짧은 질문
            if any(keyword in question for keyword in keywords):
                bonus += 3.0
        
        return bonus

    async def _search_conversations(self, query: str, limit: int) -> List[Dict]:
        """기존 대화에서 관련 답변을 검색합니다."""
        try:
            # 키워드 추출
            keywords = self._extract_improved_keywords(query)
            
            # MongoDB 텍스트 검색을 위한 쿼리 구성
            search_query = {
                "$or": [
                    {"messages.content": {"$regex": keyword, "$options": "i"}} 
                    for keyword in keywords
                ]
            }
            
            # 관련 대화 검색
            conversations = await self.conversations_collection.find(
                search_query,
                {"messages": 1, "session_id": 1, "created_at": 1}
            ).limit(limit * 2).to_list(length=limit * 2)
            
            relevant_answers = []
            
            for conv in conversations:
                if 'messages' in conv:
                    for msg in conv['messages']:
                        if msg.get('role') == 'assistant' and msg.get('content'):
                            # 사용자 질문과 AI 답변 쌍 찾기
                            answer_text = msg['content']
                            
                            # 키워드 매칭 확인
                            if any(keyword.lower() in answer_text.lower() for keyword in keywords):
                                relevant_answers.append({
                                    'content': answer_text,
                                    'source': 'conversation',
                                    'session_id': conv.get('session_id'),
                                    'timestamp': msg.get('timestamp'),
                                    'score': 0  # 나중에 계산
                                })
            
            return relevant_answers
            
        except Exception as e:
            logging.error(f"Error searching conversations: {str(e)}")
            return []
    
    async def _search_knowledge_base(self, query: str, limit: int) -> List[Dict]:
        """지식 베이스에서 관련 답변을 검색합니다."""
        try:
            # 지식 베이스 컬렉션이 존재하는지 확인
            collections = await self.db.list_collection_names()
            if 'knowledge_base' not in collections:
                logging.info("Knowledge base collection not found")
                return []
            
            # 키워드 추출
            keywords = self._extract_improved_keywords(query)
            logging.info(f"Extracted keywords: {keywords}")
            
            # 검색 쿼리 구성
            search_conditions = []
            
            # 질문에서 키워드 검색
            for keyword in keywords:
                search_conditions.append({"question": {"$regex": keyword, "$options": "i"}})
                search_conditions.append({"answer": {"$regex": keyword, "$options": "i"}})
            
            # 키워드 배열에서 검색
            if keywords:
                search_conditions.append({"keywords": {"$in": keywords}})
            
            search_query = {"$or": search_conditions} if search_conditions else {}
            
            logging.info(f"Search query: {search_query}")
            
            # 지식 베이스에서 검색
            knowledge_items = await self.knowledge_collection.find(
                search_query
            ).limit(limit).to_list(length=limit)
            
            logging.info(f"Found {len(knowledge_items)} knowledge items")
            
            relevant_answers = []
            for item in knowledge_items:
                relevant_answers.append({
                    'content': item.get('answer', ''),
                    'source': 'knowledge_base',
                    'question': item.get('question', ''),
                    'keywords': item.get('keywords', []),
                    'score': 0  # 나중에 계산
                })
            
            return relevant_answers
            
        except Exception as e:
            logging.error(f"Error searching knowledge base: {str(e)}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def _extract_keywords(self, query: str) -> List[str]:
        """질문에서 키워드를 추출합니다."""
        # 한국어 조사, 접속사 등 제거
        stop_words = ['이', '가', '을', '를', '의', '에', '에서', '로', '으로', '와', '과', '도', '만', '은', '는', '이', '그', '저', '어떤', '무엇', '어떻게', '왜', '언제', '어디서']
        
        # 특수문자 제거 및 소문자 변환
        cleaned_query = re.sub(r'[^\w\s가-힣]', ' ', query.lower())
        
        # 단어 분리
        words = cleaned_query.split()
        
        # 불용어 제거 및 2글자 이상 단어만 선택
        keywords = [word for word in words if word not in stop_words and len(word) >= 2]
        
        return keywords
    
    def _score_relevance(self, query: str, answers: List[Dict]) -> List[Dict]:
        """답변의 관련도를 점수화합니다."""
        query_keywords = self._extract_keywords(query)
        
        for answer in answers:
            content = answer.get('content', '').lower()
            score = 0
            
            # 키워드 매칭 점수
            for keyword in query_keywords:
                if keyword in content:
                    score += 1
            
            # 길이 점수 (너무 짧거나 긴 답변은 낮은 점수)
            content_length = len(content)
            if 50 <= content_length <= 500:
                score += 1
            elif content_length > 1000:
                score -= 1
            
            # 소스별 가중치 (지식 베이스에 높은 가중치)
            if answer.get('source') == 'knowledge_base':
                score += 5  # 지식 베이스 답변에 높은 가중치
            elif answer.get('source') == 'conversation':
                score += 1  # 기존 대화 답변에 낮은 가중치
            
            answer['score'] = score
        
        return answers
    
    async def save_knowledge_item(self, question: str, answer: str, keywords: List[str] = None):
        """지식 베이스를 확장하기 위한 메서드"""
        try:
            if keywords is None:
                keywords = self._extract_improved_keywords(question)
            
            knowledge_item = {
                'question': question,
                'answer': answer,
                'keywords': keywords,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            await self.knowledge_collection.insert_one(knowledge_item)
            logging.info(f"Saved knowledge item: {question}")
            
        except Exception as e:
            logging.error(f"Error saving knowledge item: {str(e)}")
    
    async def get_best_answer(self, query: str) -> Optional[str]:
        """가장 관련성 높은 답변을 반환합니다."""
        try:
            # 너무 일반적인 질문인지 먼저 확인
            if self._is_too_general(query):
                return self._get_clarification_response(query)
            
            answers = await self.search_relevant_answers(query, limit=1)
            
            if answers and answers[0]['score'] > 5.0:  # 점수 임계값을 높임
                return answers[0]['content']
            
            # 관련 답변이 없는 경우 구체적인 질문 유도
            return self._get_clarification_response(query)
            
        except Exception as e:
            logging.error(f"Error getting best answer: {str(e)}")
            return None

    def _is_too_general(self, query: str) -> bool:
        """질문이 너무 일반적인지 확인합니다."""
        query_lower = query.lower().strip()
        
        # 구체적인 질문 패턴들 (이것들은 일반적인 질문이 아님) - 먼저 확인
        specific_patterns = [
            '포스 재설치',
            '포스 설치',
            '키오스크 터치',
            '프린터 오류',
            '백업 방법',
            'sql 설치',
            '클라우드 설치',
            '6버전 설치',
            '프로그램 실행',
            '연결 문제',
            '설정 방법'
        ]
        
        for pattern in specific_patterns:
            if pattern in query_lower:
                return False  # 구체적인 질문이므로 일반적인 질문이 아님
        
        # 너무 짧은 질문 (구체적인 패턴이 없는 경우에만)
        if len(query.strip()) < 10:
            return True
        
        # 일반적인 질문 패턴들
        general_patterns = [
            '설치하고 싶어요',
            '설치하고 싶습니다',
            '설치해주세요',
            '오류가 발생했어요',
            '오류가 발생했습니다',
            '문제가 있어요',
            '문제가 있습니다',
            '도움이 필요해요',
            '도움이 필요합니다',
            '어떻게 하나요',
            '어떻게 하나요?',
            '어떻게 해요',
            '어떻게 해요?',
            '알려주세요',
            '알려주세요.',
            '알려주세요?'
        ]
        
        for pattern in general_patterns:
            if pattern in query_lower:
                return True
        
        # 키워드가 너무 적거나 일반적인 경우
        keywords = self._extract_improved_keywords(query)
        if len(keywords) <= 1:
            return True
        
        return False

    def _get_clarification_response(self, query: str) -> str:
        """구체적인 질문을 유도하는 답변을 반환합니다."""
        # 키워드 추출
        keywords = self._extract_improved_keywords(query)
        
        # 일반적인 질문 패턴 감지
        if len(keywords) == 0 or len(keywords) == 1:
            return "더 구체적으로 말씀해 주시면 정확한 답변을 드릴 수 있습니다. 예를 들어:\n\n• 포스 재설치 방법\n• 키오스크 터치 오류 해결\n• 프린터 연결 문제\n• 백업 방법\n\n어떤 부분에 대해 도움이 필요하신가요?"
        
        # 특정 키워드 기반 안내
        if '설치' in query.lower():
            return "설치와 관련된 질문이시군요. 더 구체적으로 말씀해 주세요:\n\n• 어떤 프로그램을 설치하시려고 하나요? (포스, 클라우드, 키오스크 등)\n• 신규 설치인가요, 재설치인가요?\n• 설치 중 오류가 발생했나요?"
        
        if '오류' in query.lower() or '문제' in query.lower():
            return "오류나 문제가 발생하셨군요. 더 구체적으로 말씀해 주세요:\n\n• 어떤 장비에서 문제가 발생했나요? (포스, 키오스크, 프린터 등)\n• 어떤 오류 메시지가 나타났나요?\n• 언제부터 문제가 발생했나요?"
        
        if '코드' in query.lower():
            return "코드와 관련된 질문이시군요. 더 구체적으로 말씀해 주세요:\n\n• 설치 코드가 필요하신가요?\n• 코드 입력 중 오류가 발생했나요?\n• 코드를 찾을 수 없나요?"
        
        # 기본 안내
        return "질문을 더 구체적으로 말씀해 주시면 정확한 답변을 드릴 수 있습니다. 어떤 부분에 대해 도움이 필요하신가요?" 