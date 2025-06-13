import pandas as pd
from pymongo import MongoClient
from collections import Counter
import matplotlib.pyplot as plt
from datetime import datetime
import seaborn as sns
from typing import List, Dict
import logging
import os
import re

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('conversation_analysis.log'),
        logging.StreamHandler()
    ]
)

class ConversationAnalyzer:
    def __init__(self, mongo_uri="mongodb://localhost:27017", db_name="aicounsel"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db['conversations']
        
    def get_basic_stats(self) -> Dict:
        """기본 통계 정보 수집"""
        total_conversations = self.collection.count_documents({})
        
        # 메시지 수 계산
        total_messages = 0
        role_stats = Counter()
        for doc in self.collection.find():
            if 'messages' in doc:
                messages = doc['messages']
                total_messages += len(messages)
                for message in messages:
                    if 'role' in message:
                        role_stats[message['role']] += 1
        
        # 대화 길이 통계
        conversation_lengths = []
        for doc in self.collection.find():
            if 'messages' in doc:
                conversation_lengths.append(len(doc['messages']))
        
        avg_length = sum(conversation_lengths) / len(conversation_lengths) if conversation_lengths else 0
        
        return {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'role_stats': dict(role_stats),
            'avg_conversation_length': avg_length,
            'min_conversation_length': min(conversation_lengths) if conversation_lengths else 0,
            'max_conversation_length': max(conversation_lengths) if conversation_lengths else 0
        }
    
    def analyze_keywords(self, top_n: int = 20) -> Dict[str, int]:
        """자주 사용되는 키워드 분석"""
        # 모든 메시지 내용 수집
        all_contents = []
        for doc in self.collection.find():
            if 'messages' in doc:
                for message in doc['messages']:
                    if 'content' in message:
                        all_contents.append(message['content'])
        
        # 간단한 단어 추출 (2글자 이상의 연속된 한글)
        words = []
        for content in all_contents:
            # 한글 단어 추출 (2글자 이상)
            korean_words = re.findall(r'[가-힣]{2,}', content)
            words.extend(korean_words)
        
        # 불용어 제거 (필요시 수정)
        stopwords = {'이', '그', '저', '것', '수', '등', '및', '또', '더', '많', '적', '잘', '못'}
        filtered_words = [word for word in words if word not in stopwords]
        
        return dict(Counter(filtered_words).most_common(top_n))
    
    def analyze_conversation_patterns(self) -> Dict:
        """대화 패턴 분석"""
        patterns = {
            'user_first': 0,  # 사용자가 먼저 말한 대화
            'assistant_first': 0,  # 어시스턴트가 먼저 말한 대화
            'avg_turn_length': 0,  # 평균 턴 길이
            'max_turn_length': 0,  # 최대 턴 길이
        }
        
        total_turns = 0
        total_turn_length = 0
        
        for doc in self.collection.find():
            if 'messages' in doc and doc['messages']:
                messages = doc['messages']
                # 첫 발화자 확인
                if messages[0]['role'] == 'user':
                    patterns['user_first'] += 1
                else:
                    patterns['assistant_first'] += 1
                
                # 턴 길이 계산
                current_role = messages[0]['role']
                turn_length = 1
                
                for msg in messages[1:]:
                    if msg['role'] == current_role:
                        turn_length += 1
                    else:
                        total_turns += 1
                        total_turn_length += turn_length
                        patterns['max_turn_length'] = max(patterns['max_turn_length'], turn_length)
                        current_role = msg['role']
                        turn_length = 1
                
                # 마지막 턴 처리
                total_turns += 1
                total_turn_length += turn_length
                patterns['max_turn_length'] = max(patterns['max_turn_length'], turn_length)
        
        if total_turns > 0:
            patterns['avg_turn_length'] = total_turn_length / total_turns
        
        return patterns
    
    def generate_report(self, output_dir: str = "analysis_results"):
        """분석 결과 리포트 생성"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 기본 통계
        stats = self.get_basic_stats()
        logging.info("기본 통계:")
        logging.info(f"총 대화 수: {stats['total_conversations']}")
        logging.info(f"총 메시지 수: {stats['total_messages']}")
        logging.info(f"역할별 통계: {stats['role_stats']}")
        logging.info(f"평균 대화 길이: {stats['avg_conversation_length']:.2f}")
        
        # 대화 패턴 분석
        patterns = self.analyze_conversation_patterns()
        logging.info("\n대화 패턴 분석:")
        logging.info(f"사용자 첫 발화 대화: {patterns['user_first']}")
        logging.info(f"어시스턴트 첫 발화 대화: {patterns['assistant_first']}")
        logging.info(f"평균 턴 길이: {patterns['avg_turn_length']:.2f}")
        logging.info(f"최대 턴 길이: {patterns['max_turn_length']}")
        
        # 키워드 분석
        keywords = self.analyze_keywords()
        logging.info("\n자주 사용된 키워드:")
        for word, count in keywords.items():
            logging.info(f"{word}: {count}")
        
        # 시각화
        plt.figure(figsize=(15, 15))
        
        # 역할별 통계 그래프
        plt.subplot(3, 1, 1)
        roles = list(stats['role_stats'].keys())
        counts = list(stats['role_stats'].values())
        plt.bar(roles, counts)
        plt.title('역할별 메시지 수')
        plt.xlabel('역할')
        plt.ylabel('메시지 수')
        
        # 대화 패턴 그래프
        plt.subplot(3, 1, 2)
        pattern_labels = ['사용자 첫 발화', '어시스턴트 첫 발화']
        pattern_values = [patterns['user_first'], patterns['assistant_first']]
        plt.bar(pattern_labels, pattern_values)
        plt.title('첫 발화자 통계')
        plt.ylabel('대화 수')
        
        # 키워드 분석 그래프
        plt.subplot(3, 1, 3)
        words = list(keywords.keys())
        counts = list(keywords.values())
        plt.barh(words, counts)
        plt.title('자주 사용된 키워드')
        plt.xlabel('사용 빈도')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'conversation_analysis.png'))
        
        # 결과를 CSV로 저장
        pd.DataFrame({
            'metric': ['총 대화 수', '총 메시지 수', '평균 대화 길이', 
                      '사용자 첫 발화', '어시스턴트 첫 발화', 
                      '평균 턴 길이', '최대 턴 길이'],
            'value': [stats['total_conversations'], stats['total_messages'], 
                     stats['avg_conversation_length'],
                     patterns['user_first'], patterns['assistant_first'],
                     patterns['avg_turn_length'], patterns['max_turn_length']]
        }).to_csv(os.path.join(output_dir, 'basic_stats.csv'), index=False)
        
        pd.DataFrame({
            'keyword': list(keywords.keys()),
            'count': list(keywords.values())
        }).to_csv(os.path.join(output_dir, 'keywords.csv'), index=False)
        
    def close(self):
        """MongoDB 연결 종료"""
        self.client.close()

def main():
    analyzer = ConversationAnalyzer()
    try:
        analyzer.generate_report()
    finally:
        analyzer.close()

if __name__ == "__main__":
    main() 