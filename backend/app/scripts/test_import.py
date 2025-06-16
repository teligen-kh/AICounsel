import csv
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

async def test_import():
    # MongoDB 연결
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.aicounsel
    collection = db.conversations

    # 테스트할 CSV 파일
    csv_file = "D:/AICounsel/data/csv/395.07044504290.20240919101557.csv"
    
    try:
        # CSV 파일 읽기
        with open(csv_file, 'r', encoding='utf-8') as f:
            messages = []
            
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                # 발화자와 시간, 내용 분리
                parts = line.split('] ', 1)
                if len(parts) != 2:
                    continue
                    
                speaker_time = parts[0] + ']'
                content = parts[1]
                
                # 발화자와 시간 분리
                speaker = '고객' if '고객' in speaker_time else '상담사'
                time_range = speaker_time.split(']')[0].split('[')[1]
                start_time, end_time = time_range.split(' - ')
                
                message = {
                    'role': 'user' if speaker == '고객' else 'assistant',
                    'speaker': speaker,
                    'start_time': start_time,
                    'end_time': end_time,
                    'content': content
                }
                messages.append(message)
                print(f"생성된 메시지: {message}")

            if not messages:
                print("메시지가 없습니다.")
                return

            # 요약 생성
            summary = ""
            if messages:
                all_messages = [msg["content"] for msg in messages]
                summary = " ".join(all_messages)
                if len(summary) > 200:
                    summary = summary[:200] + "..."

            # MongoDB에 저장
            conversation = {
                'title': '395.07044504290.20240919101557.csv',  # 원본 파일명 사용
                'messages': messages,
                'summary': summary,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'status': 'completed',
                'consultation_start_time': datetime.now()
            }
            
            # 저장 전 데이터 출력
            print("\n저장할 데이터:", conversation)
            
            # 기존 문서 업데이트
            result = await collection.update_one(
                {'title': '395.07044504290.20240919101557.csv'},
                {'$set': conversation},
                upsert=True
            )
            
            if result.upserted_id:
                print(f"\n새로 생성됨. ID: {result.upserted_id}")
            else:
                print("\n기존 문서 업데이트 완료")

    except Exception as e:
        print(f"에러 발생: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_import()) 