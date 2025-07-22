"""
키워드 관리 API 모듈
입력 분류를 위한 키워드를 동적으로 관리할 수 있는 API 제공
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel
from ...database import get_database
from ...services.db_based_input_classifier import DBBasedInputClassifier

router = APIRouter()

class KeywordItem(BaseModel):
    category: str
    keyword: str

class KeywordCategory(BaseModel):
    category: str
    keywords: List[str]
    description: str

class KeywordResponse(BaseModel):
    category: str
    keywords: List[str]
    description: str
    count: int

@router.post("/keywords/add")
async def add_keyword(
    item: KeywordItem,
    db = Depends(get_database)
):
    """새로운 키워드를 추가합니다."""
    try:
        classifier = DBBasedInputClassifier(db)
        success = await classifier.add_keyword(item.category, item.keyword)
        
        if success:
            return {"message": f"키워드 추가 성공: {item.category} - {item.keyword}"}
        else:
            raise HTTPException(status_code=400, detail="키워드 추가 실패")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"키워드 추가 중 오류: {str(e)}")

@router.delete("/keywords/remove")
async def remove_keyword(
    item: KeywordItem,
    db = Depends(get_database)
):
    """키워드를 제거합니다."""
    try:
        classifier = DBBasedInputClassifier(db)
        success = await classifier.remove_keyword(item.category, item.keyword)
        
        if success:
            return {"message": f"키워드 제거 성공: {item.category} - {item.keyword}"}
        else:
            raise HTTPException(status_code=400, detail="키워드 제거 실패")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"키워드 제거 중 오류: {str(e)}")

@router.get("/keywords", response_model=List[KeywordResponse])
async def get_keywords(
    category: Optional[str] = None,
    db = Depends(get_database)
):
    """키워드 목록을 조회합니다."""
    try:
        classifier = DBBasedInputClassifier(db)
        categories = await classifier.load_keywords_from_db()
        
        result = []
        for cat, keywords in categories.items():
            if category is None or cat == category:
                # 카테고리 설명 가져오기
                cat_info = await db.input_keywords.find_one({"category": cat})
                description = cat_info.get("description", "") if cat_info else ""
                
                result.append(KeywordResponse(
                    category=cat,
                    keywords=keywords,
                    description=description,
                    count=len(keywords)
                ))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"키워드 조회 중 오류: {str(e)}")

@router.post("/keywords/refresh")
async def refresh_keywords(
    db = Depends(get_database)
):
    """키워드 캐시를 새로고침합니다."""
    try:
        classifier = DBBasedInputClassifier(db)
        await classifier.refresh_cache()
        return {"message": "키워드 캐시 새로고침 완료"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"키워드 새로고침 중 오류: {str(e)}")

@router.post("/keywords/test")
async def test_classification(
    text: str,
    db = Depends(get_database)
):
    """텍스트 분류를 테스트합니다."""
    try:
        classifier = DBBasedInputClassifier(db)
        input_type, details = await classifier.classify_input(text)
        
        return {
            "input_text": text,
            "classification": input_type.value,
            "details": details,
            "template_response": await classifier.get_response_template(input_type)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분류 테스트 중 오류: {str(e)}")

@router.post("/keywords/auto-extract")
async def auto_extract_keywords(
    db = Depends(get_database)
):
    """knowledge_base에서 자동으로 키워드를 추출하여 technical 카테고리에 추가합니다."""
    try:
        # knowledge_base의 모든 키워드 수집
        all_keywords = set()
        async for item in db.knowledge_base.find({}):
            if 'keywords' in item and item['keywords']:
                all_keywords.update(item['keywords'])
        
        if all_keywords:
            # technical 카테고리 업데이트
            technical_keywords = list(all_keywords)
            
            await db.input_keywords.update_one(
                {"category": "technical"},
                {"$set": {
                    "keywords": technical_keywords,
                    "updated_at": datetime.now()
                }}
            )
            
            return {
                "message": f"자동 키워드 추출 완료",
                "extracted_count": len(technical_keywords),
                "keywords": technical_keywords[:20]  # 처음 20개만 반환
            }
        else:
            return {"message": "추출할 키워드가 없습니다."}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"키워드 추출 중 오류: {str(e)}") 