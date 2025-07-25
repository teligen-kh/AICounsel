"""
knowledge_base 중복 데이터 제거 스크립트
"""

import asyncio
import motor.motor_asyncio
from datetime import datetime
import logging
from typing import List, Dict, Set
import hashlib
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DuplicateRemover:
    """knowledge_base 중복 데이터 제거"""
    
    def __init__(self, db):
        self.db = db
        self.knowledge_collection = db.knowledge_base
    
    def _normalize_text(self, text: str) -> str:
        """텍스트 정규화 (중복 체크용)"""
        if not text:
            return ""
        
        # 소문자 변환 및 공백 정리
        normalized = text.lower().strip()
        
        # 특수문자 제거 (하지만 한글은 유지)
        normalized = re.sub(r'[^\w\s가-힣]', '', normalized)
        
        # 연속된 공백을 하나로
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _generate_hash(self, text: str) -> str:
        """텍스트 해시 생성 (중복 체크용)"""
        normalized = self._normalize_text(text)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    async def find_duplicates(self) -> Dict[str, List]:
        """중복 데이터 찾기"""
        logger.info("중복 데이터 검색 중...")
        
        # 질문별로 그룹화
        question_groups = {}
        
        async for doc in self.knowledge_collection.find({}):
            question = doc.get("question", "").strip()
            if not question:
                continue
            
            # 질문 정규화
            normalized_question = self._normalize_text(question)
            
            if normalized_question not in question_groups:
                question_groups[normalized_question] = []
            
            question_groups[normalized_question].append(doc)
        
        # 중복이 있는 그룹만 필터링
        duplicates = {}
        for question, docs in question_groups.items():
            if len(docs) > 1:
                duplicates[question] = docs
        
        logger.info(f"중복 질문 수: {len(duplicates)}")
        for question, docs in duplicates.items():
            logger.info(f"  - '{question[:50]}...': {len(docs)}개")
        
        return duplicates
    
    async def remove_duplicates(self, keep_strategy: str = "latest") -> Dict:
        """중복 데이터 제거"""
        logger.info("중복 데이터 제거 시작...")
        
        duplicates = await self.find_duplicates()
        
        total_removed = 0
        total_kept = 0
        
        for question, docs in duplicates.items():
            logger.info(f"처리 중: '{question[:50]}...' ({len(docs)}개)")
            
            if keep_strategy == "latest":
                # 가장 최근 데이터 유지
                docs.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
                keep_doc = docs[0]
                remove_docs = docs[1:]
            elif keep_strategy == "longest_answer":
                # 가장 긴 답변 유지
                docs.sort(key=lambda x: len(x.get("answer", "")), reverse=True)
                keep_doc = docs[0]
                remove_docs = docs[1:]
            else:
                # 첫 번째 데이터 유지
                keep_doc = docs[0]
                remove_docs = docs[1:]
            
            # 제거할 문서들의 ID 수집
            remove_ids = [doc["_id"] for doc in remove_docs]
            
            # 중복 제거
            if remove_ids:
                result = await self.knowledge_collection.delete_many({"_id": {"$in": remove_ids}})
                removed_count = result.deleted_count
                total_removed += removed_count
                total_kept += 1
                
                logger.info(f"  - 유지: 1개, 제거: {removed_count}개")
                
                # 유지된 문서의 답변 출력
                answer = keep_doc.get("answer", "")[:100]
                logger.info(f"  - 유지된 답변: {answer}...")
        
        return {
            "total_duplicate_groups": len(duplicates),
            "total_removed": total_removed,
            "total_kept": total_kept
        }
    
    async def get_statistics(self) -> Dict:
        """현재 통계 정보"""
        total_count = await self.knowledge_collection.count_documents({})
        
        # 소스별 통계
        pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        source_stats = []
        async for result in self.knowledge_collection.aggregate(pipeline):
            source_stats.append({
                "source": result["_id"],
                "count": result["count"]
            })
        
        return {
            "total_documents": total_count,
            "source_statistics": source_stats
        }

async def main():
    """메인 함수"""
    # MongoDB 연결
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.aicounsel
    
    try:
        remover = DuplicateRemover(db)
        
        # 현재 통계
        stats = await remover.get_statistics()
        print(f"\n📊 현재 통계:")
        print(f"   - 총 문서 수: {stats['total_documents']}")
        for source_stat in stats['source_statistics']:
            print(f"   - {source_stat['source']}: {source_stat['count']}개")
        
        # 중복 제거
        result = await remover.remove_duplicates(keep_strategy="longest_answer")
        
        print(f"\n✅ 중복 제거 완료!")
        print(f"   - 중복 그룹 수: {result['total_duplicate_groups']}")
        print(f"   - 제거된 문서: {result['total_removed']}개")
        print(f"   - 유지된 문서: {result['total_kept']}개")
        
        # 제거 후 통계
        stats_after = await remover.get_statistics()
        print(f"\n📊 제거 후 통계:")
        print(f"   - 총 문서 수: {stats_after['total_documents']}")
        for source_stat in stats_after['source_statistics']:
            print(f"   - {source_stat['source']}: {source_stat['count']}개")
        
    except Exception as e:
        logger.error(f"실행 중 오류: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main()) 