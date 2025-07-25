"""
TSV 파일 구조 디버그 스크립트
"""

def debug_tsv_structure(file_path: str):
    """TSV 파일 구조 확인"""
    print(f"TSV 파일 구조 확인: {file_path}")
    print("=" * 50)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # 첫 10행 확인
            for i, line in enumerate(file, 1):
                if i > 10:
                    break
                
                print(f"행 {i}: {repr(line.strip())}")
                
                # 탭으로 분리
                parts = line.strip().split('\t')
                print(f"  탭 분리 결과: {len(parts)}개 셀")
                for j, part in enumerate(parts):
                    print(f"    셀 {j}: {repr(part)}")
                print()
                
    except Exception as e:
        print(f"오류: {str(e)}")

if __name__ == "__main__":
    file_path = "D:/AICounsel/data/csv/knowledge_base_ai_counseling_data.tsv"
    debug_tsv_structure(file_path) 