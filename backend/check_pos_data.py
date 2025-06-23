import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_pos_data():
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client.aicounsel
    
    try:
        # POS 재설치 관련 데이터 검색
        pos_data = await db.knowledge_base.find({
            'question': {'$regex': '포스.*재설치', '$options': 'i'}
        }).to_list(length=5)
        
        print(f'POS 재설치 관련 데이터: {len(pos_data)}개')
        
        for item in pos_data:
            print(f'Q: {item["question"]}')
            print(f'A: {item["answer"]}')
            print('-' * 50)
            
    except Exception as e:
        print(f'오류 발생: {e}')
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_pos_data()) 