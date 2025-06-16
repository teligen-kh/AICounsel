import os
import csv
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

async def import_csv():
    # MongoDB 연결
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.aicounsel
    collection = db.conversations

    # CSV 파일이 있는 디렉토리
    csv_dir = "D:/AICounsel/data/csv"
    
    if not os.path.exists(csv_dir):
        print(f"Directory not found: {csv_dir}")
        return

    # CSV 파일 목록 가져오기
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in directory")
        return

    print(f"Found {len(csv_files)} CSV files")

    for csv_file in csv_files:
        try:
            file_path = os.path.join(csv_dir, csv_file)
            print(f"Processing {file_path}")
            
            # CSV 파일 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
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

                if not messages:
                    print(f"No messages in {csv_file}")
                    continue

                # 요약 생성
                summary = ""
                if messages:
                    all_messages = [msg["content"] for msg in messages]
                    summary = " ".join(all_messages)
                    if len(summary) > 200:
                        summary = summary[:200] + "..."

                # MongoDB에 저장
                conversation = {
                    'title': csv_file,
                    'messages': messages,
                    'summary': summary,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now(),
                    'status': 'completed',
                    'consultation_start_time': datetime.now()
                }
                
                # 기존 문서 업데이트
                result = await collection.update_one(
                    {'title': csv_file},
                    {'$set': conversation},
                    upsert=True
                )
                
                if result.upserted_id:
                    print(f"Created new document for {csv_file}")
                else:
                    print(f"Updated existing document for {csv_file}")

        except Exception as e:
            print(f"Error processing {csv_file}: {str(e)}")

    print("Import completed")

if __name__ == "__main__":
    asyncio.run(import_csv()) 