import asyncio
from app.database import get_database

async def check_users():
    try:
        db = await get_database()
        cursor = db.users.find({}, {'username': 1, 'email': 1, '_id': 0})
        users = await cursor.to_list(length=None)
        print('데이터베이스의 사용자 목록:')
        for user in users:
            print(f"  - 사용자명: {user.get('username', 'N/A')}, 이메일: {user.get('email', 'N/A')}")
        print(f'총 {len(users)}명의 사용자가 있습니다.')
    except Exception as e:
        print(f'오류 발생: {e}')

if __name__ == "__main__":
    asyncio.run(check_users()) 