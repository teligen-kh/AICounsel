import re
import logging
from typing import Optional

class FormattingService:
    """응답 포맷팅을 담당하는 독립적인 서비스"""
    
    @staticmethod
    def format_response(response: str) -> str:
        """응답을 포맷팅합니다."""
        if not response:
            return response
            
        # 기본 정리
        response = response.strip()
        
        # 줄바꿈 개선
        response = response.replace('\\n', '\n')
        
        # 번호 매기기 개선 (더 정확한 패턴 매칭)
        response = re.sub(r'(\d+)\.\s+', r'\n\1. ', response)
        
        # 불릿 포인트 개선
        response = re.sub(r'\*\s+', r'\n• ', response)
        response = re.sub(r'•\s+', r'\n• ', response)
        
        # 대시 개선
        response = re.sub(r'-\s+', r'\n- ', response)
        
        # 화살표 개선
        response = re.sub(r'→\s+', r'\n→ ', response)
        
        # 문장 끝 개선 (너무 과도하지 않게)
        response = re.sub(r'\.\s+([A-Z가-힣])', r'.\n\1', response)
        response = re.sub(r'\?\s+([A-Z가-힣])', r'?\n\1', response)
        response = re.sub(r'!\s+([A-Z가-힣])', r'!\n\1', response)

        # 한글 동사로 끝나는 문장 뒤에 줄바꿈 추가 (test_formatting.py에서 검증된 패턴)
        response = re.sub(r'(다|는다|있다|없다|한다면|됩니다|있습니다|않습니다|드립니다|니다|습니다|요)\s+([가-힣A-Za-z0-9])', r'\1\n\2', response)
        
        # 연속된 공백을 줄바꿈으로 (2개 이상)
        response = re.sub(r'\s{2,}', '\n', response)
        
        # 긴 문장 줄바꿈 개선 (100자 이상의 문장을 적절히 분할)
        lines = response.split('\n')
        formatted_lines = []
        
        for line in lines:
            if len(line) > 100:  # 100자 이상인 경우
                # 문장 단위로 분할
                sentences = re.split(r'(?<=[.!?])\s+', line)
                current_line = ""
                
                for sentence in sentences:
                    if len(current_line + sentence) > 100:
                        if current_line:
                            formatted_lines.append(current_line.strip())
                            current_line = sentence
                        else:
                            # 한 문장이 100자 이상인 경우 강제로 분할
                            words = sentence.split()
                            temp_line = ""
                            for word in words:
                                if len(temp_line + word) > 80:
                                    if temp_line:
                                        formatted_lines.append(temp_line.strip())
                                        temp_line = word
                                    else:
                                        formatted_lines.append(word)
                                else:
                                    temp_line += " " + word if temp_line else word
                            if temp_line:
                                current_line = temp_line
                    else:
                        current_line += " " + sentence if current_line else sentence
                
                if current_line:
                    formatted_lines.append(current_line.strip())
            else:
                formatted_lines.append(line)
        
        response = '\n'.join(formatted_lines)
        
        # 특정 키워드에서 줄바꿈 추가
        keywords_to_break = [
            '알파넷>', '디비늘리기진행', 'R2의 경우', '그외', '> ALTER DATABASE',
            'SQL Server Management Studio', 'POSEXPRESS', 'MSDE의경우'
        ]
        
        for keyword in keywords_to_break:
            response = response.replace(keyword, f'\n{keyword}')
        
        # 응답 길이 제한 (문자 수 기준)
        if len(response) > 800:
            response = response[:800] + "..."
        
        # 줄 정리 (빈 줄 제거, 앞뒤 공백 제거)
        lines = []
        for line in response.split('\n'):
            line = line.strip()
            if line:  # 빈 줄이 아닌 경우만 추가
                lines.append(line)
        
        response = '\n'.join(lines)
        
        # 첫 줄이 번호나 불릿로 시작하지 않으면 개행 추가
        if response and not re.match(r'^[\d•\-→]', response):
            response = '\n' + response
        
        return response
    
    @staticmethod
    def format_db_answer(db_answer: str) -> str:
        """DB 답변을 간단히 정리하여 반환합니다."""
        try:
            if not db_answer:
                return db_answer
                
            # 기본 정리
            response = db_answer.strip()
            
            # 줄바꿈 개선 - 사용자 입력의 줄바꿈을 보존
            response = response.replace('\\n', '\n')
            
            # 연속된 공백을 줄바꿈으로 (2개 이상)
            response = re.sub(r'\s{2,}', '\n', response)
            
            # 특정 키워드에서 줄바꿈 추가
            keywords_to_break = [
                '알파넷>', '디비늘리기진행', 'R2의 경우', '그외', '> ALTER DATABASE',
                'SQL Server Management Studio', 'POSEXPRESS', 'MSDE의경우'
            ]
            
            for keyword in keywords_to_break:
                response = response.replace(keyword, f'\n{keyword}')
            
            # 응답 길이 제한 (문자 수 기준)
            if len(response) > 800:
                response = response[:800] + "..."
            
            # 줄 정리 (빈 줄 제거, 앞뒤 공백 제거)
            lines = []
            for line in response.split('\n'):
                line = line.strip()
                if line:  # 빈 줄이 아닌 경우만 추가
                    lines.append(line)
            
            response = '\n'.join(lines)
            
            return response
            
        except Exception as e:
            logging.error(f"Error formatting DB answer: {str(e)}")
            return db_answer 