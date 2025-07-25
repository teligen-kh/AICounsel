"""
knowledge_base 검색 테스트 스크립트
"""

import asyncio
import motor.motor_asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeSearchTester:
    """knowledge_base 검색 테스트"""
    
    def __init__(self, db):
        self.db = db
        self.knowledge_collection = db.knowledge_base
    
    async def test_search(self, query: str):
        """검색 테스트"""
        logger.info(f"검색 테스트: {query}")
        
        # 1. 정확한 매치 검색
        exact_matches = []
        async for doc in self.knowledge_collection.find({"question": {"$regex": query, "$options": "i"}}):
            exact_matches.append(doc)
        
        logger.info(f"정확한 매치: {len(exact_matches)}개")
        for i, doc in enumerate(exact_matches[:3], 1):
            logger.info(f"  {i}. Q: {doc['question']}")
            logger.info(f"     A: {doc['answer'][:100]}...")
        
        # 2. 키워드 기반 검색
        keywords = self._extract_keywords(query)
        logger.info(f"추출된 키워드: {keywords}")
        
        keyword_matches = []
        for keyword in keywords:
            async for doc in self.knowledge_collection.find({"question": {"$regex": keyword, "$options": "i"}}):
                if doc not in keyword_matches:
                    keyword_matches.append(doc)
        
        logger.info(f"키워드 매치: {len(keyword_matches)}개")
        for i, doc in enumerate(keyword_matches[:3], 1):
            logger.info(f"  {i}. Q: {doc['question']}")
            logger.info(f"     A: {doc['answer'][:100]}...")
        
        # 3. 답변 내용 검색
        answer_matches = []
        async for doc in self.knowledge_collection.find({"answer": {"$regex": query, "$options": "i"}}):
            answer_matches.append(doc)
        
        logger.info(f"답변 매치: {len(answer_matches)}개")
        for i, doc in enumerate(answer_matches[:3], 1):
            logger.info(f"  {i}. Q: {doc['question']}")
            logger.info(f"     A: {doc['answer'][:100]}...")
        
        return {
            "exact_matches": len(exact_matches),
            "keyword_matches": len(keyword_matches),
            "answer_matches": len(answer_matches),
            "total_unique": len(set([doc["_id"] for doc in exact_matches + keyword_matches + answer_matches]))
        }
    
    def _extract_keywords(self, text: str):
        """키워드 추출"""
        import re
        # 한글, 영문, 숫자로 구성된 단어 추출
        words = re.findall(r'[가-힣a-zA-Z0-9]+', text.lower())
        # 2글자 이상, 10글자 이하 단어만 선택
        keywords = [word for word in words if 2 <= len(word) <= 10]
        return keywords[:5]

async def main():
    """메인 함수"""
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.aicounsel
    
    try:
        tester = KnowledgeSearchTester(db)
        
        # 테스트 케이스들
        test_queries = [
            "견적서 출력하면 참조사항이라고 있던데",
            "참조사항이 뭐야",
            "프린터가 안 나와요",
            "포스 시스템 오류",
            "결제 안됨",
            "영수증 안 나와요",
            "설치 방법",
            "설정 방법",
            "네트워크 연결 안됨",
            "로그인 안됨",
            "데이터 백업",
            "업데이트 안됨",
            "키오스크 오류",
            "원격 접속",
            "권한 없음",
            "비밀번호 변경",
            "계정 생성",
            "재고 확인",
            "매출 조회",
            "매출 통계"
        ]
        
        print("🔍 knowledge_base 검색 테스트 시작...")
        print("=" * 60)
        
        for query in test_queries:
            result = await tester.test_search(query)
            print(f"\n📊 '{query}' 검색 결과:")
            print(f"   - 정확한 매치: {result['exact_matches']}개")
            print(f"   - 키워드 매치: {result['keyword_matches']}개")
            print(f"   - 답변 매치: {result['answer_matches']}개")
            print(f"   - 총 고유 결과: {result['total_unique']}개")
            print("-" * 40)
        
    except Exception as e:
        logger.error(f"실행 중 오류: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main()) 