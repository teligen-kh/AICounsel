#!/usr/bin/env python3
"""
파인튜닝된 모델 테스트 실행 스크립트
개발 컴퓨터에서 실행하여 파인튜닝된 모델을 테스트
"""

import os
import sys
import argparse
import logging
import json
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_model_path(model_path: str) -> bool:
    """모델 경로 확인"""
    
    if not os.path.exists(model_path):
        logger.error(f"모델 경로가 존재하지 않습니다: {model_path}")
        return False
    
    # 필요한 파일들 확인
    required_files = [
        "adapter_config.json",
        "adapter_model.bin",
        "finetune_config.json"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = os.path.join(model_path, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        logger.warning(f"다음 파일들이 없습니다: {missing_files}")
        logger.warning("모델이 완전히 파인튜닝되지 않았을 수 있습니다.")
    
    return True

def run_scenario_test(model_path: str, output_path: str = None):
    """시나리오 테스트 실행"""
    
    from model_tester import ModelTester
    
    logger.info("시나리오 테스트를 시작합니다...")
    
    tester = ModelTester(model_path)
    tester.load_model()
    
    results = tester.test_counseling_scenarios()
    
    # 결과 출력
    print("\n=== 시나리오 테스트 결과 ===")
    print(f"평균 키워드 매칭률: {results['average_keyword_match_rate']:.2f}")
    print(f"평균 생성 시간: {results['average_generation_time']:.2f}초")
    
    print("\n=== 상세 결과 ===")
    for scenario in results['test_scenarios']:
        print(f"\n{scenario['category']}:")
        print(f"  프롬프트: {scenario['prompt']}")
        print(f"  응답: {scenario['response']}")
        print(f"  키워드 매칭률: {scenario['keyword_match_rate']:.2f}")
        print(f"  생성 시간: {scenario['generation_time']:.2f}초")
    
    # 결과 저장
    if output_path:
        tester.save_test_results(results, output_path)
        print(f"\n결과가 저장되었습니다: {output_path}")
    
    return results

def run_comparison_test(model_path: str, original_model_path: str, output_path: str = None):
    """비교 테스트 실행"""
    
    from model_tester import ModelTester
    
    logger.info("비교 테스트를 시작합니다...")
    
    tester = ModelTester(model_path)
    tester.load_model()
    
    results = tester.compare_with_original(original_model_path)
    
    # 결과 출력
    print("\n=== 비교 테스트 결과 ===")
    print(f"평균 개선도: {results['average_improvement']:.2f}")
    
    print("\n=== 상세 비교 ===")
    for comparison in results['comparison_results']:
        print(f"\n프롬프트: {comparison['prompt']}")
        print(f"파인튜닝된 모델: {comparison['finetuned_response']}")
        print(f"원본 모델: {comparison['original_response']}")
        print(f"개선도: {comparison['improvement']:.2f}")
    
    # 결과 저장
    if output_path:
        tester.save_test_results(results, output_path)
        print(f"\n결과가 저장되었습니다: {output_path}")
    
    return results

def run_interactive_test(model_path: str):
    """대화형 테스트 실행"""
    
    from model_tester import ModelTester
    
    logger.info("대화형 테스트를 시작합니다...")
    
    tester = ModelTester(model_path)
    tester.load_model()
    
    # 모델 정보 출력
    model_info = tester.get_model_info()
    print(f"\n모델 정보:")
    print(f"  경로: {model_info['model_path']}")
    print(f"  토크나이저 크기: {model_info['tokenizer_vocab_size']}")
    if 'model_size_mb' in model_info:
        print(f"  모델 크기: {model_info['model_size_mb']:.1f}MB")
    
    tester.interactive_test()

def main():
    """메인 함수"""
    
    parser = argparse.ArgumentParser(description="파인튜닝된 모델 테스트")
    parser.add_argument("--model_path", required=True, help="파인튜닝된 모델 경로")
    parser.add_argument("--test_type", choices=["scenarios", "comparison", "interactive"], 
                       default="scenarios", help="테스트 타입")
    parser.add_argument("--original_model", help="원본 모델 경로 (비교 테스트용)")
    parser.add_argument("--output", help="결과 저장 경로")
    
    args = parser.parse_args()
    
    logger.info("=== AI 상담사 모델 테스트 도구 ===")
    
    # 모델 경로 확인
    if not check_model_path(args.model_path):
        return 1
    
    # 출력 경로 설정
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"test_results_{args.test_type}_{timestamp}.json"
    
    try:
        # 테스트 실행
        if args.test_type == "scenarios":
            run_scenario_test(args.model_path, args.output)
            
        elif args.test_type == "comparison":
            if not args.original_model:
                logger.error("비교 테스트를 위해서는 --original_model 옵션이 필요합니다.")
                return 1
            run_comparison_test(args.model_path, args.original_model, args.output)
            
        elif args.test_type == "interactive":
            run_interactive_test(args.model_path)
        
        logger.info("테스트가 완료되었습니다.")
        return 0
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 