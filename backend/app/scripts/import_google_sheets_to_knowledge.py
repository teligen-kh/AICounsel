"""
구글 스프레드시트에서 knowledge_base로 데이터 가져오기
중복 제외 및 일괄 등록
"""

import asyncio
import motor.motor_asyncio
from datetime import datetime
import logging
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Set
import hashlib
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleSheetsImporter:
    """구글 스프레드시트에서 knowledge_base로 데이터 가져오기"""
    
    def __init__(self, db):
        self.db = db
        self.knowledge_collection = db.knowledge_base
        
        # 구글 스프레드시트 설정
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # 서비스 계정 키 파일 경로 (필요시 수정)
        self.credentials_file = 'google_credentials.json'
        
    def setup_google_sheets(self):
        """구글 스프레드시트 연결 설정"""
        try:
            # 서비스 계정 인증
            creds = Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=self.scope
            )
            client = gspread.authorize(creds)
            return client
        except FileNotFoundError:
            logger.error(f"❌ 구글 인증 파일을 찾을 수 없습니다: {self.credentials_file}")
            logger.info("구글 스프레드시트 API 사용을 위한 설정이 필요합니다.")
            return None
        except Exception as e:
            logger.error(f"구글 스프레드시트 연결 오류: {str(e)}")
            return None
    
    def load_csv_as_fallback(self, csv_file_path: str) -> pd.DataFrame:
        """CSV 파일을 대안으로 로드"""
        try:
            logger.info(f"CSV 파일 로드 중: {csv_file_path}")
            df = pd.read_csv(csv_file_path, encoding='utf-8')
            logger.info(f"CSV 로드 완료: {len(df)}행")
            return df
        except Exception as e:
            logger.error(f"CSV 파일 로드 오류: {str(e)}")
            return None
    
    def get_sheet_data(self, sheet_url: str = None, sheet_name: str = None, csv_fallback: str = None) -> pd.DataFrame:
        """구글 스프레드시트 또는 CSV에서 데이터 가져오기"""
        
        # 1. 구글 스프레드시트 시도
        if sheet_url:
            client = self.setup_google_sheets()
            if client:
                try:
                    logger.info("구글 스프레드시트에서 데이터 가져오기 시도...")
                    
                    # URL에서 스프레드시트 ID 추출
                    sheet_id = self._extract_sheet_id(sheet_url)
                    if not sheet_id:
                        raise ValueError("스프레드시트 URL에서 ID를 추출할 수 없습니다.")
                    
                    # 스프레드시트 열기
                    spreadsheet = client.open_by_key(sheet_id)
                    
                    # 워크시트 선택
                    if sheet_name:
                        worksheet = spreadsheet.worksheet(sheet_name)
                    else:
                        worksheet = spreadsheet.get_worksheet(0)  # 첫 번째 시트
                    
                    # 데이터 가져오기
                    data = worksheet.get_all_records()
                    df = pd.DataFrame(data)
                    
                    logger.info(f"구글 스프레드시트 로드 완료: {len(df)}행")
                    return df
                    
                except Exception as e:
                    logger.error(f"구글 스프레드시트 로드 오류: {str(e)}")
                    logger.info("CSV 파일로 대체합니다.")
        
        # 2. CSV 파일 대안
        if csv_fallback:
            return self.load_csv_as_fallback(csv_fallback)
        
        return None
    
    def _extract_sheet_id(self, url: str) -> str:
        """구글 스프레드시트 URL에서 ID 추출"""
        import re
        pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    def _normalize_text(self, text: str) -> str:
        """텍스트 정규화 (중복 체크용)"""
        if not text:
            return ""
        
        # 소문자 변환 및 공백 정리
        normalized = text.lower().strip()
        
        # 특수문자 제거 (하지만 한글은 유지)
        normalized = re.sub(r'[^\w\s가-힣]', '', normalized)
        
        # 연속된 공백을 하나로
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _generate_hash(self, text: str) -> str:
        """텍스트 해시 생성 (중복 체크용)"""
        normalized = self._normalize_text(text)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    async def get_existing_hashes(self) -> Set[str]:
        """기존 knowledge_base의 해시값들 가져오기"""
        existing_hashes = set()
        
        async for doc in self.knowledge_collection.find({}):
            question = doc.get("question", "")
            answer = doc.get("answer", "")
            
            # 질문과 답변을 합쳐서 해시 생성
            combined_text = f"{question} {answer}"
            hash_value = self._generate_hash(combined_text)
            existing_hashes.add(hash_value)
        
        logger.info(f"기존 knowledge_base 해시 수: {len(existing_hashes)}")
        return existing_hashes
    
    async def import_data(self, df: pd.DataFrame, question_col: str = None, answer_col: str = None) -> Dict:
        """데이터를 knowledge_base에 가져오기"""
        try:
            logger.info("데이터 가져오기 시작...")
            
            # 컬럼명 확인
            if not question_col or not answer_col:
                # 자동으로 컬럼 찾기
                columns = df.columns.tolist()
                logger.info(f"사용 가능한 컬럼: {columns}")
                
                # 질문 컬럼 찾기
                question_candidates = ['question', '질문', '요청내용', '제목', 'title']
                question_col = None
                for candidate in question_candidates:
                    if candidate in columns:
                        question_col = candidate
                        break
                
                # 답변 컬럼 찾기
                answer_candidates = ['answer', '답변', '처리내용', '내용', 'content']
                answer_col = None
                for candidate in answer_candidates:
                    if candidate in columns:
                        answer_col = candidate
                        break
                
                if not question_col or not answer_col:
                    raise ValueError(f"질문/답변 컬럼을 찾을 수 없습니다. 사용 가능한 컬럼: {columns}")
            
            logger.info(f"사용할 컬럼: 질문={question_col}, 답변={answer_col}")
            
            # 기존 해시값들 가져오기
            existing_hashes = await self.get_existing_hashes()
            
            # 새 데이터 처리
            new_docs = []
            duplicate_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    question = str(row[question_col]).strip()
                    answer = str(row[answer_col]).strip()
                    
                    if not question or not answer:
                        continue
                    
                    # 중복 체크
                    combined_text = f"{question} {answer}"
                    hash_value = self._generate_hash(combined_text)
                    
                    if hash_value in existing_hashes:
                        duplicate_count += 1
                        continue
                    
                    # 새 문서 생성
                    doc = {
                        "question": question,
                        "answer": answer,
                        "category": "technical",  # 기본값
                        "keywords": self._extract_keywords(question + " " + answer),
                        "created_at": datetime.now(),
                        "updated_at": datetime.now(),
                        "source": "google_sheets_import",
                        "hash": hash_value
                    }
                    
                    new_docs.append(doc)
                    existing_hashes.add(hash_value)  # 중복 방지
                    
                except Exception as e:
                    logger.error(f"행 {index} 처리 중 오류: {str(e)}")
                    error_count += 1
                    continue
            
            logger.info(f"처리 결과:")
            logger.info(f"  - 총 행: {len(df)}")
            logger.info(f"  - 중복 제외: {duplicate_count}")
            logger.info(f"  - 오류: {error_count}")
            logger.info(f"  - 새 데이터: {len(new_docs)}")
            
            # 일괄 삽입
            if new_docs:
                result = await self.knowledge_collection.insert_many(new_docs)
                inserted_count = len(result.inserted_ids)
                logger.info(f"✅ {inserted_count}개 문서가 성공적으로 추가되었습니다.")
            else:
                inserted_count = 0
                logger.info("추가할 새 데이터가 없습니다.")
            
            return {
                "total_rows": len(df),
                "duplicates": duplicate_count,
                "errors": error_count,
                "inserted": inserted_count
            }
            
        except Exception as e:
            logger.error(f"데이터 가져오기 중 오류: {str(e)}")
            raise
    
    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 키워드 추출"""
        # 간단한 키워드 추출 (한글 단어)
        keywords = re.findall(r'[가-힣]{2,}', text)
        
        # 중복 제거 및 상위 10개만 반환
        unique_keywords = list(set(keywords))
        return unique_keywords[:10]

async def main():
    """메인 함수"""
    # MongoDB 연결
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.aicounsel
    
    try:
        importer = GoogleSheetsImporter(db)
        
        # 설정 (필요에 따라 수정)
        sheet_url = "https://docs.google.com/spreadsheets/d/1V1Md1CoauKRIf3HZzUsqNc9nsYX0xvtjqkwMgzPr4tk/edit?gid=1123689008#gid=1123689008"  # 구글 스프레드시트 URL
        sheet_name = None  # 워크시트 이름 (첫 번째 시트 사용)
        csv_fallback = "D:/AICounsel/data/csv/Counseling Training Data_backup.csv"  # CSV 파일 경로 (대안)
        
        # 컬럼명 (필요에 따라 수정)
        question_col = "요청내용"
        answer_col = "처리내용 표준화"
        
        # 데이터 가져오기
        df = importer.get_sheet_data(
            sheet_url=sheet_url,
            sheet_name=sheet_name,
            csv_fallback=csv_fallback
        )
        
        if df is None:
            logger.error("데이터를 가져올 수 없습니다.")
            return
        
        # knowledge_base에 가져오기
        result = await importer.import_data(df, question_col, answer_col)
        
        print(f"\n✅ 가져오기 완료!")
        print(f"   - 총 행: {result['total_rows']}")
        print(f"   - 중복 제외: {result['duplicates']}")
        print(f"   - 오류: {result['errors']}")
        print(f"   - 추가됨: {result['inserted']}")
        
    except Exception as e:
        logger.error(f"실행 중 오류: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main()) 