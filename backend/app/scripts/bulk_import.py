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
                file_path = os.path.join(directory_path, csv_file)
                
                # CSV 파일 읽기
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 대화 파싱
                utterances = ConversationParser.parse_conversation(content)
                
                if utterances:
                    # 대화 문서 생성
                    conversation = {
                        'id': str(uuid.uuid4()),
                        'title': os.path.splitext(csv_file)[0],
                        'created_at': datetime.now(),
                        'utterances': utterances,
                        'summary': None,  # 나중에 LLM으로 요약 생성
                        'category': None,  # 나중에 분류
                        'tags': []
                    }
                    
                    # MongoDB에 삽입
                    self.collection.insert_one(conversation)
                    logging.info(f"{csv_file} 처리 완료: {len(utterances)}개 발화 삽입됨")
                else:
                    logging.warning(f"{csv_file}에 유효한 대화가 없습니다.")
                    
            except Exception as e:
                logging.error(f"{csv_file} 처리 중 오류 발생: {str(e)}")
                continue
                
    def close(self):
        """MongoDB 연결 종료"""
        self.client.close()

def main():
    # 프로젝트 루트 디렉토리 기준으로 상대 경로 설정
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    csv_directory = os.path.join(project_root, "data", "csv")
    
    # 디렉토리가 없으면 생성
    os.makedirs(csv_directory, exist_ok=True)
    
    importer = BulkCSVImporter()
    try:
        importer.import_csv_directory(csv_directory)
    finally:
        importer.close()

if __name__ == "__main__":
    main() 