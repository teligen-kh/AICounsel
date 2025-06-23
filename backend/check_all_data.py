import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_all_data():
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client.aicounsel
    
    try:
        # 전체 데이터 개수 확인
        total_count = await db.knowledge_base.count_documents({})
        print(f'전체 데이터 개수: {total_count}개')
        print('=' * 60)
        
        # 키워드별 검색
        keywords = [
            ('포스', '포스 관련'),
            ('키오스크', '키오스크 관련'),
            ('프로그램', '프로그램 관련'),
            ('설치', '설치 관련'),
            ('오류', '오류 관련'),
            ('백업', '백업 관련'),
            ('SQL', 'SQL 관련'),
            ('재설치', '재설치 관련')
        ]
        
        for keyword, description in keywords:
            count = await db.knowledge_base.count_documents({
                '$or': [
                    {'question': {'$regex': keyword, '$options': 'i'}},
                    {'answer': {'$regex': keyword, '$options': 'i'}}
                ]
            })
            print(f'{description}: {count}개')
        
        print('=' * 60)
        
        # 샘플 데이터 몇 개 출력
        print('샘플 데이터:')
        sample_data = await db.knowledge_base.find({}).limit(3).to_list(length=3)
        
        for i, item in enumerate(sample_data, 1):
            print(f'\n{i}. Q: {item["question"]}')
            print(f'   A: {item["answer"][:100]}...' if len(item["answer"]) > 100 else f'   A: {item["answer"]}')
            print('-' * 50)
            
    except Exception as e:
        print(f'오류 발생: {e}')
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_all_data()) 