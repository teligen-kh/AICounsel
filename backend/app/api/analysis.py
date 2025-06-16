from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..database import get_database
import re

router = APIRouter(prefix="/analysis")

class AnalysisRequest(BaseModel):
    startDate: str
    endDate: str

class SearchRequest(BaseModel):
    startDate: str
    endDate: str
    keyword: Optional[str] = None

# 불용어 목록
stop_words = {'안녕', '네', '아니요', '그래', '음', '어', '저', '이', '그', '저거', '이거', '그거'}

def extract_nouns(text: str) -> List[str]:
    """텍스트에서 명사만 추출"""
    # 한글 단어 추출 (2글자 이상)
    words = re.findall(r'[가-힣]{2,}', text)
    
    # 불용어가 아닌 단어만 필터링
    return [word for word in words if word not in stop_words]

@router.post("/search")
async def search_conversations(request: SearchRequest) -> Dict[str, Any]:
    try:
        start_date = datetime.fromisoformat(request.startDate.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(request.endDate.replace('Z', '+00:00'))
        
        db = await get_database()
        collection = db.conversations
        
        # 기본 쿼리: 날짜 범위
        query = {
            'consultation_start_time': {
                '$gte': start_date,
                '$lte': end_date
            }
        }
        
        # 키워드 검색이 있는 경우
        if request.keyword:
            keyword = request.keyword.lower()
            # messages 배열의 content에서 키워드 검색
            query['$or'] = [
                {'messages.content': {'$regex': keyword, '$options': 'i'}},
                {'utterances.text': {'$regex': keyword, '$options': 'i'}},
                {'title': {'$regex': keyword, '$options': 'i'}}
            ]
        
        # 필요한 필드만 선택
        projection = {
            '_id': 1,
            'title': 1,
            'consultation_start_time': 1,
            'messages': 1,
            'utterances': 1,
            'status': 1
        }
        
        # 날짜순으로 정렬
        cursor = collection.find(query, projection).sort('consultation_start_time', -1)
        conversations = await cursor.to_list(length=None)
        
        # 응답 데이터 가공
        result = []
        for conv in conversations:
            # 메시지 내용을 요약으로 사용
            summary = ""
            messages = []
            
            # utterances가 있는 경우 messages로 변환
            if 'utterances' in conv and conv['utterances']:
                for utterance in conv['utterances']:
                    message = {
                        'role': 'user' if utterance.get('speaker') == '고객' else 'assistant',
                        'content': utterance.get('text', ''),
                        'timestamp': utterance.get('timestamp')
                    }
                    messages.append(message)
            # messages가 있는 경우 그대로 사용
            elif 'messages' in conv and conv['messages']:
                messages = conv['messages']
            
            # 요약 생성
            if messages:
                all_messages = []
                for msg in messages:
                    if 'content' in msg:
                        all_messages.append(msg['content'])
                summary = " ".join(all_messages)
                if len(summary) > 200:  # 200자로 제한
                    summary = summary[:200] + "..."
            
            result.append({
                'id': str(conv['_id']),
                'title': conv.get('title', ''),
                'consultation_time': conv.get('consultation_start_time'),
                'summary': summary,
                'status': conv.get('status', 'unknown'),
                'message_count': len(messages),
                'messages': messages  # 전체 메시지 내용도 포함
            })
        
        return {
            'total': len(result),
            'conversations': result
        }
            
    except Exception as e:
        print(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def analyze_conversations(request: AnalysisRequest) -> Dict[str, Any]:
    try:
        start_date = datetime.fromisoformat(request.startDate.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(request.endDate.replace('Z', '+00:00'))
        
        db = await get_database()
        collection = db.conversations
        
        # 상담 시작 시간으로 필터링
        cursor = collection.find({
            'consultation_start_time': {
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
        total_messages = 0
        role_stats = {'user': 0, 'assistant': 0}
        
        for conv in conversations:
            if 'messages' in conv:
                messages = conv['messages']
                total_messages += len(messages)
                for msg in messages:
                    if 'role' in msg:
                        role = msg['role']
                        role_stats[role] = role_stats.get(role, 0) + 1
        
        avg_conversation_length = total_messages / total_conversations if total_conversations > 0 else 0
        
        # 대화 패턴 분석
        user_first = 0
        assistant_first = 0
        
        for conv in conversations:
            if 'messages' in conv and conv['messages']:
                first_msg = conv['messages'][0]
                if 'role' in first_msg:
                    if first_msg['role'] == 'user':
                        user_first += 1
                    else:
                        assistant_first += 1
        
        # 턴 길이 분석
        turn_lengths = []
        for conv in conversations:
            if 'messages' in conv:
                current_role = None
                current_length = 0
                for msg in conv['messages']:
                    if 'role' in msg:
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
        
        # 키워드 분석 (명사만 추출)
        keywords = {}
        for conv in conversations:
            if 'messages' in conv:
                for msg in conv['messages']:
                    if 'role' in msg and msg['role'] == 'user' and 'content' in msg:
                        # 명사만 추출
                        nouns = extract_nouns(msg['content'])
                        for noun in nouns:
                            keywords[noun] = keywords.get(noun, 0) + 1
        
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