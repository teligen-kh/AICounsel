#!/usr/bin/env python3
import asyncio
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, backend_dir)

from app.database import get_database

async def check_patterns():
    db = await get_database()
    count = await db.context_patterns.count_documents({})
    print(f"Context Patterns 총 개수: {count}")
    
    cursor = db.context_patterns.find().limit(5)
    patterns = await cursor.to_list(length=5)
    print("샘플 패턴들:")
    for p in patterns:
        print(f"- {p['pattern']} -> {p['context']}")

if __name__ == "__main__":
    asyncio.run(check_patterns()) 