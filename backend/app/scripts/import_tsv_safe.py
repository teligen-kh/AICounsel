"""
안전한 TSV 파일 가져오기 (탭 구분 값)
쉼표 문제 완전 해결
"""

import asyncio
import motor.motor_asyncio
from datetime import datetime
import logging
import pandas as pd
from typing import List, Dict, Set
import hashlib
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SafeTSVImporter:
    """안전한 TSV 파일 가져오기 (탭 구분 값)"""
    
    def __init__(self, db):
        self.db = db
        self.knowledge_collection = db.knowledge_base
    
    def load_tsv_safe(self, tsv_file_path: str, encoding: str = 'utf-8') -> pd.DataFrame:
        """안전한 TSV 로드 (탭 구분)"""
        try:
            logger.info(f"안전한 TSV 파일 로드 중: {tsv_file_path}")
            
            # 방법 1: pandas with tab separator
            try:
                df = pd.read_csv(
                    tsv_file_path, 
                    encoding=encoding,
                    sep='\t',  # 탭 구분자
                    on_bad_lines='skip',  # 문제 있는 행 건너뛰기
                    dtype=str  # 모든 컬럼을 문자열로 처리
                )
                logger.info(f"pandas로 TSV 로드 완료: {len(df)}행")
                return df
            except Exception as e:
                logger.warning(f"pandas TSV 로드 실패: {str(e)}")
            
            # 방법 2: 직접 TSV 파싱
            logger.info("직접 TSV 파싱 시도...")
            data = []
            with open(tsv_file_path, 'r', encoding=encoding, newline='') as file:
                for line_num, line in enumerate(file, start=1):
                    try:
                        # 탭으로 분리
                        row = line.strip().split('\t')
                        
                        # 첫 번째 행은 헤더
                        if line_num == 1:
                            headers = row
                            logger.info(f"컬럼명: {headers}")
                            continue
                        
                        # 빈 행 건너뛰기
                        if not line.strip():
                            continue
                        
                        # 행의 셀 수가 헤더와 다르면 건너뛰기
                        if len(row) != len(headers):
                            logger.warning(f"행 {line_num}: 셀 수 불일치 (예상: {len(headers)}, 실제: {len(row)})")
                            continue
                        
                        data.append(row)
                        
                    except Exception as e:
                        logger.warning(f"행 {line_num} 처리 중 오류: {str(e)}")
                        continue
            
            df = pd.DataFrame(data, columns=headers)
            logger.info(f"직접 TSV 파싱 완료: {len(df)}행")
            return df
            
        except Exception as e:
            logger.error(f"TSV 파일 로드 오류: {str(e)}")
            return None
    
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
                        "source": "tsv_safe_import",
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
        importer = SafeTSVImporter(db)
        
        # TSV 파일 경로 (필요에 따라 수정)
        tsv_file_path = "D:/AICounsel/data/csv/knowledge_base_ai_counseling_data.tsv"
        
        # 컬럼명 (필요에 따라 수정)
        question_col = "요청내용"
        answer_col = "처리내용 표준화"
        
        # 안전한 TSV 로드
        df = importer.load_tsv_safe(tsv_file_path)
        
        if df is None:
            logger.error("TSV 파일을 로드할 수 없습니다.")
            return
        
        # knowledge_base에 가져오기
        result = await importer.import_data(df, question_col, answer_col)
        
        print(f"\n✅ 안전한 TSV 가져오기 완료!")
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