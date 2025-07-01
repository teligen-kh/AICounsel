from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
import logging
import time
from typing import Dict, Optional, Tuple
from enum import Enum

class ModelType(Enum):
    """사용 가능한 모델 타입"""
    LLAMA_3_1_8B = "llama-3.1-8b"
    POLYGLOT_KO_5_8B = "polyglot-ko-5.8b"

class ModelConfig:
    """모델별 설정"""
    def __init__(self, name: str, path: str, max_tokens: int = 20, temperature: float = 0.3):
        self.name = name
        self.path = path
        self.max_tokens = max_tokens
        self.temperature = temperature

class ModelManager:
    """여러 LLM 모델을 관리하는 매니저"""
    
    def __init__(self):
        self.models: Dict[str, Tuple[AutoModelForCausalLM, AutoTokenizer]] = {}
        self.current_model: Optional[str] = None
        self.model_configs = {
            ModelType.LLAMA_3_1_8B.value: ModelConfig(
                "Llama-3.1-8B-Instruct",
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                           "models", "Llama-3.1-8B-Instruct"),
                max_tokens=20,
                temperature=0.3
            ),
            ModelType.POLYGLOT_KO_5_8B.value: ModelConfig(
                "Polyglot-Ko-5.8B",
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                           "models", "Polyglot-Ko-5.8B"),
                max_tokens=30,  # 한국어 모델이므로 조금 더 긴 응답
                temperature=0.4
            )
        }
    
    def get_model_path(self, model_type: str) -> str:
        """모델 경로를 반환합니다."""
        if model_type in self.model_configs:
            return self.model_configs[model_type].path
        raise ValueError(f"Unknown model type: {model_type}")
    
    def load_model(self, model_type: str) -> bool:
        """지정된 모델을 로딩합니다."""
        try:
            if model_type in self.models:
                logging.info(f"Model {model_type} already loaded")
                return True
            
            if model_type not in self.model_configs:
                logging.error(f"Unknown model type: {model_type}")
                return False
            
            config = self.model_configs[model_type]
            model_path = config.path
            
            if not os.path.exists(model_path):
                logging.error(f"Model path does not exist: {model_path}")
                return False
            
            logging.info(f"Loading model: {model_type} from {model_path}")
            
            # 토크나이저 로딩
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # 모델 로딩
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            # 모델 저장
            self.models[model_type] = (model, tokenizer)
            self.current_model = model_type
            
            logging.info(f"✅ Model {model_type} loaded successfully!")
            return True
            
        except Exception as e:
            logging.error(f"Failed to load model {model_type}: {str(e)}")
            return False
    
    def unload_model(self, model_type: str) -> bool:
        """지정된 모델을 언로딩합니다."""
        try:
            if model_type in self.models:
                model, tokenizer = self.models[model_type]
                
                # GPU 메모리 해제
                del model
                del tokenizer
                
                # 모델 제거
                del self.models[model_type]
                
                # 현재 모델이 언로딩된 모델이면 None으로 설정
                if self.current_model == model_type:
                    self.current_model = None
                
                logging.info(f"✅ Model {model_type} unloaded successfully!")
                return True
            else:
                logging.warning(f"Model {model_type} is not loaded")
                return False
                
        except Exception as e:
            logging.error(f"Failed to unload model {model_type}: {str(e)}")
            return False
    
    def switch_model(self, model_type: str) -> bool:
        """현재 모델을 다른 모델로 전환합니다."""
        try:
            # 새 모델 로딩
            if not self.load_model(model_type):
                return False
            
            # 이전 모델 언로딩 (메모리 절약)
            if self.current_model and self.current_model != model_type:
                self.unload_model(self.current_model)
            
            self.current_model = model_type
            logging.info(f"✅ Switched to model: {model_type}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to switch to model {model_type}: {str(e)}")
            return False
    
    def get_current_model(self) -> Optional[Tuple[AutoModelForCausalLM, AutoTokenizer]]:
        """현재 로딩된 모델을 반환합니다."""
        if self.current_model and self.current_model in self.models:
            return self.models[self.current_model]
        return None
    
    def get_current_model_config(self) -> Optional[ModelConfig]:
        """현재 모델의 설정을 반환합니다."""
        if self.current_model and self.current_model in self.model_configs:
            return self.model_configs[self.current_model]
        return None
    
    def is_model_loaded(self, model_type: str) -> bool:
        """지정된 모델이 로딩되어 있는지 확인합니다."""
        return model_type in self.models
    
    def get_loaded_models(self) -> list:
        """로딩된 모델 목록을 반환합니다."""
        return list(self.models.keys())
    
    def get_available_models(self) -> list:
        """사용 가능한 모델 목록을 반환합니다."""
        return list(self.model_configs.keys())

# 전역 모델 매니저 인스턴스
model_manager = ModelManager()

def get_model_manager() -> ModelManager:
    """전역 모델 매니저 인스턴스를 반환합니다."""
    return model_manager 