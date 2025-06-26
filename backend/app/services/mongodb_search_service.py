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
        
    async def search_answer(self, query: str) -> Optional[str]:
        """
        쿼리와 가장 관련성 높은 답변을 검색합니다.
        
        Args:
            query: 검색 쿼리
            
        Returns:
            가장 관련성 높은 답변 또는 None
        """
        try:
            # 1. 정확한 매치 검색
            exact_match = await self._search_exact_match(query)
            if exact_match:
                logging.info(f"Exact match found for query: {query[:50]}...")
                return exact_match
            
            # 2. 키워드 기반 검색
            logging.info("No exact matches found, using improved keyword search")
            keywords = self._extract_keywords(query)
            logging.info(f"Extracted keywords: {keywords}")
            
            keyword_match = await self._search_by_keywords(keywords)
            if keyword_match:
                logging.info(f"Keyword match found for query: {query[:50]}...")
                return keyword_match
            
            # 3. 유사도 검색
            similarity_match = await self._search_by_similarity(query)
            if similarity_match:
                logging.info(f"Similarity match found for query: {query[:50]}...")
                return similarity_match
            
            # 4. DB에 답변이 없을 때 상담사 연락 안내
            logging.info(f"No relevant answer found for query: {query[:50]}...")
            return self._get_consultant_contact_response(query)
            
        except Exception as e:
            logging.error(f"Error in search_answer: {str(e)}")
            return self._get_consultant_contact_response(query)
    
    async def _search_exact_match(self, query: str) -> Optional[str]:
        """정확한 매치를 검색합니다."""
        try:
            # 정규화된 쿼리
            normalized_query = self._normalize_text(query)
            
            # 정확한 매치 검색
            pipeline = [
                {
                    "$match": {
                        "$or": [
                            {"question": {"$regex": normalized_query, "$options": "i"}},
                            {"keywords": {"$in": [normalized_query]}}
                        ]
                    }
                },
                {"$limit": 1}
            ]
            
            result = await self.knowledge_collection.aggregate(pipeline).to_list(1)
            return result[0]['answer'] if result else None
            
        except Exception as e:
            logging.error(f"Error in exact match search: {str(e)}")
            return None

    async def _search_by_keywords(self, keywords: List[str]) -> Optional[str]:
        """키워드 기반 검색을 수행합니다."""
        try:
            if not keywords:
                return None
            
            # 핵심 키워드 확인
            core_keywords = ['DB', '데이터베이스', '늘리기', '늘리', '공간']
            has_core_keyword = any(keyword in core_keywords for keyword in keywords)
            
            if not has_core_keyword:
                return None
            
            # 모든 지식 베이스 항목을 가져와서 점수 계산
            all_items = await self.knowledge_collection.find({}).to_list(length=None)
            
            best_match = None
            best_score = 0
            
            for item in all_items:
                score = self._calculate_precise_keyword_score(item, keywords)
                if score > best_score:
                    best_score = score
                    best_match = item
            
            # 점수가 충분히 높은 경우만 반환 (임계값을 낮춤)
            if best_score >= 2.0:  # 3.0에서 2.0으로 낮춤
                return best_match['answer']
            
            return None
            
        except Exception as e:
            logging.error(f"Error in keyword search: {str(e)}")
            return None

    def _calculate_precise_keyword_score(self, item: Dict, keywords: List[str]) -> float:
        """정확한 키워드 매칭 점수를 계산합니다."""
        score = 0.0
        question = item.get('question', '').lower()
        answer = item.get('answer', '').lower()
        
        # 핵심 키워드 조합 확인 (DB와 늘리기 관련)
        core_combinations = [
            ('DB', '늘리기'),
            ('DB', '늘리'),
            ('데이터베이스', '늘리기'),
            ('데이터베이스', '늘리'),
            ('공간', '늘리기'),
            ('공간', '늘리'),
            ('DB', '공간'),
            ('데이터베이스', '공간'),
            ('ARUMLOCADB', '늘리기'),
            ('ARUMLOCADB', '늘리'),
            ('TABLE', '늘리기'),
            ('TABLE', '늘리')
        ]
        
        # 핵심 키워드 가중치 (DB와 늘리기 관련 키워드 강화)
        priority_keywords = {
            'DB': 8.0,  # 가중치 증가
            '데이터베이스': 8.0,  # 가중치 증가
            'ARUMLOCADB': 10.0,  # 가장 높은 가중치
            '공간': 6.0,  # 가중치 증가
            '늘리기': 6.0,  # 가중치 증가
            '늘리': 6.0,  # 가중치 증가
            'TABLE': 5.0,  # 가중치 증가
            'SQL': 4.0,
            '데이터': 4.0,  # 가중치 증가
            '저장': 3.0,
            '용량': 4.0,  # 새로운 키워드
            '확장': 5.0,  # 새로운 키워드
            '증가': 5.0,  # 새로운 키워드
            '크기': 4.0,  # 새로운 키워드
            '사이즈': 4.0  # 새로운 키워드
        }
        
        # 핵심 키워드 조합이 있는지 확인 (가중치 증가)
        for combo in core_combinations:
            if combo[0] in question and combo[1] in question:
                score += 15.0  # 핵심 조합에 더 높은 점수
            if combo[0] in answer and combo[1] in answer:
                score += 8.0  # 답변에서도 조합 발견 시 높은 점수
        
        # DB와 늘리기 조합 특별 처리
        if ('DB' in question or '데이터베이스' in question) and ('늘리' in question or '늘리기' in question):
            score += 20.0  # 매우 높은 점수
        if ('DB' in answer or '데이터베이스' in answer) and ('늘리' in answer or '늘리기' in answer):
            score += 12.0  # 답변에서도 높은 점수
        
        # 개별 키워드 점수
        for keyword in keywords:
            weight = priority_keywords.get(keyword, 1.0)
            
            # 질문에 키워드가 있으면 높은 점수
            if keyword in question:
                score += 4.0 * weight  # 가중치 증가
            # 답변에 키워드가 있으면 중간 점수
            if keyword in answer:
                score += 1.5 * weight  # 가중치 증가
        
        # 연속된 키워드 매칭에 추가 점수
        for i in range(len(keywords) - 1):
            phrase = f"{keywords[i]} {keywords[i+1]}"
            if phrase in question:
                score += 6.0  # 가중치 증가
            if phrase in answer:
                score += 2.0  # 가중치 증가
        
        # ARUMLOCADB 특별 처리
        if 'ARUMLOCADB' in question:
            score += 15.0  # 매우 높은 점수
        if 'ARUMLOCADB' in answer:
            score += 8.0
        
        return score

    async def _search_by_similarity(self, query: str) -> Optional[str]:
        """유사도 기반 검색을 수행합니다."""
        try:
            # 간단한 유사도 검색 (키워드 기반)
            keywords = self._extract_keywords(query)
            return await self._search_by_keywords(keywords)
            
        except Exception as e:
            logging.error(f"Error in similarity search: {str(e)}")
            return None
    
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
    
    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 키워드를 추출합니다."""
        try:
            # 특수문자 제거 및 소문자 변환
            text = re.sub(r'[^\w\s가-힣]', ' ', text)
            words = text.split()
            
            # 불용어 목록 (더 구체적으로) - '방법' 제거
            stop_words = {
                '어떻게', '해요', '돼요', '있어요', '하나요', '오류', '발생', '했어요', '안돼요',
                '이', '가', '을', '를', '의', '에', '에서', '로', '으로', '와', '과', '도', '만', 
                '은', '는', '그', '저', '어떤', '무엇', '왜', '언제', '어디서', '잘', '못', '안',
                '문제', '해결', '알려', '주세요', '요청', '문의', '도움', '좀', '요',
                '아니', '그게', '아니라', '그것도', '방법이긴', '한데', '다른', '매장', '점주에게',
                '들으니', '하드디스크', '용량만큼', '사용이', '가능하게', '늘려주는', '방법이',
                '있다고', '하던데', '뭔소리야', '인가', '뭔가를', '늘리는', '방법이', '있다며'
            }
            
            # 불용어 제거 및 2글자 이상만 선택
            keywords = [word for word in words if word not in stop_words and len(word) >= 2]
            
            # 핵심 키워드 우선순위 부여
            priority_keywords = ['DB', '데이터베이스', '공간', '늘리기', '늘리', '방법', 'ARUMLOCADB', 'TABLE']
            filtered_keywords = []
            
            for keyword in keywords:
                if keyword in priority_keywords:
                    filtered_keywords.insert(0, keyword)  # 우선순위 키워드를 앞에 배치
                else:
                    filtered_keywords.append(keyword)
            
            return filtered_keywords[:5]  # 상위 5개만 반환
            
        except Exception as e:
            logging.error(f"Error extracting keywords: {str(e)}")
            return []

    def _extract_improved_keywords(self, text: str) -> List[str]:
        """개선된 키워드 추출 - 더 정확한 검색을 위한 키워드 추출"""
        try:
            # 특수문자 제거 및 소문자 변환
            text = re.sub(r'[^\w\s가-힣]', ' ', text)
            words = text.split()
            
            # 불용어 목록 확장
            stop_words = {
                '어떻게', '해요', '돼요', '있어요', '하나요', '오류', '발생', '했어요', '안돼요',
                '이', '가', '을', '를', '의', '에', '에서', '로', '으로', '와', '과', '도', '만', 
                '은', '는', '그', '저', '어떤', '무엇', '왜', '언제', '어디서', '잘', '못', '안',
                '문제', '해결', '방법', '알려', '주세요', '요청', '문의', '도움', '좀', '요',
                '아니', '그게', '아니라', '그것도', '방법이긴', '한데', '다른', '매장', '점주에게',
                '들으니', '하드디스크', '용량만큼', '사용이', '가능하게', '늘려주는', '방법이',
                '있다고', '하던데', '뭔소리야', '인가', '뭔가를', '늘리는', '방법이', '있다며',
                '안녕하세요', '안녕', '하세요', '안녕하', '세요', '안녕하세요?', '안녕하세요!',
                '어떤', '도움이', '필요하신가요', '필요하신가요?', '필요하신가요!',
                '도움이', '필요해요', '필요합니다', '필요해', '필요하', '도움', '필요'
            }
            
            # 불용어 제거 및 2글자 이상만 선택
            keywords = [word for word in words if word not in stop_words and len(word) >= 2]
            
            # 핵심 키워드 우선순위 부여 (확장)
            priority_keywords = [
                'DB', '데이터베이스', '공간', '늘리기', '늘리', 'ARUMLOCADB', 'TABLE',
                '데이터', '저장', '용량', '확장', '증가', '크기', '사이즈', '설치', '재설치',
                '포스', 'POS', '프로그램', '백업', '복원', '오류', '에러', '문제', '해결',
                '연결', '설정', '터치', '프린터', '키오스크', '클라우드', 'SQL', '서버'
            ]
            
            # 특정 조합 키워드 생성
            combination_keywords = []
            
            # DB 관련 조합
            if any(word in text for word in ['DB', '데이터베이스', '데이터']):
                if any(word in text for word in ['늘리', '늘리기', '증가', '확장', '크기']):
                    combination_keywords.extend(['DB늘리기', '데이터베이스늘리기', 'DB공간늘리기'])
            
            # 포스 관련 조합
            if '포스' in text or 'POS' in text:
                if '설치' in text:
                    combination_keywords.extend(['포스설치', 'POS설치'])
                if '재설치' in text:
                    combination_keywords.extend(['포스재설치', 'POS재설치'])
            
            # 프로그램 관련 조합
            if '프로그램' in text:
                if '설치' in text:
                    combination_keywords.append('프로그램설치')
                if '재설치' in text:
                    combination_keywords.append('프로그램재설치')
            
            filtered_keywords = []
            
            # 조합 키워드를 최우선으로 추가
            filtered_keywords.extend(combination_keywords)
            
            # 개별 키워드 처리
            for keyword in keywords:
                if keyword in priority_keywords:
                    filtered_keywords.insert(len(combination_keywords), keyword)  # 조합 키워드 다음에 배치
                else:
                    filtered_keywords.append(keyword)
            
            return filtered_keywords[:10]  # 상위 10개까지 반환
            
        except Exception as e:
            logging.error(f"Error extracting improved keywords: {str(e)}")
            return []

    def _normalize_text(self, text: str) -> str:
        """텍스트를 정규화합니다."""
        try:
            # 특수문자 제거 및 소문자 변환
            text = re.sub(r'[^\w\s가-힣]', ' ', text)
            return text.strip()
            
        except Exception as e:
            logging.error(f"Error normalizing text: {str(e)}")
            return text
    
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
            
            answers = await self.search_answer(query)
            
            if answers and answers['score'] > 5.0:  # 점수 임계값을 높임
                return answers['content']
            
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

    def _get_consultant_contact_response(self, query: str) -> str:
        """상담사 연락을 유도하는 답변을 반환합니다."""
        # 키워드 추출
        keywords = self._extract_improved_keywords(query)
        
        # 일반적인 질문 패턴 감지
        if len(keywords) == 0 or len(keywords) == 1:
            return "상담사에게 문의하시겠습니까? 저희 상담사에게 연락하여 도움을 받을 수 있습니다. 전화번호는 02-1234-5678입니다."
        
        # 특정 키워드 기반 안내
        if '설치' in query.lower():
            return "설치와 관련된 질문이시군요. 상담사에게 문의하시면 더 구체적인 답변을 드릴 수 있습니다."
        
        if '오류' in query.lower() or '문제' in query.lower():
            return "오류나 문제가 발생하셨군요. 상담사에게 문의하시면 더 구체적인 답변을 드릴 수 있습니다."
        
        if '코드' in query.lower():
            return "코드와 관련된 질문이시군요. 상담사에게 문의하시면 더 구체적인 답변을 드릴 수 있습니다."
        
        # 기본 안내
        return "상담사에게 문의하시면 더 구체적인 답변을 드릴 수 있습니다." 