import csv
import sys
import os
import re

# 가상환경 확인
if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("경고: 가상환경이 활성화되지 않았습니다.")
    print("가상환경을 활성화한 후 다시 실행하세요:")
    print("venv_finetune\\Scripts\\activate")
    sys.exit(1)

print("가상환경이 활성화되어 있습니다. CSV 파일을 수정합니다...")

input_path = "D:/AICounsel/data/csv/Counseling Training Data.csv"
output_path = "D:/AICounsel/data/csv/Counseling_Training_Data_fixed.csv"

def fix_csv_line(line):
    """CSV 라인을 수정하여 쉼표 문제를 해결"""
    # 줄바꿈 문자 제거
    line = line.strip()
    
    # 이미 따옴표로 감싸진 필드가 있는지 확인
    if '"' in line:
        # 이미 따옴표가 있으면 그대로 반환
        return line
    
    # 쉼표로 분할
    parts = line.split(',')
    
    # 각 부분을 따옴표로 감싸기
    quoted_parts = []
    for part in parts:
        part = part.strip()
        if part:  # 빈 문자열이 아닌 경우만
            quoted_parts.append(f'"{part}"')
        else:
            quoted_parts.append('""')
    
    return ','.join(quoted_parts)

try:
    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8", newline="") as outfile:
        
        for line_num, line in enumerate(infile, 1):
            fixed_line = fix_csv_line(line)
            outfile.write(fixed_line + '\n')
            
            # 진행상황 표시
            if line_num % 100 == 0:
                print(f"처리 중... {line_num}줄 완료")

    print("CSV 파일이 자동으로 올바른 형식으로 저장되었습니다:", output_path)
    print("이제 수정된 파일을 사용해서 파인튜닝을 진행하세요.")
    
except Exception as e:
    print(f"오류가 발생했습니다: {e}")
    sys.exit(1) 