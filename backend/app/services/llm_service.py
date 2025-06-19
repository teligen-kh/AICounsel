from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from langchain_mongodb import MongoDBChatMessageHistory
from ..config import settings
import os

class LLMService:
    def __init__(self):
        # LLaMA 3.1 8B Instruct 모델 경로
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                "models", "Llama-3.1-8B-Instruct")
        
        # 토크나이저와 모델 로드
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )

    async def get_response(self, session_id: str, message: str) -> str:
        try:
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
            print(f"Error in get_response: {str(e)}")
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