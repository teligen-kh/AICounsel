from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
import logging
import time
import psutil
from typing import Dict, Optional, Tuple
from enum import Enum

class ModelType(Enum):
    """사용 가능한 모델 타입"""
    LLAMA_2_7B_CHAT = "llama-2-7b-chat"

class ModelConfig:
    """모델별 설정"""
    def __init__(self, name: str, path: str, max_tokens: int = 50, temperature: float = 0.6):
        self.name = name
        self.path = path
        self.max_tokens = max_tokens
        self.temperature = temperature

class ModelManager:
    """LLaMA 2 7B Chat 모델을 관리하는 매니저"""
    
    def __init__(self):
        self.models: Dict[str, Tuple[AutoModelForCausalLM, AutoTokenizer]] = {}
        self.current_model: Optional[str] = None
        self.model_configs = {
            ModelType.LLAMA_2_7B_CHAT.value: ModelConfig(
                "Llama-2-7B-Chat",
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                           "models", "llama-2-7b-chat.Q4_K_M.gguf"),
                max_tokens=50,
                temperature=0.6
            )
        }
        
        # 성능 모니터링 데이터
        self.performance_stats = {
            'model_load_times': {},
            'memory_usage': {},
            'gpu_usage': {},
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0,
            'response_times': []
        }
    
    def log_system_metrics(self, stage: str, model_type: str = None):
        """시스템 메트릭 로깅"""
        try:
            # CPU 및 메모리 정보
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # GPU 정보
            gpu_info = "N/A"
            if torch.cuda.is_available():
                gpu_memory_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
                gpu_memory_reserved = torch.cuda.memory_reserved() / 1024**3  # GB
                gpu_info = f"Allocated: {gpu_memory_allocated:.2f}GB, Reserved: {gpu_memory_reserved:.2f}GB"
            
            logging.info(f"=== 시스템 메트릭 ({stage}) ===")
            if model_type:
                logging.info(f"모델: {model_type}")
            logging.info(f"CPU 사용률: {cpu_percent:.1f}%")
            logging.info(f"메모리 사용률: {memory.percent:.1f}% ({memory.used/1024**3:.1f}GB/{memory.total/1024**3:.1f}GB)")
            logging.info(f"GPU 메모리: {gpu_info}")
            logging.info(f"================================")
            
        except Exception as e:
            logging.warning(f"시스템 메트릭 로깅 실패: {str(e)}")
    
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
            
            # 로딩 시작 전 시스템 메트릭
            self.log_system_metrics("모델 로딩 시작", model_type)
            load_start_time = time.time()
            
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
            
            # 로딩 완료 후 시스템 메트릭
            load_end_time = time.time()
            load_time = (load_end_time - load_start_time) * 1000  # ms
            
            self.performance_stats['model_load_times'][model_type] = load_time
            self.log_system_metrics("모델 로딩 완료", model_type)
            
            # 모델 저장
            self.models[model_type] = (model, tokenizer)
            self.current_model = model_type
            
            logging.info(f"✅ Model {model_type} loaded successfully in {load_time:.2f}ms!")
            return True
            
        except Exception as e:
            logging.error(f"Failed to load model {model_type}: {str(e)}")
            return False
    
    def unload_model(self, model_type: str) -> bool:
        """지정된 모델을 언로딩합니다."""
        try:
            if model_type in self.models:
                # 언로딩 시작 전 시스템 메트릭
                self.log_system_metrics("모델 언로딩 시작", model_type)
                
                model, tokenizer = self.models[model_type]
                
                # GPU 메모리 해제
                del model
                del tokenizer
                
                # 모델 제거
                del self.models[model_type]
                
                # 현재 모델이 언로딩된 모델이면 None으로 설정
                if self.current_model == model_type:
                    self.current_model = None
                
                # 언로딩 완료 후 시스템 메트릭
                self.log_system_metrics("모델 언로딩 완료")
                
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
            
            # 전역 서비스 인스턴스들 업데이트
            try:
                from ..dependencies import get_llm_service, get_chat_service
                llm_service = get_llm_service()
                if llm_service:
                    llm_service.model_type = model_type
                    logging.info(f"Updated global LLM service model type to: {model_type}")
            except Exception as e:
                logging.warning(f"Failed to update global services: {str(e)}")
            
            logging.info(f"✅ Switched to model: {model_type}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to switch model: {str(e)}")
            return False
    
    def get_current_model(self) -> Optional[Tuple[AutoModelForCausalLM, AutoTokenizer]]:
        """현재 로드된 모델을 반환합니다."""
        if self.current_model and self.current_model in self.models:
            return self.models[self.current_model]
        return None
    
    def get_current_model_config(self) -> Optional[ModelConfig]:
        """현재 모델 설정을 반환합니다."""
        if self.current_model and self.current_model in self.model_configs:
            return self.model_configs[self.current_model]
        return None
    
    def is_model_loaded(self, model_type: str) -> bool:
        """모델이 로드되었는지 확인합니다."""
        return model_type in self.models
    
    def get_loaded_models(self) -> list:
        """로드된 모델 목록을 반환합니다."""
        return list(self.models.keys())
    
    def get_available_models(self) -> list:
        """사용 가능한 모델 목록을 반환합니다."""
        return list(self.model_configs.keys())
    
    def get_performance_stats(self) -> Dict:
        """성능 통계를 반환합니다."""
        stats = self.performance_stats.copy()
        
        # 평균 응답 시간 계산
        if stats['response_times']:
            stats['avg_response_time'] = sum(stats['response_times']) / len(stats['response_times'])
        
        return stats
    
    def log_performance_summary(self):
        """성능 요약을 로깅합니다."""
        stats = self.get_performance_stats()
        
        logging.info("=== 모델 매니저 성능 요약 ===")
        logging.info(f"총 요청 수: {stats['total_requests']}")
        logging.info(f"성공 요청 수: {stats['successful_requests']}")
        logging.info(f"실패 요청 수: {stats['failed_requests']}")
        logging.info(f"평균 응답 시간: {stats['avg_response_time']:.2f}ms")
        logging.info(f"최소 처리 시간: {stats.get('min_processing_time', 0):.2f}ms")
        logging.info(f"최대 처리 시간: {stats.get('max_processing_time', 0):.2f}ms")
        logging.info(f"로드된 모델: {self.get_loaded_models()}")
        logging.info(f"현재 모델: {self.current_model}")
        logging.info("================================")

# 전역 모델 매니저 인스턴스
_model_manager: Optional[ModelManager] = None

def get_model_manager() -> ModelManager:
    """전역 모델 매니저 인스턴스를 반환합니다."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager 