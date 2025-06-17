from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from langchain_community.llms import HuggingFacePipeline
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
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
        
        # 파이프라인 생성
        from transformers import pipeline
        pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=100,
            temperature=0.2,
            top_p=0.2,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        # LangChain 파이프라인으로 변환
        self.llm = HuggingFacePipeline(pipeline=pipe)
        
        # 프롬프트 템플릿 설정
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 한국의 IT 기술지원 상담사입니다. 고객의 문제에 공감을 표현하고 구체적인 해결 방법을 제시하세요. 항상 한국어로만 답변하세요."),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        
        # 체인 구성
        self.chain = (
            self.prompt
            | self.llm
            | StrOutputParser()
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
            
            # 응답 생성
            response = await self.chain.ainvoke({
                "history": messages,
                "input": message
            })
            
            # 응답에서 태그 제거
            response = response.replace("<|eot_id|>", "").replace("<|start_header_id|>", "").replace("<|end_header_id|>", "").strip()
            
            # assistant 태그 이후의 내용만 추출
            if "assistant" in response:
                parts = response.split("assistant")
                if len(parts) > 1:
                    response = parts[-1].strip()
            
            # 영어 응답이 나온 경우 기본 응답으로 대체
            if any(word in response.lower() for word in ['hello', 'hi', 'thank', 'please', 'sorry']):
                return "죄송합니다. 문제를 자세히 파악하고 도와드리도록 하겠습니다. 어떤 증상이 나타나시나요?"
            
            # 응답 저장
            message_history.add_user_message(message)
            message_history.add_ai_message(response)
            
            return response
            
        except Exception as e:
            print(f"Error in get_response: {str(e)}")
            return "죄송합니다. 일시적인 오류가 발생했습니다. 다시 한 번 말씀해 주시겠어요?" 