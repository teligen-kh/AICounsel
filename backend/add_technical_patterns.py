#!/usr/bin/env python3
import asyncio
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from app.database import get_database
from app.services.context_aware_classifier import ContextAwareClassifier

async def add_technical_patterns():
    db = await get_database()
    classifier = ContextAwareClassifier(db)
    
    technical_patterns = [
        ('법인결재', 'technical', '법인결재 관련 질문'),
        ('법인결재란', 'technical', '법인결재란 관련 질문'),
        ('포스 설치', 'technical', '포스 설치 관련 질문'),
        ('포스 설정', 'technical', '포스 설정 관련 질문'),
        ('프린터 오류', 'technical', '프린터 오류 관련 질문'),
        ('키오스크 설정', 'technical', '키오스크 설정 관련 질문'),
        ('카드리더기', 'technical', '카드리더기 관련 질문'),
        ('영수증 출력', 'technical', '영수증 출력 관련 질문'),
        ('바코드 스캔', 'technical', '바코드 스캔 관련 질문'),
        ('QR코드', 'technical', 'QR코드 관련 질문'),
        ('프로그램 설치', 'technical', '프로그램 설치 관련 질문'),
        ('소프트웨어 업데이트', 'technical', '소프트웨어 업데이트 관련 질문'),
        ('하드웨어 문제', 'technical', '하드웨어 문제 관련 질문'),
        ('드라이버 설치', 'technical', '드라이버 설치 관련 질문'),
        ('재설치', 'technical', '재설치 관련 질문'),
        ('백업', 'technical', '백업 관련 질문'),
        ('복구', 'technical', '복구 관련 질문'),
        ('오류 해결', 'technical', '오류 해결 관련 질문'),
        ('문제 해결', 'technical', '문제 해결 관련 질문'),
        ('시스템 설정', 'technical', '시스템 설정 관련 질문')
    ]
    
    for pattern, context, description in technical_patterns:
        await classifier.add_context_pattern(pattern, context, description, priority=1)
        print(f'✅ 추가됨: {pattern} -> {context}')
    
    print('\n🎉 Technical 패턴 추가 완료!')

if __name__ == "__main__":
    asyncio.run(add_technical_patterns()) 