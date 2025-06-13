from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, List
from ..database import get_database

router = APIRouter()

class AnalysisRequest(BaseModel):
    startDate: str
    endDate: str

@router.post("/analysis")
async def analyze_conversations(request: AnalysisRequest) -> Dict[str, Any]:
    try:
        start_date = datetime.fromisoformat(request.startDate.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(request.endDate.replace('Z', '+00:00'))
        
        db = await get_database()
        collection = db.conversations
        
        # 날짜 범위에 맞는 대화만 필터링
        cursor = collection.find({
            'created_at': {
                '$gte': start_date,
                '$lte': end_date
            }
        })
        conversations = await cursor.to_list(length=None)
        
        if not conversations:
            return {
                'basic_stats': {
                    'total_conversations': 0,
                    'total_messages': 0,
                    'role_stats': {'user': 0, 'assistant': 0},
                    'avg_conversation_length': 0
                },
                'patterns': {
                    'user_first': 0,
                    'assistant_first': 0,
                    'avg_turn_length': 0,
                    'max_turn_length': 0
                },
                'keywords': {}
            }
        
        # 기본 통계 계산
        total_conversations = len(conversations)
        total_messages = sum(len(conv['messages']) for conv in conversations)
        role_stats = {
            'user': sum(1 for conv in conversations for msg in conv['messages'] if msg['role'] == 'user'),
            'assistant': sum(1 for conv in conversations for msg in conv['messages'] if msg['role'] == 'assistant')
        }
        avg_conversation_length = total_messages / total_conversations if total_conversations > 0 else 0
        
        # 대화 패턴 분석
        user_first = sum(1 for conv in conversations if conv['messages'][0]['role'] == 'user')
        assistant_first = total_conversations - user_first
        
        # 턴 길이 분석
        turn_lengths = []
        for conv in conversations:
            current_role = None
            current_length = 0
            for msg in conv['messages']:
                if current_role != msg['role']:
                    if current_length > 0:
                        turn_lengths.append(current_length)
                    current_role = msg['role']
                    current_length = 1
                else:
                    current_length += 1
            if current_length > 0:
                turn_lengths.append(current_length)
        
        avg_turn_length = sum(turn_lengths) / len(turn_lengths) if turn_lengths else 0
        max_turn_length = max(turn_lengths) if turn_lengths else 0
        
        # 키워드 분석 (간단한 구현)
        keywords = {}
        for conv in conversations:
            for msg in conv['messages']:
                if msg['role'] == 'user':
                    words = msg['content'].lower().split()
                    for word in words:
                        if len(word) > 2:  # 2글자 이상만 카운트
                            keywords[word] = keywords.get(word, 0) + 1
        
        # 상위 10개 키워드만 반환
        top_keywords = dict(sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10])
        
        return {
            'basic_stats': {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'role_stats': role_stats,
                'avg_conversation_length': round(avg_conversation_length, 2)
            },
            'patterns': {
                'user_first': user_first,
                'assistant_first': assistant_first,
                'avg_turn_length': round(avg_turn_length, 2),
                'max_turn_length': max_turn_length
            },
            'keywords': top_keywords
        }
            
    except Exception as e:
        print(f"Analysis error: {str(e)}")  # 서버 로그에 에러 출력
        raise HTTPException(status_code=500, detail=str(e)) 