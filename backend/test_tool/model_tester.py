"""
파인튜닝된 모델 테스트 도구
개발 컴퓨터에서 파인튜닝된 모델을 테스트하고 성능을 평가
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelTester:
    """파인튜닝된 모델 테스트 클래스"""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.config = None
        
    def load_model(self):
        """모델 로드"""
        
        logger.info(f"모델 로드 중: {self.model_path}")
        
        try:
            # 설정 파일 로드
            config_file = os.path.join(self.model_path, "finetune_config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info("설정 파일 로드 완료")
            
            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # 기본 모델 로드
            base_model = AutoModelForCausalLM.from_pretrained(
                self.config["finetune"]["model_name"] if self.config else "microsoft/Phi-3.5-mini",
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
            
            # LoRA 어댑터 로드
            self.model = PeftModel.from_pretrained(base_model, self.model_path)
            
            logger.info("모델 로드 완료")
            
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            raise
    
    def generate_response(self, prompt: str, max_length: int = 200, 
                         temperature: float = 0.7, top_p: float = 0.9) -> str:
        """응답 생성"""
        
        if self.model is None:
            raise ValueError("모델이 로드되지 않았습니다.")
        
        try:
            # 입력 토크나이징
            inputs = self.tokenizer(prompt, return_tensors="pt")
            
            # GPU로 이동
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # 생성
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # 디코딩
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 프롬프트 제거
            if response.startswith(prompt):
                response = response[len(prompt):].strip()
            
            return response
            
        except Exception as e:
            logger.error(f"응답 생성 실패: {e}")
            return f"오류 발생: {str(e)}"
    
    def test_counseling_scenarios(self) -> Dict[str, Any]:
        """상담 시나리오 테스트"""
        
        test_scenarios = [
            {
                "category": "카드결제 문제",
                "prompt": "고객이 카드결제가 안된다고 문의합니다. 어떻게 응답하시겠습니까?",
                "expected_keywords": ["인터넷", "리더기", "단말기", "확인"]
            },
            {
                "category": "비밀번호 문의",
                "prompt": "고객이 비밀번호 관련 문의를 합니다. 어떻게 응답하시겠습니까?",
                "expected_keywords": ["확인", "불가능", "기술팀"]
            },
            {
                "category": "프로그램 설치",
                "prompt": "고객이 프로그램 재설치를 요청합니다. 어떻게 응답하시겠습니까?",
                "expected_keywords": ["백업", "설치", "코드"]
            },
            {
                "category": "일반 상담",
                "prompt": "고객이 안녕하세요라고 인사합니다. 어떻게 응답하시겠습니까?",
                "expected_keywords": ["안녕", "감사", "도움"]
            }
        ]
        
        results = []
        
        for scenario in test_scenarios:
            logger.info(f"테스트 시나리오: {scenario['category']}")
            
            # 응답 생성
            start_time = time.time()
            response = self.generate_response(scenario["prompt"])
            generation_time = time.time() - start_time
            
            # 키워드 매칭 확인
            matched_keywords = []
            for keyword in scenario["expected_keywords"]:
                if keyword.lower() in response.lower():
                    matched_keywords.append(keyword)
            
            # 결과 저장
            result = {
                "category": scenario["category"],
                "prompt": scenario["prompt"],
                "response": response,
                "generation_time": generation_time,
                "expected_keywords": scenario["expected_keywords"],
                "matched_keywords": matched_keywords,
                "keyword_match_rate": len(matched_keywords) / len(scenario["expected_keywords"])
            }
            
            results.append(result)
            
            logger.info(f"응답: {response[:100]}...")
            logger.info(f"키워드 매칭률: {result['keyword_match_rate']:.2f}")
        
        return {
            "test_scenarios": results,
            "average_keyword_match_rate": sum(r["keyword_match_rate"] for r in results) / len(results),
            "average_generation_time": sum(r["generation_time"] for r in results) / len(results)
        }
    
    def compare_with_original(self, original_model_path: str) -> Dict[str, Any]:
        """원본 모델과 비교"""
        
        logger.info("원본 모델과 비교 테스트 시작")
        
        # 원본 모델 로드
        original_tokenizer = AutoTokenizer.from_pretrained(
            original_model_path,
            trust_remote_code=True
        )
        
        original_model = AutoModelForCausalLM.from_pretrained(
            original_model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        # 테스트 프롬프트
        test_prompts = [
            "카드결제가 안됩니다",
            "비밀번호를 잊어버렸어요",
            "프로그램을 재설치하고 싶어요",
            "안녕하세요"
        ]
        
        comparison_results = []
        
        for prompt in test_prompts:
            # 파인튜닝된 모델 응답
            finetuned_response = self.generate_response(prompt)
            
            # 원본 모델 응답
            inputs = original_tokenizer(prompt, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = original_model.generate(
                    **inputs,
                    max_length=200,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=original_tokenizer.eos_token_id
                )
            
            original_response = original_tokenizer.decode(outputs[0], skip_special_tokens=True)
            if original_response.startswith(prompt):
                original_response = original_response[len(prompt):].strip()
            
            comparison_results.append({
                "prompt": prompt,
                "finetuned_response": finetuned_response,
                "original_response": original_response,
                "improvement": self.assess_improvement(finetuned_response, original_response)
            })
        
        return {
            "comparison_results": comparison_results,
            "average_improvement": sum(r["improvement"] for r in comparison_results) / len(comparison_results)
        }
    
    def assess_improvement(self, finetuned_response: str, original_response: str) -> float:
        """개선도 평가 (0-1)"""
        
        # 간단한 평가 기준
        counseling_keywords = ["확인", "설정", "설치", "백업", "코드", "기술팀", "문의"]
        
        finetuned_score = sum(1 for keyword in counseling_keywords if keyword in finetuned_response)
        original_score = sum(1 for keyword in counseling_keywords if keyword in original_response)
        
        # 응답 길이 고려
        finetuned_length = len(finetuned_response)
        original_length = len(original_response)
        
        # 적절한 길이 보너스 (50-200자)
        finetuned_length_bonus = 1.0 if 50 <= finetuned_length <= 200 else 0.5
        original_length_bonus = 1.0 if 50 <= original_length <= 200 else 0.5
        
        finetuned_total = finetuned_score * finetuned_length_bonus
        original_total = original_score * original_length_bonus
        
        if original_total == 0:
            return 1.0 if finetuned_total > 0 else 0.0
        
        improvement = (finetuned_total - original_total) / original_total
        return max(0.0, min(1.0, improvement))
    
    def interactive_test(self):
        """대화형 테스트"""
        
        print("\n=== 대화형 모델 테스트 ===")
        print("종료하려면 'quit' 또는 'exit'를 입력하세요.\n")
        
        while True:
            try:
                user_input = input("사용자: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '종료']:
                    break
                
                if not user_input:
                    continue
                
                # 응답 생성
                start_time = time.time()
                response = self.generate_response(user_input)
                generation_time = time.time() - start_time
                
                print(f"AI 상담사: {response}")
                print(f"(생성 시간: {generation_time:.2f}초)\n")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"오류 발생: {e}\n")
        
        print("테스트를 종료합니다.")
    
    def save_test_results(self, results: Dict[str, Any], output_path: str):
        """테스트 결과 저장"""
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 타임스탬프 추가
        results["timestamp"] = datetime.now().isoformat()
        results["model_path"] = self.model_path
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"테스트 결과 저장: {output_path}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        
        info = {
            "model_path": self.model_path,
            "config": self.config,
            "tokenizer_vocab_size": len(self.tokenizer) if self.tokenizer else 0,
        }
        
        if self.model:
            # 모델 크기 계산
            param_size = 0
            buffer_size = 0
            
            for param in self.model.parameters():
                param_size += param.nelement() * param.element_size()
            
            for buffer in self.model.buffers():
                buffer_size += buffer.nelement() * buffer.element_size()
            
            size_all_mb = (param_size + buffer_size) / 1024**2
            
            info.update({
                "model_size_mb": size_all_mb,
                "trainable_parameters": sum(p.numel() for p in self.model.parameters() if p.requires_grad),
                "total_parameters": sum(p.numel() for p in self.model.parameters())
            })
        
        return info

def main():
    """메인 함수"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="파인튜닝된 모델 테스트")
    parser.add_argument("--model_path", required=True, help="파인튜닝된 모델 경로")
    parser.add_argument("--test_type", choices=["scenarios", "comparison", "interactive"], 
                       default="scenarios", help="테스트 타입")
    parser.add_argument("--original_model", help="원본 모델 경로 (비교 테스트용)")
    parser.add_argument("--output", help="결과 저장 경로")
    
    args = parser.parse_args()
    
    # 모델 테스터 생성
    tester = ModelTester(args.model_path)
    
    try:
        # 모델 로드
        tester.load_model()
        
        # 모델 정보 출력
        model_info = tester.get_model_info()
        print(f"모델 정보: {json.dumps(model_info, indent=2, ensure_ascii=False)}")
        
        # 테스트 실행
        if args.test_type == "scenarios":
            results = tester.test_counseling_scenarios()
            print(f"\n시나리오 테스트 결과:")
            print(f"평균 키워드 매칭률: {results['average_keyword_match_rate']:.2f}")
            print(f"평균 생성 시간: {results['average_generation_time']:.2f}초")
            
        elif args.test_type == "comparison":
            if not args.original_model:
                print("원본 모델 경로를 지정해주세요.")
                return
            results = tester.compare_with_original(args.original_model)
            print(f"\n비교 테스트 결과:")
            print(f"평균 개선도: {results['average_improvement']:.2f}")
            
        elif args.test_type == "interactive":
            tester.interactive_test()
            return
        
        # 결과 저장
        if args.output:
            tester.save_test_results(results, args.output)
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    main() 