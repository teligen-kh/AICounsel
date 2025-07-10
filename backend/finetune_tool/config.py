"""
파인튜닝 도구 설정 파일
로컬 GPU와 클라우드 GPU 환경을 모두 지원
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class FinetuneConfig:
    """파인튜닝 기본 설정"""
    
    # 모델 설정
    model_name: str = "microsoft/Phi-3.5-mini"
    model_type: str = "phi"  # phi, llama, mistral 등
    
    # LoRA 설정
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: list = None
    
    # 학습 설정
    num_epochs: int = 3
    learning_rate: float = 2e-4
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    max_seq_length: int = 512
    
    # 양자화 설정 (GTX 1050 Ti용)
    use_4bit: bool = True
    use_8bit: bool = False
    
    # 출력 설정
    output_dir: str = "./finetuned_models"
    save_steps: int = 500
    eval_steps: int = 500
    logging_steps: int = 10
    
    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = ["q_proj", "v_proj"]

@dataclass
class CloudConfig:
    """클라우드 GPU 설정 (향후 사용)"""
    
    # 클라우드 제공업체
    provider: str = "local"  # local, aws, gcp, azure
    
    # AWS 설정
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    aws_region: str = "us-east-1"
    aws_instance_type: str = "g4dn.xlarge"
    
    # GCP 설정
    gcp_project_id: Optional[str] = None
    gcp_zone: str = "us-central1-a"
    gcp_machine_type: str = "n1-standard-4"
    gcp_accelerator_type: str = "nvidia-tesla-t4"
    
    # Azure 설정
    azure_subscription_id: Optional[str] = None
    azure_resource_group: Optional[str] = None
    azure_location: str = "eastus"
    azure_vm_size: str = "Standard_NC4as_T4_v3"
    
    # 스토리지 설정
    storage_bucket: Optional[str] = None
    storage_path: str = "models/"

@dataclass
class DataConfig:
    """데이터 설정"""
    
    # 데이터 경로
    faq_data_path: str = "../data/csv/Counseling Training Data.csv"
    conversation_data_path: str = "../data/conversations/"
    
    # 데이터 분할
    train_ratio: float = 0.8
    val_ratio: float = 0.1
    test_ratio: float = 0.1
    
    # 데이터 형식
    input_format: str = "csv"  # csv, json, txt
    output_format: str = "json"  # json, parquet

class ConfigManager:
    """설정 관리자"""
    
    def __init__(self):
        self.finetune = FinetuneConfig()
        self.cloud = CloudConfig()
        self.data = DataConfig()
    
    def get_model_config(self, model_type: str = "phi") -> Dict[str, Any]:
        """모델별 설정 반환"""
        
        configs = {
            "phi": {
                "model_name": "microsoft/Phi-3.5-mini",
                "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
                "max_seq_length": 512
            },
            "llama": {
                "model_name": "meta-llama/Llama-2-7b-chat-hf",
                "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
                "max_seq_length": 1024
            },
            "mistral": {
                "model_name": "mistralai/Mistral-7B-Instruct-v0.2",
                "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
                "max_seq_length": 1024
            }
        }
        
        return configs.get(model_type, configs["phi"])
    
    def get_hardware_config(self, gpu_memory: int) -> Dict[str, Any]:
        """하드웨어별 설정 반환"""
        
        if gpu_memory >= 24:  # RTX 4090, A100 등
            return {
                "batch_size": 8,
                "use_4bit": False,
                "gradient_accumulation_steps": 2
            }
        elif gpu_memory >= 12:  # RTX 3080, 4080 등
            return {
                "batch_size": 4,
                "use_4bit": False,
                "gradient_accumulation_steps": 4
            }
        elif gpu_memory >= 8:  # RTX 3070, 4060 등
            return {
                "batch_size": 2,
                "use_4bit": True,
                "gradient_accumulation_steps": 8
            }
        else:  # GTX 1050 Ti, 1060 등
            return {
                "batch_size": 1,
                "use_4bit": True,
                "gradient_accumulation_steps": 16
            }
    
    def save_config(self, filepath: str):
        """설정을 파일로 저장"""
        import json
        
        config_dict = {
            "finetune": self.finetune.__dict__,
            "cloud": self.cloud.__dict__,
            "data": self.data.__dict__
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
    
    def load_config(self, filepath: str):
        """파일에서 설정 로드"""
        import json
        
        with open(filepath, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        self.finetune = FinetuneConfig(**config_dict.get("finetune", {}))
        self.cloud = CloudConfig(**config_dict.get("cloud", {}))
        self.data = DataConfig(**config_dict.get("data", {}))

# 전역 설정 인스턴스
config_manager = ConfigManager() 