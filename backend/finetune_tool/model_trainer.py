"""
모델 파인튜닝 학습 모듈
LoRA/QLoRA를 사용한 효율적인 파인튜닝
"""

import torch
import os
import json
import logging
from typing import Dict, Any, Optional
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    TrainingArguments, 
    Trainer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset
import wandb
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelTrainer:
    """모델 파인튜닝 클래스"""
    
    def __init__(self, config):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.trainer = None
        
    def setup_model_and_tokenizer(self):
        """모델과 토크나이저 설정"""
        
        logger.info(f"모델 로드 중: {self.config.finetune.model_name}")
        
        # GGUF 모델인지 확인
        if hasattr(self.config.finetune, 'use_gguf') and self.config.finetune.use_gguf:
            logger.info("GGUF 모델 로드 중...")
            self._load_gguf_model()
        else:
            logger.info("Hugging Face 모델 로드 중...")
            self._load_hf_model()
        
        logger.info("모델과 토크나이저 로드 완료")
    
    def _load_gguf_model(self):
        """GGUF 모델 로드"""
        try:
            from llama_cpp import Llama
            
            # GGUF 모델 로드
            self.gguf_model = Llama(
                model_path=self.config.finetune.model_name,
                n_ctx=2048,
                n_threads=4,
                n_gpu_layers=1
            )
            
            # 토크나이저는 Phi-3.5용으로 설정
            self.tokenizer = AutoTokenizer.from_pretrained(
                "microsoft/Phi-3.5-mini",
                trust_remote_code=True
            )
            
            # 패딩 토큰 설정
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            logger.info("GGUF 모델 로드 완료")
            
        except ImportError:
            logger.error("llama-cpp-python이 설치되지 않았습니다. pip install llama-cpp-python으로 설치하세요.")
            raise
        except Exception as e:
            logger.error(f"GGUF 모델 로드 실패: {e}")
            raise
    
    def _load_hf_model(self):
        """Hugging Face 모델 로드"""
        # 양자화 설정 (GTX 1050 Ti용)
        quantization_config = None
        if self.config.finetune.use_4bit:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
            logger.info("4비트 양자화 설정 적용")
        elif self.config.finetune.use_8bit:
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True
            )
            logger.info("8비트 양자화 설정 적용")
        
        # 모델 로드
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.finetune.model_name,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True
        )
        
        # 토크나이저 로드
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.finetune.model_name,
            trust_remote_code=True
        )
        
        # 패딩 토큰 설정
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def setup_lora(self):
        """LoRA 설정"""
        
        logger.info("LoRA 설정 중...")
        
        # LoRA 설정
        lora_config = LoraConfig(
            r=self.config.finetune.lora_r,
            lora_alpha=self.config.finetune.lora_alpha,
            target_modules=self.config.finetune.target_modules,
            lora_dropout=self.config.finetune.lora_dropout,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )
        
        # 모델에 LoRA 적용
        self.model = get_peft_model(self.model, lora_config)
        
        # 훈련 가능한 파라미터 출력
        self.model.print_trainable_parameters()
        
        logger.info("LoRA 설정 완료")
    
    def tokenize_function(self, examples):
        """토크나이징 함수"""
        return self.tokenizer(
            examples["text"],
            truncation=True,
            padding=True,
            max_length=self.config.finetune.max_seq_length,
            return_tensors="pt"
        )
    
    def prepare_dataset(self, dataset: Dataset) -> Dataset:
        """데이터셋 준비"""
        tokenized_dataset = dataset.map(
            self.tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )
        return tokenized_dataset
    
    def setup_training_args(self) -> TrainingArguments:
        """훈련 인수 설정"""
        
        # 출력 디렉토리 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(
            self.config.finetune.output_dir, 
            f"finetuned_{self.config.finetune.model_type}_{timestamp}"
        )
        
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=self.config.finetune.num_epochs,
            per_device_train_batch_size=self.config.finetune.batch_size,
            per_device_eval_batch_size=self.config.finetune.batch_size,
            gradient_accumulation_steps=self.config.finetune.gradient_accumulation_steps,
            learning_rate=self.config.finetune.learning_rate,
            warmup_steps=100,
            logging_steps=self.config.finetune.logging_steps,
            save_steps=self.config.finetune.save_steps,
            eval_strategy="steps",
            eval_steps=self.config.finetune.eval_steps,
            save_total_limit=3,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            fp16=True,
            dataloader_pin_memory=False,
            remove_unused_columns=False,
            report_to="wandb" if self.config.finetune.use_wandb else None,
        )
        
        return training_args
    
    def setup_trainer(self, train_dataset: Dataset, eval_dataset: Dataset):
        """Trainer 설정"""
        
        # 데이터 콜레이터
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
        )
        
        # 훈련 인수
        training_args = self.setup_training_args()
        
        # Trainer 생성
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )
        
        logger.info("Trainer 설정 완료")
    
    def train(self, train_dataset: Dataset, eval_dataset: Dataset):
        """모델 훈련"""
        
        logger.info("파인튜닝 시작...")
        
        # 모델과 토크나이저 설정
        self.setup_model_and_tokenizer()
        
        # LoRA 설정
        self.setup_lora()
        
        # 데이터셋 준비
        train_dataset = self.prepare_dataset(train_dataset)
        eval_dataset = self.prepare_dataset(eval_dataset)
        
        # Trainer 설정
        self.setup_trainer(train_dataset, eval_dataset)
        
        # 훈련 실행
        try:
            train_result = self.trainer.train()
            
            # 훈련 결과 저장
            self.save_training_results(train_result)
            
            logger.info("파인튜닝 완료!")
            
        except Exception as e:
            logger.error(f"훈련 중 오류 발생: {e}")
            raise
    
    def save_training_results(self, train_result):
        """훈련 결과 저장"""
        
        # 훈련 메트릭 저장
        metrics = train_result.metrics
        metrics_file = os.path.join(self.trainer.args.output_dir, "training_metrics.json")
        
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        logger.info(f"훈련 메트릭 저장: {metrics_file}")
    
    def save_model(self, output_path: Optional[str] = None):
        """모델 저장"""
        
        if output_path is None:
            output_path = self.trainer.args.output_dir
        
        # 모델 저장
        self.model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)
        
        # 설정 파일 저장
        config_file = os.path.join(output_path, "finetune_config.json")
        self.config.save_config(config_file)
        
        logger.info(f"모델 저장 완료: {output_path}")
        
        return output_path
    
    def convert_to_gguf(self, model_path: str, output_path: str):
        """GGUF 형식으로 변환 (선택사항)"""
        
        try:
            # llama-cpp-python을 사용한 변환
            from llama_cpp import Llama
            
            # 변환 스크립트 실행
            convert_script = f"""
            python -m llama_cpp.convert_hf_to_gguf {model_path} --outfile {output_path}
            """
            
            os.system(convert_script)
            logger.info(f"GGUF 변환 완료: {output_path}")
            
        except ImportError:
            logger.warning("llama-cpp-python이 설치되지 않아 GGUF 변환을 건너뜁니다.")
        except Exception as e:
            logger.error(f"GGUF 변환 실패: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        
        if self.model is None:
            return {}
        
        # 훈련 가능한 파라미터 수
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        all_params = sum(p.numel() for p in self.model.parameters())
        
        info = {
            "model_name": self.config.finetune.model_name,
            "model_type": self.config.finetune.model_type,
            "trainable_parameters": trainable_params,
            "total_parameters": all_params,
            "trainable_ratio": trainable_params / all_params if all_params > 0 else 0,
            "lora_r": self.config.finetune.lora_r,
            "lora_alpha": self.config.finetune.lora_alpha,
            "target_modules": self.config.finetune.target_modules,
            "use_4bit": self.config.finetune.use_4bit,
            "use_8bit": self.config.finetune.use_8bit,
        }
        
        return info
    
    def estimate_training_time(self, train_dataset: Dataset) -> Dict[str, Any]:
        """훈련 시간 예상"""
        
        # 데이터 크기
        total_samples = len(train_dataset)
        batch_size = self.config.finetune.batch_size
        gradient_accumulation_steps = self.config.finetune.gradient_accumulation_steps
        num_epochs = self.config.finetune.num_epochs
        
        # 스텝 수 계산
        steps_per_epoch = total_samples // (batch_size * gradient_accumulation_steps)
        total_steps = steps_per_epoch * num_epochs
        
        # GTX 1050 Ti 기준 예상 시간 (분)
        estimated_minutes = total_steps * 0.5  # 스텝당 약 0.5분
        
        estimate = {
            "total_samples": total_samples,
            "batch_size": batch_size,
            "gradient_accumulation_steps": gradient_accumulation_steps,
            "num_epochs": num_epochs,
            "steps_per_epoch": steps_per_epoch,
            "total_steps": total_steps,
            "estimated_minutes": estimated_minutes,
            "estimated_hours": estimated_minutes / 60,
        }
        
        return estimate 