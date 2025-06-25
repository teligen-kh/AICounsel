#!/usr/bin/env python3
"""
포맷팅 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.formatting_service import FormattingService

def test_formatting():
    """포맷팅 테스트"""
    print("=" * 60)
    print("포맷팅 테스트")
    print("=" * 60)
    
    # 테스트 응답들
    test_responses = [
        "1. SQL Server Management Studio 실행 2. 데이터베이스 우클릭 3. 속성 선택 4. 파일 그룹에서 공간 증가",
        "프린터 용지 출력 문제와 빨간 불 깜빡임은 다음과 같은 원인들이 있을 수 있어요: 1. 용지 걸림: 프린터 내부에 용지가 걸려있을 수 있습니다. 프린터를 끄고 용지함을 열어서 걸린 용지를 제거해주세요. 2. 용지 부족: 용지함에 용지가 부족하거나 용지가 제대로 들어가지 않았을 수 있습니다. 용지를 다시 넣어주세요. 3. 토너/잉크 부족: 토너나 잉크가 부족하면 빨간 불이 깜빡일 수 있습니다. 교체가 필요합니다.",
        "DB 공간 늘리기: * SQL 실행 * 데이터베이스 선택 * 속성 변경 * 공간 증가",
        "안녕하세요! 무엇을 도와드릴까요?",
        "'포스'에 대해 답변드리겠습니다. 더 자세한 정보가 필요하시면 말씀해 주세요.",
        "알파넷> 상품코드정보관리에서 조회되는지 숨김처리된건 아닌지 숨김처리가 되어있다면 사용으로 저장후 포스 에이전트에서 수신완료후 포스에서 검색여부 확인한다 알파넷에서 조회는 되는데 포스에만 검색이 안된다면 실제상품의 바코드와 알파넷에 입력되어있는 바코드가 동일한지 확인한다 알파넷에서는 있는데 포스에서만 조회가 안된다면 db공간이 없어서수신이 안된경우이다 디비늘리기진행 \"DB늘리기는 2가지 방법이 있습니다.R2의 경우 SQL Server Management Studio >ARUMLLOCADB우클릭 속성>파일> ARUMLOCADB_TABLE 해당파일을 파일 무제한 증가로 설정한다 그외 POSEXPRESS 나 MSDE의경우 설치폴더안에 SqlManagerTool 에서 설치되어있는 폴더명으로 변경후 해당 쿼리 저장한다> ALTER DATABASE ARUMLOCADB ADD FILE ( NAME = ARUMLOCADB_TABLE_11, FILENAME = 'D:\\AlphaNetPOS\\DataFiles\\ARUMLOCADB_TABLE_11.ndf', SIZE = 10MB, MAXSIZE = 1000MB, FILEGROWTH = 100MB ) TO FILEGROUP ARUMLOCADB_TABLE ;\""
    ]
    
    for i, response in enumerate(test_responses, 1):
        print(f"\n테스트 {i}:")
        print(f"원본: {response}")
        formatted = FormattingService.format_response(response)
        print(f"포맷팅: {formatted}")
        print("-" * 40)

if __name__ == "__main__":
    test_formatting() 