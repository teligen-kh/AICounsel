#!/usr/bin/env python3
import asyncio
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from app.database import get_database

async def add_knowledge_base():
    db = await get_database()
    
    knowledge_items = [
        {
            "question": "법인결재란이 안보이는데 없어진건가요?",
            "answer": "법인결재란은 현재 시스템에서 정상적으로 제공되고 있습니다. 만약 화면에서 보이지 않는다면 다음을 확인해주세요:\n\n1. 로그인 권한 확인\n2. 메뉴 설정에서 '법인결재' 활성화\n3. 브라우저 새로고침\n4. 캐시 삭제 후 재접속\n\n여전히 문제가 있다면 고객센터로 문의해주세요.",
            "keywords": ["법인결재", "결재", "메뉴", "화면", "보이지 않음"],
            "category": "technical"
        },
        {
            "question": "포스 설치 방법",
            "answer": "포스 설치는 smart.arumnet.com에서 진행하세요.\n\n설치 과정:\n1. smart.arumnet.com 접속\n2. 포스 프로그램 다운로드\n3. 설치 파일 실행\n4. 라이선스 키 입력\n5. 설정 완료\n\n설치 중 문제가 있으면 고객센터로 연락주세요.",
            "keywords": ["포스", "설치", "smart.arumnet.com", "다운로드"],
            "category": "technical"
        },
        {
            "question": "프린터 오류 해결",
            "answer": "프린터 오류 해결 방법:\n\n1. 프린터 전원 확인\n2. USB 케이블 연결 상태 확인\n3. 프린터 드라이버 재설치\n4. 프린터 큐 초기화\n5. 포스 프로그램 재시작\n\n위 방법으로도 해결되지 않으면 고객센터로 문의해주세요.",
            "keywords": ["프린터", "오류", "해결", "드라이버", "재설치"],
            "category": "technical"
        }
    ]
    
    for item in knowledge_items:
        await db.knowledge_base.insert_one(item)
        print(f'✅ 추가됨: {item["question"][:30]}...')
    
    print('\n🎉 Knowledge Base 추가 완료!')

if __name__ == "__main__":
    asyncio.run(add_knowledge_base()) 