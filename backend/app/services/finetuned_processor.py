import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel, PeftConfig
import logging
from typing import Optional

class FinetunedProcessor:
    def __init__(self, base_model_path: str, adapter_path: str):
        """
        파인튜닝된 모델 프로세서 초기화
        
        Args:
            base_model_path: 기본 모델 경로
            adapter_path: LoRA 어댑터 경로
        """
        self.base_model_path = base_model_path
        self.adapter_path = adapter_path
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logging.info(f"FinetunedProcessor 초기화: base_model={base_model_path}, adapter={adapter_path}")
        self._load_model()
    
    def _load_model(self):
        """모델과 토크나이저를 로드합니다."""
        try:
            logging.info("파인튜닝된 모델 로딩 시작...")
            
            # CPU 환경에서는 4비트 양자화를 사용하지 않음
            if torch.cuda.is_available():
                # GPU 환경: 4비트 양자화 설정
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.bfloat16
                )
                quantization_config = bnb_config
                torch_dtype = torch.bfloat16
            else:
                # CPU 환경: 일반 설정
                quantization_config = None
                torch_dtype = torch.float32
                logging.info("CPU 환경에서 일반 모드로 로딩합니다.")
            
            # 기본 모델 로드
            logging.info(f"기본 모델 로딩: {self.base_model_path}")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.base_model_path,
                quantization_config=quantization_config,
                device_map="auto" if torch.cuda.is_available() else None,
                torch_dtype=torch_dtype,
                trust_remote_code=True
            )
            
            # LoRA 어댑터 로드
            logging.info(f"LoRA 어댑터 로딩: {self.adapter_path}")
            self.model = PeftModel.from_pretrained(self.model, self.adapter_path)
            
            # 토크나이저 로드
            logging.info("토크나이저 로딩...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.base_model_path,
                trust_remote_code=True
            )
            
            # 패딩 토큰 설정
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logging.info("✅ 파인튜닝된 모델 로딩 완료")
            
        except Exception as e:
            logging.error(f"파인튜닝된 모델 로딩 실패: {str(e)}")
            raise
    
    def generate_response(self, prompt: str, max_length: int = 512, temperature: float = 0.7) -> str:
        """
        파인튜닝된 모델로 응답 생성
        
        Args:
            prompt: 입력 프롬프트
            max_length: 최대 토큰 길이
            temperature: 생성 온도
            
        Returns:
            str: 생성된 응답
        """
        try:
            if self.model is None or self.tokenizer is None:
                raise ValueError("모델이 로드되지 않았습니다.")
            
            # 입력 인코딩
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=max_length,
                padding=True
            ).to(self.device)
            
            # 생성 설정 (간단한 버전)
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=min(max_length, 256),
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # 응답 디코딩
            response = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            )
            
            return response.strip()
            
        except Exception as e:
            logging.error(f"응답 생성 중 오류: {str(e)}")
            return "죄송합니다. 응답 생성 중 오류가 발생했습니다."
    
    def cleanup(self):
        """리소스 정리"""
        if self.model is not None:
            del self.model
        if self.tokenizer is not None:
            del self.tokenizer
        torch.cuda.empty_cache()
        logging.info("파인튜닝된 모델 리소스 정리 완료")

# 싱글톤 인스턴스
_finetuned_processor: Optional[FinetunedProcessor] = None

def get_finetuned_processor() -> FinetunedProcessor:
    """파인튜닝된 모델 프로세서 싱글톤 인스턴스 반환"""
    global _finetuned_processor
    
    if _finetuned_processor is None:
        # 경로 설정
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        base_model_path = os.path.join(base_path, "backend", "finetune_tool", "models", "microsoft", "Phi-3.5-mini-instruct")
        adapter_path = os.path.join(base_path, "backend", "finetune_tool", "finetuned_models")
        
        _finetuned_processor = FinetunedProcessor(base_model_path, adapter_path)
    
    return _finetuned_processor 