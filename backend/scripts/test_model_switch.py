#!/usr/bin/env python3
"""
모델 전환 테스트 스크립트
"""

import asyncio
import aiohttp
import json
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api/v1"

async def test_model_status():
    """모델 상태를 확인합니다."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/model-status") as response:
            if response.status == 200:
                data = await response.json()
                logger.info("Current model status:")
                logger.info(f"  Current model: {data['current_model']}")
                logger.info(f"  Available models: {data['available_models']}")
                logger.info(f"  Loaded models: {data['loaded_models']}")
                return data
            else:
                logger.error(f"Failed to get model status: {response.status}")
                return None

async def test_model_switch(model_type: str):
    """모델을 전환합니다."""
    async with aiohttp.ClientSession() as session:
        payload = {"model_type": model_type}
        async with session.post(f"{BASE_URL}/switch-model", json=payload) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"✅ Successfully switched to {model_type}")
                logger.info(f"  Response: {data}")
                return True
            else:
                error_data = await response.json()
                logger.error(f"❌ Failed to switch to {model_type}: {error_data}")
                return False

async def test_chat(message: str):
    """채팅을 테스트합니다."""
    async with aiohttp.ClientSession() as session:
        payload = {"message": message}
        async with session.post(f"{BASE_URL}/chat", json=payload) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"Chat response: {data['response'][:100]}...")
                return data
            else:
                error_data = await response.json()
                logger.error(f"Chat failed: {error_data}")
                return None

async def main():
    """메인 테스트 함수"""
    logger.info("Starting model switch test...")
    
    # 1. 현재 모델 상태 확인
    logger.info("\n1. Checking current model status...")
    status = await test_model_status()
    if not status:
        return
    
    # 2. LLaMA 3.1 8B로 전환 (이미 로드되어 있을 수 있음)
    logger.info("\n2. Switching to LLaMA 3.1 8B...")
    success = await test_model_switch("llama-3.1-8b")
    if success:
        await test_chat("안녕하세요!")
    
    # 3. Polyglot-Ko 5.8B로 전환
    logger.info("\n3. Switching to Polyglot-Ko 5.8B...")
    success = await test_model_switch("polyglot-ko-5.8b")
    if success:
        await test_chat("안녕하세요!")
    
    # 4. 다시 LLaMA 3.1 8B로 전환
    logger.info("\n4. Switching back to LLaMA 3.1 8B...")
    success = await test_model_switch("llama-3.1-8b")
    if success:
        await test_chat("안녕하세요!")
    
    # 5. 최종 상태 확인
    logger.info("\n5. Final model status...")
    await test_model_status()
    
    logger.info("\n✅ Model switch test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 