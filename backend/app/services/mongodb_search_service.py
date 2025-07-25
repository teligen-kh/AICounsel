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
        사용자 질문에 대한 답변을 검색합니다.
        
        Args:
            query: 사용자 질문
            
        Returns:
            Optional[str]: 찾은 답변 또는 None
        """
        logging.info(f"🔍 MongoDB 검색 시작: {query[:50]}...")
        
        try:
            # 1. 정확한 매치 검색 (부분 매치 우선)
            logging.info("🔍 1단계: 정확한 매치 검색")
            exact_match = await self._search_exact_match(query)
            if exact_match:
                logging.info("✅ 정확한 매치에서 답변 찾음")
                return exact_match
            
            # 2. 키워드 기반 검색
            logging.info("🔍 2단계: 키워드 기반 검색")
            keywords = self._extract_keywords(query)
            if keywords:
                logging.info(f"🔍 추출된 키워드: {keywords}")
                keyword_match = await self._search_by_keywords(keywords)
                if keyword_match:
                    logging.info("✅ 키워드 검색에서 답변 찾음")
                    return keyword_match
            
            # 3. 유사도 기반 검색
            logging.info("🔍 3단계: 유사도 기반 검색")
            similarity_match = await self._search_by_similarity(query)
            if similarity_match:
                logging.info("✅ 유사도 검색에서 답변 찾음")
                return similarity_match
            
            logging.info("❌ 모든 검색 방법에서 답변을 찾지 못함")
            return None
            
        except Exception as e:
            logging.error(f"❌ 검색 중 오류 발생: {str(e)}")
            return None
    
    async def _search_exact_match(self, query: str) -> Optional[str]:
        """스마트 검색: 부분 매치 → 키워드 기반 → 유사도 순"""
        try:
            # 정규화된 쿼리
            normalized_query = self._normalize_text(query)
            
            # 1. 부분 매치 검색 (현재: question 그대로 사용)
            partial_match = await self.knowledge_collection.find_one({
                "question": {"$regex": normalized_query, "$options": "i"}
            })
            
            if partial_match:
                logging.info(f"Partial match found: {partial_match['question']}")
                return partial_match['answer']
            
            # 2. 키워드 기반 검색 (미래: question 꼬인 형태 대응)
            keywords = self._extract_keywords(query)
            if keywords:
                # AND 조건: 모든 키워드가 포함된 답변
                and_match = await self._search_by_keywords_and(keywords)
                if and_match:
                    logging.info(f"AND keyword match found: {and_match['question']}")
                    return and_match['answer']
                
                # OR 조건: 주요 키워드가 포함된 답변
                or_match = await self._search_by_keywords_or(keywords)
                if or_match:
                    logging.info(f"OR keyword match found: {or_match['question']}")
                    return or_match['answer']
            
            return None
            
        except Exception as e:
            logging.error(f"Error in smart search: {str(e)}")
            return None

    async def _search_by_keywords_and(self, keywords: List[str]) -> Optional[Dict]:
        """모든 키워드가 포함된 답변 검색 (AND 조건)"""
        try:
            # 핵심 키워드만 선택 (상위 3개)
            core_keywords = keywords[:3]
            
            # 모든 키워드가 포함된 질문 찾기
            for keyword in core_keywords:
                result = await self.knowledge_collection.find_one({
                    "question": {"$regex": keyword, "$options": "i"}
                })
                if not result:
                    return None  # 하나라도 없으면 실패
            
            # 모든 키워드가 포함된 질문 중 가장 관련성 높은 것 선택
            best_match = None
            best_score = 0
            
            for keyword in core_keywords:
                results = await self.knowledge_collection.find({
                    "question": {"$regex": keyword, "$options": "i"}
                }).to_list(length=10)
                
                for result in results:
                    score = self._calculate_keyword_score(result, core_keywords)
                    if score > best_score:
                        best_score = score
                        best_match = result
            
            return best_match if best_score > 5.0 else None
            
        except Exception as e:
            logging.error(f"Error in AND keyword search: {str(e)}")
            return None

    async def _search_by_keywords_or(self, keywords: List[str]) -> Optional[Dict]:
        """주요 키워드가 포함된 답변 검색 (OR 조건)"""
        try:
            # 핵심 키워드만 선택 (상위 2개)
            core_keywords = keywords[:2]
            
            best_match = None
            best_score = 0
            
            # 각 키워드별로 검색
            for keyword in core_keywords:
                results = await self.knowledge_collection.find({
                    "question": {"$regex": keyword, "$options": "i"}
                }).to_list(length=5)
                
                for result in results:
                    score = self._calculate_keyword_score(result, core_keywords)
                    if score > best_score:
                        best_score = score
                        best_match = result
            
            return best_match if best_score > 3.0 else None
            
        except Exception as e:
            logging.error(f"Error in OR keyword search: {str(e)}")
            return None

    def _calculate_keyword_score(self, item: Dict, keywords: List[str]) -> float:
        """키워드 매칭 점수를 계산합니다."""
        score = 0.0
        question = item.get('question', '').lower()
        answer = item.get('answer', '').lower()
        
        # 핵심 키워드 가중치 (포인트 관련 추가)
        priority_keywords = {
            '포인트': 8.0,
            '적립': 8.0,
            '포인트적립': 10.0,
            '포인트 적립': 10.0,
            '포스': 5.0,
            'POS': 5.0,
            '프로그램': 4.0,
            '설치': 4.0,
            '재설치': 6.0,
            '데이터': 4.0,
            '백업': 5.0,
            '복원': 4.0,
            '키오스크': 5.0,
            '터치': 3.0,
            '프린터': 5.0,
            '인쇄': 4.0,
            '출력': 3.0,
            '오류': 3.0,
            '에러': 3.0,
            '문제': 2.0,
            '연결': 3.0,
            '설정': 3.0,
            '네트워크': 4.0,
            '와이파이': 4.0,
            'WiFi': 4.0,
            '결제': 4.0,
            '환불': 4.0,
            '취소': 3.0,
            'DB': 6.0,
            '데이터베이스': 6.0,
            '공간': 4.0,
            '늘리기': 5.0,
            '늘리': 5.0,
            'ARUMLOCADB': 8.0,
            'TABLE': 4.0,
            '견적서': 6.0,
            '참조사항': 6.0,
            '참고사항': 6.0,
            '메모': 4.0
        }
        
        # 개별 키워드 점수
        for keyword in keywords:
            weight = priority_keywords.get(keyword, 1.0)
            
            # 질문에 키워드가 있으면 높은 점수
            if keyword in question:
                score += 5.0 * weight  # 3.0 -> 5.0으로 증가
            # 답변에 키워드가 있으면 중간 점수
            if keyword in answer:
                score += 2.0 * weight  # 1.0 -> 2.0으로 증가
        
        # 연속된 키워드 매칭에 추가 점수
        for i in range(len(keywords) - 1):
            phrase = f"{keywords[i]} {keywords[i+1]}"
            if phrase in question:
                score += 8.0  # 4.0 -> 8.0으로 증가
            if phrase in answer:
                score += 4.0  # 2.0 -> 4.0으로 증가
        
        # 특정 조합에 높은 점수 (포인트 관련 추가)
        combinations = [
            ('포스', '포인트'),
            ('포인트', '적립'),
            ('포인트', '설정'),
            ('포스', '재설치'),
            ('POS', '재설치'),
            ('프로그램', '재설치'),
            ('데이터', '백업'),
            ('키오스크', '터치'),
            ('프린터', '오류'),
            ('DB', '늘리기'),
            ('데이터베이스', '늘리기'),
            ('견적서', '참조사항'),
            ('견적서', '참고사항')
        ]
        
        for combo in combinations:
            if combo[0] in question and combo[1] in question:
                score += 12.0  # 8.0 -> 12.0으로 증가
            if combo[0] in answer and combo[1] in answer:
                score += 6.0   # 4.0 -> 6.0으로 증가
        
        return score

    async def _search_by_keywords(self, keywords: List[str]) -> Optional[str]:
        """키워드 기반 검색을 수행합니다."""
        try:
            import time
            if not keywords:
                return None
            
            # 모든 지식 베이스 항목을 가져와서 점수 계산
            fetch_start = time.time()
            all_items = await self.knowledge_collection.find({}).to_list(length=None)
            fetch_time = (time.time() - fetch_start) * 1000
            logging.info(f"DB 데이터 가져오기 시간: {fetch_time:.2f}ms (항목 수: {len(all_items)})")
            
            # 점수 계산
            score_start = time.time()
            best_match = None
            best_score = 0
            
            for item in all_items:
                score = self._calculate_keyword_score(item, keywords)
                if score > best_score:
                    best_score = score
                    best_match = item
            
            score_time = (time.time() - score_start) * 1000
            logging.info(f"점수 계산 시간: {score_time:.2f}ms (항목당 평균: {score_time/len(all_items):.3f}ms)")
            
            # 점수가 충분히 높은 경우만 반환 (임계값을 더 낮춤)
            if best_score >= 1.0:  # 1.5에서 1.0으로 낮춤
                logging.info(f"Keyword match found with score {best_score}: {best_match.get('question', '')[:50]}...")
                return best_match['answer']
            
            return None
            
        except Exception as e:
            logging.error(f"Error in keyword search: {str(e)}")
            return None

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
            
            # 불용어 목록 (더 구체적으로) - 핵심 키워드는 제거하지 않음
            stop_words = {
                '어떻게', '해요', '돼요', '있어요', '하나요', '오류', '발생', '했어요', '안돼요',
                '이', '가', '을', '를', '의', '에', '에서', '로', '으로', '와', '과', '도', '만', 
                '은', '는', '그', '저', '어떤', '무엇', '왜', '언제', '어디서', '잘', '못', '안',
                '문제', '해결', '알려', '주세요', '요청', '문의', '도움', '좀', '요',
                '아니', '그게', '아니라', '그것도', '방법이긴', '한데', '다른', '매장', '점주에게',
                '들으니', '하드디스크', '용량만큼', '사용이', '가능하게', '늘려주는', '방법이',
                '있다고', '하던데', '뭔소리야', '인가', '뭔가를', '늘리는', '방법이', '있다며',
                '안녕하세요', '안녕', '하세요', '안녕하', '세요', '안녕하세요?', '안녕하세요!',
                '어떤', '도움이', '필요하신가요', '필요하신가요?', '필요하신가요!',
                '도움이', '필요해요', '필요합니다', '필요해', '필요하', '도움', '필요',
                '그러면', '그럼', '그래서', '그리고', '또한', '또는', '하지만', '그런데'
            }
            
            # 불용어 제거 및 2글자 이상만 선택
            keywords = [word for word in words if word not in stop_words and len(word) >= 2]
            
            # 핵심 키워드 우선순위 부여 (확장)
            priority_keywords = [
                'DB', '데이터베이스', '공간', '늘리기', '늘리', '방법', 'ARUMLOCADB', 'TABLE',
                '포스', 'POS', '프로그램', '설치', '재설치', '데이터', '백업', '복원',
                '키오스크', '터치', '프린터', '인쇄', '출력', '오류', '에러', '문제',
                '연결', '설정', '네트워크', '와이파이', 'WiFi', '결제', '환불', '취소',
                '로그인', '로그아웃', '비밀번호', '아이디', '계정', '업데이트', '다운로드'
            ]
            
            filtered_keywords = []
            
            # 우선순위 키워드를 먼저 추가
            for keyword in keywords:
                if keyword in priority_keywords:
                    filtered_keywords.insert(0, keyword)  # 우선순위 키워드를 앞에 배치
                else:
                    filtered_keywords.append(keyword)
            
            return filtered_keywords[:8]  # 상위 8개까지 반환
            
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
        """텍스트 정규화 (간단하게)"""
        try:
            # 기본 정리만
            normalized = text.strip()
            
            # 연속된 공백을 하나로
            normalized = re.sub(r'\s+', ' ', normalized)
            
            return normalized
            
        except Exception as e:
            logging.error(f"Error in text normalization: {str(e)}")
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