import os
import pandas as pd
from pymongo import MongoClient
from tqdm import tqdm
import logging
from datetime import datetime
import re
import uuid
from typing import List, Dict

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bulk_import.log'),
        logging.StreamHandler()
    ]
)

class ConversationParser:
    @staticmethod
    def parse_line(line: str) -> Dict:
        """대화 라인을 파싱하여 발화 정보를 추출"""
        pattern = r'^(고객|상담사)\s+\[(\d{2}:\d{2}:\d{2})\s*-\s*(\d{2}:\d{2}:\d{2})\]\s+(.+)$'
        match = re.match(pattern, line.strip())
        
        if match:
            speaker, start_time, end_time, content = match.groups()
            return {
                'speaker': speaker,
                'start_time': start_time,
                'end_time': end_time,
                'content': content.strip()
            }
        return None

    @staticmethod
    def parse_conversation(text: str) -> List[Dict]:
        """전체 대화 텍스트를 파싱하여 발화 목록 생성"""
        utterances = []
        for line in text.strip().split('\n'):
            if line.strip():
                utterance = ConversationParser.parse_line(line)
                if utterance:
                    utterances.append(utterance)
        return utterances

    @staticmethod
    def extract_datetime_from_filename(filename: str) -> datetime:
        """CSV 파일명에서 날짜와 시간을 추출"""
        # 파일명에서 숫자 부분 추출 (예: 314.01071547275.20240919174442.csv)
        match = re.search(r'(\d{8})(\d{6})', filename)
        if match:
            date_str, time_str = match.groups()
            # YYYYMMDDHHMMSS 형식으로 변환
            datetime_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} {time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
            return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        return None

class BulkCSVImporter:
    def __init__(self, mongo_uri="mongodb://localhost:27017", db_name="aicounsel"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db['conversations']
        
    def import_csv_directory(self, directory_path):
        """디렉토리 내의 모든 CSV 파일을 MongoDB에 임포트"""
        csv_files = [f for f in os.listdir(directory_path) if f.endswith('.csv')]
        
        if not csv_files:
            logging.warning(f"디렉토리 {directory_path}에 CSV 파일이 없습니다.")
            return
            
        logging.info(f"총 {len(csv_files)}개의 CSV 파일을 처리합니다.")
        
        for csv_file in tqdm(csv_files, desc="CSV 파일 처리 중"):
            try:
                # 파일명에서 실제 상담 시간 추출
                consultation_datetime = ConversationParser.extract_datetime_from_filename(csv_file)
                if not consultation_datetime:
                    logging.warning(f"파일명에서 날짜/시간을 추출할 수 없습니다: {csv_file}")
                    continue

                file_path = os.path.join(directory_path, csv_file)
                df = pd.read_csv(file_path, encoding='utf-8')
                
                # 대화 내용 파싱
                messages = []
                for _, row in df.iterrows():
                    if 'content' in row:
                        content = str(row['content'])
                        if content.strip():
                            # 발화자 구분 (고객/상담사)
                            if '고객' in content:
                                role = 'human'
                            else:
                                role = 'assistant'
                            
                            messages.append({
                                'type': role,
                                'content': content.strip()
                            })
                
                if messages:
                    # MongoDB에 저장
                    conversation = {
                        'session_id': str(uuid.uuid4()),
                        'messages': messages,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now(),
                        'consultation_datetime': consultation_datetime,  # 실제 상담 시간 추가
                        'status': 'completed'
                    }
                    
                    self.collection.insert_one(conversation)
                    logging.info(f"파일 처리 완료: {csv_file}")
                
            except Exception as e:
                logging.error(f"파일 처리 중 오류 발생: {csv_file} - {str(e)}")
                continue
        
        logging.info("모든 파일 처리 완료")
    
    def close(self):
        """MongoDB 연결 종료"""
        self.client.close()

def main():
    importer = BulkCSVImporter()
    try:
        importer.import_csv_directory("data/csv")  # CSV 파일이 있는 디렉토리 경로
    finally:
        importer.close()

if __name__ == "__main__":
    main() 