"""
데이터 전처리 모듈
FAQ 데이터와 대화 데이터를 파인튜닝 형식으로 변환
"""

import pandas as pd
import json
import os
from typing import List, Dict, Any, Tuple
from datasets import Dataset
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    """데이터 전처리 클래스"""
    
    def __init__(self, config):
        self.config = config
        
    def load_faq_data(self, filepath: str) -> pd.DataFrame:
        """FAQ CSV 데이터 로드"""
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
            logger.info(f"FAQ 데이터 로드 완료: {len(df)}개 항목")
            return df
        except Exception as e:
            logger.error(f"FAQ 데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    def load_conversation_data(self, filepath: str) -> List[Dict]:
        """대화 데이터 로드"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"대화 데이터 로드 완료: {len(data)}개 대화")
            return data
        except Exception as e:
            logger.error(f"대화 데이터 로드 실패: {e}")
            return []
    
    def convert_faq_to_finetune_format(self, df: pd.DataFrame) -> List[Dict]:
        """FAQ 데이터를 파인튜닝 형식으로 변환"""
        finetune_data = []
        
        for _, row in df.iterrows():
            # FAQ 데이터 형식: 요청내용, 처리내용 표준화
            if len(row) >= 2:
                request = str(row.iloc[0]).strip()
                response = str(row.iloc[1]).strip()
                
                if request and response and request != "nan" and response != "nan":
                    # 상담사 스타일로 변환
                    instruction = f"고객이 '{request}' 문제를 문의합니다. 어떻게 응답하시겠습니까?"
                    
                    finetune_data.append({
                        "instruction": instruction,
                        "input": request,
                        "output": response
                    })
        
        logger.info(f"FAQ 데이터 변환 완료: {len(finetune_data)}개 항목")
        return finetune_data
    
    def convert_conversation_to_finetune_format(self, conversations: List[Dict]) -> List[Dict]:
        """대화 데이터를 파인튜닝 형식으로 변환"""
        finetune_data = []
        
        for conv in conversations:
            # 대화에서 상담사 응답만 추출
            for i, turn in enumerate(conv.get('turns', [])):
                if turn.get('speaker') == '상담사':
                    # 이전 고객 발화를 컨텍스트로 사용
                    context = ""
                    if i > 0:
                        prev_turn = conv['turns'][i-1]
                        if prev_turn.get('speaker') == '고객':
                            context = prev_turn.get('text', '')
                    
                    instruction = "고객과의 상담 중입니다. 적절한 응답을 해주세요."
                    
                    finetune_data.append({
                        "instruction": instruction,
                        "input": context,
                        "output": turn.get('text', '')
                    })
        
        logger.info(f"대화 데이터 변환 완료: {len(finetune_data)}개 항목")
        return finetune_data
    
    def create_instruction_template(self, data_type: str = "faq") -> str:
        """지시사항 템플릿 생성"""
        
        templates = {
            "faq": """당신은 전문적인 고객 상담사입니다. 고객의 문의에 대해 친근하고 정확한 답변을 제공해주세요.

고객 문의: {input}

상담사 응답:""",
            
            "conversation": """당신은 전문적인 고객 상담사입니다. 고객과의 대화에서 친근하고 도움이 되는 응답을 제공해주세요.

고객: {input}

상담사:""",
            
            "general": """당신은 전문적인 고객 상담사입니다. 고객의 문의에 대해 친근하고 정확한 답변을 제공해주세요.

{instruction}

입력: {input}

응답:"""
        }
        
        return templates.get(data_type, templates["general"])
    
    def format_for_training(self, data: List[Dict], template_type: str = "general") -> List[Dict]:
        """훈련용 형식으로 변환"""
        template = self.create_instruction_template(template_type)
        
        formatted_data = []
        for item in data:
            formatted_text = template.format(
                instruction=item.get("instruction", ""),
                input=item.get("input", ""),
                output=item.get("output", "")
            )
            
            formatted_data.append({
                "text": formatted_text + item.get("output", "")
            })
        
        return formatted_data
    
    def split_data(self, data: List[Dict], train_ratio: float = 0.8, 
                   val_ratio: float = 0.1, test_ratio: float = 0.1) -> Tuple[List, List, List]:
        """데이터 분할"""
        
        total = len(data)
        train_size = int(total * train_ratio)
        val_size = int(total * val_ratio)
        
        train_data = data[:train_size]
        val_data = data[train_size:train_size + val_size]
        test_data = data[train_size + val_size:]
        
        logger.info(f"데이터 분할 완료: 훈련 {len(train_data)}, 검증 {len(val_data)}, 테스트 {len(test_data)}")
        
        return train_data, val_data, test_data
    
    def create_dataset(self, data: List[Dict]) -> Dataset:
        """HuggingFace Dataset 생성"""
        return Dataset.from_list(data)
    
    def save_processed_data(self, data: List[Dict], filepath: str):
        """전처리된 데이터 저장"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"전처리된 데이터 저장 완료: {filepath}")
    
    def process_all_data(self) -> Tuple[Dataset, Dataset, Dataset]:
        """모든 데이터 처리"""
        
        # FAQ 데이터 처리
        faq_df = self.load_faq_data(self.config.data.faq_data_path)
        faq_data = self.convert_faq_to_finetune_format(faq_df)
        
        # 대화 데이터 처리 (있는 경우)
        conversation_data = []
        if os.path.exists(self.config.data.conversation_data_path):
            conv_files = [f for f in os.listdir(self.config.data.conversation_data_path) 
                         if f.endswith('.json')]
            for file in conv_files:
                filepath = os.path.join(self.config.data.conversation_data_path, file)
                conv_data = self.load_conversation_data(filepath)
                conversation_data.extend(self.convert_conversation_to_finetune_format(conv_data))
        
        # 데이터 통합
        all_data = faq_data + conversation_data
        
        # 데이터 분할
        train_data, val_data, test_data = self.split_data(
            all_data, 
            self.config.data.train_ratio,
            self.config.data.val_ratio,
            self.config.data.test_ratio
        )
        
        # 훈련용 형식으로 변환
        train_formatted = self.format_for_training(train_data)
        val_formatted = self.format_for_training(val_data)
        test_formatted = self.format_for_training(test_data)
        
        # Dataset 생성
        train_dataset = self.create_dataset(train_formatted)
        val_dataset = self.create_dataset(val_formatted)
        test_dataset = self.create_dataset(test_formatted)
        
        # 데이터 저장
        output_dir = os.path.join(self.config.finetune.output_dir, "processed_data")
        self.save_processed_data(train_data, os.path.join(output_dir, "train.json"))
        self.save_processed_data(val_data, os.path.join(output_dir, "val.json"))
        self.save_processed_data(test_data, os.path.join(output_dir, "test.json"))
        
        logger.info(f"전체 데이터 처리 완료: 총 {len(all_data)}개 항목")
        
        return train_dataset, val_dataset, test_dataset
    
    def get_data_stats(self, data: List[Dict]) -> Dict[str, Any]:
        """데이터 통계 정보"""
        if not data:
            return {}
        
        # 텍스트 길이 통계
        input_lengths = [len(str(item.get('input', ''))) for item in data]
        output_lengths = [len(str(item.get('output', ''))) for item in data]
        
        stats = {
            "total_samples": len(data),
            "avg_input_length": sum(input_lengths) / len(input_lengths),
            "avg_output_length": sum(output_lengths) / len(output_lengths),
            "max_input_length": max(input_lengths),
            "max_output_length": max(output_lengths),
            "min_input_length": min(input_lengths),
            "min_output_length": min(output_lengths)
        }
        
        return stats 