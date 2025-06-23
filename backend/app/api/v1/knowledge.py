from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from ...database import get_database
from ...services.mongodb_search_service import MongoDBSearchService

router = APIRouter()

class KnowledgeItem(BaseModel):
    question: str
    answer: str
    keywords: Optional[List[str]] = None
    category: Optional[str] = None

class KnowledgeResponse(BaseModel):
    id: str
    question: str
    answer: str
    keywords: List[str]
    category: str
    created_at: datetime
    updated_at: datetime

@router.post("/knowledge", response_model=KnowledgeResponse)
async def add_knowledge_item(
    item: KnowledgeItem,
    db = Depends(get_database)
):
    """지식 베이스에 새로운 항목을 추가합니다."""
    try:
        search_service = MongoDBSearchService(db)
        
        # 키워드가 제공되지 않은 경우 자동 추출
        if not item.keywords:
            item.keywords = search_service._extract_keywords(item.question)
        
        # 지식 베이스에 저장
        knowledge_item = {
            'question': item.question,
            'answer': item.answer,
            'keywords': item.keywords,
            'category': item.category or '일반',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        result = await db.knowledge_base.insert_one(knowledge_item)
        
        # 저장된 항목 반환
        saved_item = await db.knowledge_base.find_one({"_id": result.inserted_id})
        
        return KnowledgeResponse(
            id=str(saved_item["_id"]),
            question=saved_item["question"],
            answer=saved_item["answer"],
            keywords=saved_item["keywords"],
            category=saved_item["category"],
            created_at=saved_item["created_at"],
            updated_at=saved_item["updated_at"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"지식 베이스 추가 실패: {str(e)}")

@router.get("/knowledge", response_model=List[KnowledgeResponse])
async def get_knowledge_items(
    category: Optional[str] = None,
    limit: int = 50,
    db = Depends(get_database)
):
    """지식 베이스 항목들을 조회합니다."""
    try:
        query = {}
        if category:
            query["category"] = category
        
        cursor = db.knowledge_base.find(query).limit(limit)
        items = []
        
        async for item in cursor:
            items.append(KnowledgeResponse(
                id=str(item["_id"]),
                question=item["question"],
                answer=item["answer"],
                keywords=item["keywords"],
                category=item["category"],
                created_at=item["created_at"],
                updated_at=item["updated_at"]
            ))
        
        return items
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"지식 베이스 조회 실패: {str(e)}")

@router.get("/knowledge/search")
async def search_knowledge(
    query: str,
    limit: int = 10,
    db = Depends(get_database)
):
    """지식 베이스에서 관련 항목을 검색합니다."""
    try:
        search_service = MongoDBSearchService(db)
        results = await search_service.search_relevant_answers(query, limit)
        
        # 지식 베이스 결과만 필터링
        knowledge_results = [result for result in results if result.get('source') == 'knowledge_base']
        
        return {
            "query": query,
            "results": knowledge_results,
            "total_count": len(knowledge_results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"지식 베이스 검색 실패: {str(e)}")

@router.put("/knowledge/{item_id}", response_model=KnowledgeResponse)
async def update_knowledge_item(
    item_id: str,
    item: KnowledgeItem,
    db = Depends(get_database)
):
    """지식 베이스 항목을 수정합니다."""
    try:
        from bson import ObjectId
        
        # 키워드가 제공되지 않은 경우 자동 추출
        if not item.keywords:
            search_service = MongoDBSearchService(db)
            item.keywords = search_service._extract_keywords(item.question)
        
        update_data = {
            'question': item.question,
            'answer': item.answer,
            'keywords': item.keywords,
            'category': item.category or '일반',
            'updated_at': datetime.now()
        }
        
        result = await db.knowledge_base.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="지식 베이스 항목을 찾을 수 없습니다.")
        
        # 수정된 항목 반환
        updated_item = await db.knowledge_base.find_one({"_id": ObjectId(item_id)})
        
        return KnowledgeResponse(
            id=str(updated_item["_id"]),
            question=updated_item["question"],
            answer=updated_item["answer"],
            keywords=updated_item["keywords"],
            category=updated_item["category"],
            created_at=updated_item["created_at"],
            updated_at=updated_item["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"지식 베이스 수정 실패: {str(e)}")

@router.delete("/knowledge/{item_id}")
async def delete_knowledge_item(
    item_id: str,
    db = Depends(get_database)
):
    """지식 베이스 항목을 삭제합니다."""
    try:
        from bson import ObjectId
        
        result = await db.knowledge_base.delete_one({"_id": ObjectId(item_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="지식 베이스 항목을 찾을 수 없습니다.")
        
        return {"message": "지식 베이스 항목이 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"지식 베이스 삭제 실패: {str(e)}")

@router.get("/knowledge/categories")
async def get_knowledge_categories(db = Depends(get_database)):
    """지식 베이스의 모든 카테고리를 조회합니다."""
    try:
        categories = await db.knowledge_base.distinct("category")
        return {"categories": categories}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"카테고리 조회 실패: {str(e)}") 