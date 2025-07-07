#!/usr/bin/env python3
"""
수정된 Polyglot-Ko LLM 서비스 테스트
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.llm_service import LLMService

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_polyglot_service():
    """수정된 Polyglot-Ko 서비스 테스트"""
    
    try:
        logging.info("=== 수정된 Polyglot-Ko 서비스 테스트 시작 ===")
        
        # LLM 서비스 초기화
        llm_service = LLMService(use_db_priority=False, model_type="polyglot-ko-5.8b")
        logging.info("LLM 서비스 초기화 완료")
        
        # 테스트 케이스들
        test_cases = [
            "안녕하세요",
            "오늘 날씨가 좋네요",
            "도움이 필요하신가요?",
            "상품 등록 방법 알려주세요",
            "감사합니다"
        ]
        
        for i, test_input in enumerate(test_cases, 1):
            logging.info(f"\n--- 테스트 {i}: '{test_input}' ---")
            
            try:
                # 메시지 처리
                start_time = asyncio.get_event_loop().time()
                response = await llm_service.process_message(test_input)
                end_time = asyncio.get_event_loop().time()
                
                processing_time = (end_time - start_time) * 1000
                
                logging.info(f"입력: '{test_input}'")
                logging.info(f"응답: '{response}'")
                logging.info(f"처리 시간: {processing_time:.2f}ms")
                logging.info(f"응답 길이: {len(response)}")
                
                # 응답 품질 평가
                if response and len(response) > 0:
                    logging.info("✅ 정상 응답")
                else:
                    logging.warning("❌ 빈 응답")
                    
            except Exception as e:
                logging.error(f"테스트 {i} 실패: {str(e)}")
        
        logging.info("\n=== 테스트 완료 ===")
        
    except Exception as e:
        logging.error(f"서비스 테스트 실패: {str(e)}")
        import traceback
        logging.error(f"상세 오류: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_polyglot_service()) 