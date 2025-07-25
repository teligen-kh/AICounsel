"""
문맥 관리 API
문맥 패턴과 규칙을 관리하는 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from ...dependencies import get_database
from ...services.context_aware_classifier import ContextAwareClassifier

router = APIRouter(prefix="/context", tags=["context"])

# Pydantic 모델들
class ContextPatternCreate(BaseModel):
    pattern: str
    context: str
    description: str
    priority: int = 2

class ContextPatternUpdate(BaseModel):
    pattern: Optional[str] = None
    context: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    accuracy: Optional[float] = None

class ContextRuleCreate(BaseModel):
    rule_type: str  # "keyword_combination" or "sentence_pattern"
    keywords: Optional[List[str]] = None
    pattern: Optional[str] = None
    context: str
    description: str
    priority: int = 2

class ContextRuleUpdate(BaseModel):
    rule_type: Optional[str] = None
    keywords: Optional[List[str]] = None
    pattern: Optional[str] = None
    context: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None

class ClassificationTest(BaseModel):
    message: str

@router.get("/patterns", response_model=List[Dict[str, Any]])
async def get_context_patterns(
    db: AsyncIOMotorDatabase = Depends(get_database),
    context: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """문맥 패턴 목록 조회"""
    try:
        filter_query = {}
        if context:
            filter_query["context"] = context
        if is_active is not None:
            filter_query["is_active"] = is_active
        
        patterns = []
        async for pattern in db.context_patterns.find(filter_query).sort("priority", 1):
            pattern["_id"] = str(pattern["_id"])
            patterns.append(pattern)
        
        return patterns
    except Exception as e:
        logging.error(f"문맥 패턴 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="문맥 패턴 조회 중 오류가 발생했습니다.")

@router.post("/patterns", response_model=Dict[str, Any])
async def create_context_pattern(
    pattern_data: ContextPatternCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """새로운 문맥 패턴 생성"""
    try:
        classifier = ContextAwareClassifier(db)
        pattern_id = await classifier.add_context_pattern(
            pattern=pattern_data.pattern,
            context=pattern_data.context,
            description=pattern_data.description,
            priority=pattern_data.priority
        )
        
        if pattern_id:
            return {"message": "문맥 패턴이 성공적으로 생성되었습니다.", "pattern_id": str(pattern_id)}
        else:
            raise HTTPException(status_code=400, detail="문맥 패턴 생성에 실패했습니다.")
            
    except Exception as e:
        logging.error(f"문맥 패턴 생성 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="문맥 패턴 생성 중 오류가 발생했습니다.")

@router.put("/patterns/{pattern_id}", response_model=Dict[str, Any])
async def update_context_pattern(
    pattern_id: str,
    pattern_data: ContextPatternUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """문맥 패턴 수정"""
    try:
        from bson import ObjectId
        
        update_data = {}
        if pattern_data.pattern is not None:
            update_data["pattern"] = pattern_data.pattern
        if pattern_data.context is not None:
            update_data["context"] = pattern_data.context
        if pattern_data.description is not None:
            update_data["description"] = pattern_data.description
        if pattern_data.priority is not None:
            update_data["priority"] = pattern_data.priority
        if pattern_data.is_active is not None:
            update_data["is_active"] = pattern_data.is_active
        if pattern_data.accuracy is not None:
            update_data["accuracy"] = pattern_data.accuracy
        
        update_data["updated_at"] = datetime.now()
        
        result = await db.context_patterns.update_one(
            {"_id": ObjectId(pattern_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return {"message": "문맥 패턴이 성공적으로 수정되었습니다."}
        else:
            raise HTTPException(status_code=404, detail="문맥 패턴을 찾을 수 없습니다.")
            
    except Exception as e:
        logging.error(f"문맥 패턴 수정 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="문맥 패턴 수정 중 오류가 발생했습니다.")

@router.delete("/patterns/{pattern_id}", response_model=Dict[str, Any])
async def delete_context_pattern(
    pattern_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """문맥 패턴 삭제"""
    try:
        from bson import ObjectId
        
        result = await db.context_patterns.delete_one({"_id": ObjectId(pattern_id)})
        
        if result.deleted_count > 0:
            return {"message": "문맥 패턴이 성공적으로 삭제되었습니다."}
        else:
            raise HTTPException(status_code=404, detail="문맥 패턴을 찾을 수 없습니다.")
            
    except Exception as e:
        logging.error(f"문맥 패턴 삭제 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="문맥 패턴 삭제 중 오류가 발생했습니다.")

@router.get("/rules", response_model=List[Dict[str, Any]])
async def get_context_rules(
    db: AsyncIOMotorDatabase = Depends(get_database),
    rule_type: Optional[str] = None,
    context: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """문맥 규칙 목록 조회"""
    try:
        filter_query = {}
        if rule_type:
            filter_query["rule_type"] = rule_type
        if context:
            filter_query["context"] = context
        if is_active is not None:
            filter_query["is_active"] = is_active
        
        rules = []
        async for rule in db.context_rules.find(filter_query).sort("priority", 1):
            rule["_id"] = str(rule["_id"])
            rules.append(rule)
        
        return rules
    except Exception as e:
        logging.error(f"문맥 규칙 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="문맥 규칙 조회 중 오류가 발생했습니다.")

@router.post("/rules", response_model=Dict[str, Any])
async def create_context_rule(
    rule_data: ContextRuleCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """새로운 문맥 규칙 생성"""
    try:
        classifier = ContextAwareClassifier(db)
        rule_id = await classifier.add_context_rule(
            rule_type=rule_data.rule_type,
            keywords=rule_data.keywords,
            context=rule_data.context,
            description=rule_data.description,
            priority=rule_data.priority
        )
        
        if rule_id:
            return {"message": "문맥 규칙이 성공적으로 생성되었습니다.", "rule_id": str(rule_id)}
        else:
            raise HTTPException(status_code=400, detail="문맥 규칙 생성에 실패했습니다.")
            
    except Exception as e:
        logging.error(f"문맥 규칙 생성 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="문맥 규칙 생성 중 오류가 발생했습니다.")

@router.put("/rules/{rule_id}", response_model=Dict[str, Any])
async def update_context_rule(
    rule_id: str,
    rule_data: ContextRuleUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """문맥 규칙 수정"""
    try:
        from bson import ObjectId
        
        update_data = {}
        if rule_data.rule_type is not None:
            update_data["rule_type"] = rule_data.rule_type
        if rule_data.keywords is not None:
            update_data["keywords"] = rule_data.keywords
        if rule_data.pattern is not None:
            update_data["pattern"] = rule_data.pattern
        if rule_data.context is not None:
            update_data["context"] = rule_data.context
        if rule_data.description is not None:
            update_data["description"] = rule_data.description
        if rule_data.priority is not None:
            update_data["priority"] = rule_data.priority
        if rule_data.is_active is not None:
            update_data["is_active"] = rule_data.is_active
        
        update_data["updated_at"] = datetime.now()
        
        result = await db.context_rules.update_one(
            {"_id": ObjectId(rule_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return {"message": "문맥 규칙이 성공적으로 수정되었습니다."}
        else:
            raise HTTPException(status_code=404, detail="문맥 규칙을 찾을 수 없습니다.")
            
    except Exception as e:
        logging.error(f"문맥 규칙 수정 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="문맥 규칙 수정 중 오류가 발생했습니다.")

@router.delete("/rules/{rule_id}", response_model=Dict[str, Any])
async def delete_context_rule(
    rule_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """문맥 규칙 삭제"""
    try:
        from bson import ObjectId
        
        result = await db.context_rules.delete_one({"_id": ObjectId(rule_id)})
        
        if result.deleted_count > 0:
            return {"message": "문맥 규칙이 성공적으로 삭제되었습니다."}
        else:
            raise HTTPException(status_code=404, detail="문맥 규칙을 찾을 수 없습니다.")
            
    except Exception as e:
        logging.error(f"문맥 규칙 삭제 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="문맥 규칙 삭제 중 오류가 발생했습니다.")

@router.post("/test", response_model=Dict[str, Any])
async def test_classification(
    test_data: ClassificationTest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """문맥 분류 테스트"""
    try:
        classifier = ContextAwareClassifier(db)
        
        # LLM 서비스 주입
        from ...dependencies import get_llm_service
        import asyncio
        try:
            llm_service = await get_llm_service()
            classifier.inject_llm_service(llm_service)
        except:
            pass  # LLM 서비스가 아직 초기화되지 않은 경우
        
        input_type, details = await classifier.classify_input(test_data.message)
        
        return {
            "message": test_data.message,
            "classification": input_type.value,
            "details": details
        }
        
    except Exception as e:
        logging.error(f"문맥 분류 테스트 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="문맥 분류 테스트 중 오류가 발생했습니다.")

@router.get("/stats", response_model=Dict[str, Any])
async def get_context_stats(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """문맥 분류 통계 조회"""
    try:
        classifier = ContextAwareClassifier(db)
        
        # 패턴 통계
        pattern_stats = await classifier.get_pattern_stats()
        
        # 규칙 통계
        rules_count = await db.context_rules.count_documents({})
        active_rules_count = await db.context_rules.count_documents({"is_active": True})
        
        # 컨텍스트별 통계
        context_stats = {}
        async for pattern in db.context_patterns.find({}):
            context = pattern["context"]
            if context not in context_stats:
                context_stats[context] = {"patterns": 0, "rules": 0}
            context_stats[context]["patterns"] += 1
        
        async for rule in db.context_rules.find({}):
            context = rule["context"]
            if context not in context_stats:
                context_stats[context] = {"patterns": 0, "rules": 0}
            context_stats[context]["rules"] += 1
        
        return {
            "pattern_stats": pattern_stats,
            "rules_count": rules_count,
            "active_rules_count": active_rules_count,
            "context_stats": context_stats
        }
        
    except Exception as e:
        logging.error(f"문맥 통계 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="문맥 통계 조회 중 오류가 발생했습니다.") 