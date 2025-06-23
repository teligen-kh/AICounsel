import pandas as pd
import os
from pathlib import Path

def check_csv_structure():
    """CSV 파일들의 구조를 확인합니다."""
    
    # CSV 파일 경로 (backend 폴더에서 상대 경로)
    csv_dir = Path("../../data/csv")
    
    # 절대 경로로도 시도
    if not csv_dir.exists():
        csv_dir = Path("D:/AICounsel/data/csv")
    
    if not csv_dir.exists():
        print(f"CSV 디렉토리가 존재하지 않습니다: {csv_dir}")
        print("현재 작업 디렉토리:", os.getcwd())
        return
    
    # 모든 CSV 파일 찾기
    csv_files = list(csv_dir.glob("*.csv"))
    
    if not csv_files:
        print("CSV 파일이 없습니다.")
        return
    
    print(f"발견된 CSV 파일 수: {len(csv_files)}")
    print("=" * 50)
    
    for csv_file in csv_files:
        print(f"\n파일명: {csv_file.name}")
        print("-" * 30)
        
        try:
            # CSV 파일 읽기
            df = pd.read_csv(csv_file, encoding='utf-8')
            
            # 기본 정보 출력
            print(f"행 수: {len(df)}")
            print(f"열 수: {len(df.columns)}")
            print(f"컬럼명: {list(df.columns)}")
            
            # 데이터 타입 확인
            print(f"데이터 타입:")
            for col, dtype in df.dtypes.items():
                print(f"  {col}: {dtype}")
            
            # 처음 3행 미리보기
            print(f"\n처음 3행 미리보기:")
            print(df.head(3).to_string())
            
            # 각 컬럼의 고유값 개수 (카테고리형 데이터 확인)
            print(f"\n각 컬럼의 고유값 개수:")
            for col in df.columns:
                unique_count = df[col].nunique()
                print(f"  {col}: {unique_count}개")
                if unique_count <= 10:  # 고유값이 적으면 샘플 출력
                    print(f"    샘플: {list(df[col].unique())}")
            
        except Exception as e:
            print(f"파일 읽기 오류: {str(e)}")
        
        print("\n" + "=" * 50)

if __name__ == "__main__":
    check_csv_structure() 