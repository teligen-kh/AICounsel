from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from langchain_mongodb import MongoDBChatMessageHistory
from ..config import settings
from .mongodb_search_service import MongoDBSearchService
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
import logging

class LLMService:
    def __init__(self, db: AsyncIOMotorDatabase = None, use_db_priority: bool = True):
        """
        LLM 서비스 초기화
        
        Args:
            db: MongoDB 데이터베이스 연결
            use_db_priority: DB 우선 검색 모드 사용 여부
        """
        self.db = db
        self.use_db_priority = use_db_priority
        
        # MongoDB 검색 서비스 초기화
        if db is not None and use_db_priority:
            self.search_service = MongoDBSearchService(db)
        else:
            self.search_service = None
        
        # LLaMA 3.1 8B Instruct 모델 경로
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                "models", "Llama-3.1-8B-Instruct")
        
        # 토크나이저와 모델 로드 (임시로 비활성화)
        try:
            # 모델 로딩을 임시로 비활성화하여 DB 검색만 테스트
            logging.info("LLM model loading temporarily disabled for testing")
            self.tokenizer = None
            self.model = None
            # self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            # self.model = AutoModelForCausalLM.from_pretrained(
            #     model_path,
            #     torch_dtype=torch.float16,
            #     device_map="auto",
            #     trust_remote_code=True
            # )
            # logging.info("LLM model loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load LLM model: {str(e)}")
            self.tokenizer = None
            self.model = None

    def set_db_priority_mode(self, enabled: bool):
        """DB 우선 검색 모드를 설정합니다."""
        self.use_db_priority = enabled
        if enabled and self.db is not None:
            self.search_service = MongoDBSearchService(self.db)
        else:
            self.search_service = None
        logging.info(f"DB priority mode: {'enabled' if enabled else 'disabled'}")

    async def get_response(self, session_id: str, message: str) -> str:
        try:
            # 1. DB 우선 검색 모드가 활성화된 경우 MongoDB에서 관련 답변 검색
            if self.use_db_priority and self.search_service:
                db_answer = await self.search_service.get_best_answer(message)
                if db_answer:
                    logging.info(f"Found relevant answer from DB for query: {message[:50]}...")
                    # DB 답변을 기반으로 한 개선된 응답 생성
                    return await self._enhance_db_answer(message, db_answer, session_id)
            
            # 2. DB에서 관련 답변을 찾지 못한 경우 일반 LLM 응답 생성
            return await self._generate_llm_response(session_id, message)
            
        except Exception as e:
            logging.error(f"Error in get_response: {str(e)}")
            return "죄송합니다. 일시적인 오류가 발생했습니다. 다시 한 번 말씀해 주시겠어요?"
    
    async def _enhance_db_answer(self, user_message: str, db_answer: str, session_id: str) -> str:
        """DB에서 찾은 답변을 개선하여 반환합니다."""
        try:
            # 모델이 로드되지 않은 경우 DB 답변을 그대로 반환
            if self.model is None or self.tokenizer is None:
                logging.warning("LLM model not loaded, returning DB answer directly")
                return db_answer
            
            # MongoDB 기반 메시지 히스토리 설정
            message_history = MongoDBChatMessageHistory(
                connection_string=settings.MONGODB_URL,
                database_name=settings.MONGODB_DB_NAME,
                collection_name="chat_history",
                session_id=session_id
            )
            
            # 이전 대화 내용 가져오기
            messages = message_history.messages
            
            # LLaMA 3.1 8B Instruct 형식으로 대화 구성
            conversation_text = ""
            for msg in messages:
                if msg.type == "human":
                    conversation_text += f"<|im_start|>user\n{msg.content}<|im_end|>\n"
                elif msg.type == "ai":
                    conversation_text += f"<|im_start|>assistant\n{msg.content}<|im_end|>\n"
            
            # DB 답변을 참고하여 개선된 프롬프트 구성
            enhanced_prompt = f"""다음은 사용자의 질문과 관련된 기존 답변입니다. 이 답변을 참고하여 더 자연스럽고 도움이 되는 답변을 제공해주세요.

사용자 질문: {user_message}
참고 답변: {db_answer}

위의 참고 답변을 바탕으로 사용자의 질문에 대해 친근하고 도움이 되는 답변을 한국어로 제공해주세요. 답변은 자연스럽고 대화체로 작성해주세요."""

            # 현재 메시지 추가
            conversation_text += f"<|im_start|>user\n{enhanced_prompt}<|im_end|>\n<|im_start|>assistant\n"
            
            # 모델에 직접 입력
            inputs = self.tokenizer(conversation_text, return_tensors="pt")
            
            # 생성
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=300,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # 응답 디코딩
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # <|im_start|>assistant 이후의 내용만 추출
            if "<|im_start|>assistant" in response:
                response = response.split("<|im_start|>assistant")[-1].strip()
            
            # <|im_end|> 이전의 내용만 추출
            if "<|im_end|>" in response:
                response = response.split("<|im_end|>")[0].strip()
            
            # 응답 정리
            response = self._clean_response(response)
            
            # 응답 저장
            message_history.add_user_message(user_message)
            message_history.add_ai_message(response)
            
            return response
            
        except Exception as e:
            logging.error(f"Error enhancing DB answer: {str(e)}")
            # DB 답변을 그대로 반환
            return db_answer
    
    async def _generate_llm_response(self, session_id: str, message: str) -> str:
        """일반적인 LLM 응답을 생성합니다."""
        try:
            # 모델이 로드되지 않은 경우 임시 응답 반환
            if self.model is None or self.tokenizer is None:
                logging.warning("LLM model not loaded, returning temporary response")
                return "현재 AI 모델이 로드 중입니다. 잠시 후 다시 시도해주세요."
            
            # MongoDB 기반 메시지 히스토리 설정
            message_history = MongoDBChatMessageHistory(
                connection_string=settings.MONGODB_URL,
                database_name=settings.MONGODB_DB_NAME,
                collection_name="chat_history",
                session_id=session_id
            )
            
            # 이전 대화 내용 가져오기
            messages = message_history.messages
            
            # LLaMA 3.1 8B Instruct 형식으로 대화 구성
            conversation_text = ""
            for msg in messages:
                if msg.type == "human":
                    conversation_text += f"<|im_start|>user\n{msg.content}<|im_end|>\n"
                elif msg.type == "ai":
                    conversation_text += f"<|im_start|>assistant\n{msg.content}<|im_end|>\n"
            
            # 현재 메시지 추가
            conversation_text += f"<|im_start|>user\n{message}<|im_end|>\n<|im_start|>assistant\n"
            
            # 모델에 직접 입력
            inputs = self.tokenizer(conversation_text, return_tensors="pt")
            
            # 생성
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=200,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # 응답 디코딩
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # <|im_start|>assistant 이후의 내용만 추출
            if "<|im_start|>assistant" in response:
                response = response.split("<|im_start|>assistant")[-1].strip()
            
            # <|im_end|> 이전의 내용만 추출
            if "<|im_end|>" in response:
                response = response.split("<|im_end|>")[0].strip()
            
            # 응답 정리
            response = self._clean_response(response)
            
            # 응답 저장
            message_history.add_user_message(message)
            message_history.add_ai_message(response)
            
            return response
            
        except Exception as e:
            logging.error(f"Error generating LLM response: {str(e)}")
            return "죄송합니다. 일시적인 오류가 발생했습니다. 다시 한 번 말씀해 주시겠어요?"
    
    def _clean_response(self, response: str) -> str:
        """응답에서 불필요한 태그나 메타데이터를 제거합니다."""
        # 특수 태그 제거
        tags_to_remove = [
            "<|eot_id|>", "<|start_header_id|>", "<|end_header_id|>",
            "<|im_start|>", "<|im_end|>", "<|endoftext|>",
            "assistant:", "user:", "system:", "Human:", "Me:"
        ]
        
        for tag in tags_to_remove:
            response = response.replace(tag, "")
        
        # 빈 응답이나 너무 짧은 응답 처리
        response = response.strip()
        if len(response) < 5:
            return "죄송합니다. 다시 한 번 말씀해 주시겠어요?"
        
        # 중복된 공백 제거
        import re
        response = re.sub(r'\s+', ' ', response).strip()
        
        return response 