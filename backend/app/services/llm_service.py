from langchain_community.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import ConversationChain
from langchain_community.chat_message_histories import MongoDBChatMessageHistory
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from ..config import settings
import os

class LLMService:
    def __init__(self):
        # 콜백 매니저 설정
        callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
        
        # Llama 모델 초기화
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                "models", "llama-2-7b-chat.Q4_K_M.gguf")
        
        self.llm = LlamaCpp(
            model_path=model_path,
            temperature=0.2,     # 더 일관된 응답을 위해 조정
            max_tokens=100,      # 응답 길이 유지
            top_p=0.2,          # 더 일관된 응답을 위해 조정
            callback_manager=callback_manager,
            verbose=True,
            n_ctx=4096,
            grammar_path=None,
            chat_format="chatml",
            stop=["<|im_end|>", "<|im_start|>", "Human:", "Assistant:"]
        )

    def format_chat_history(self, messages):
        formatted_history = []
        for msg in messages:
            if hasattr(msg, 'content') and hasattr(msg, 'type'):
                role = "사용자" if msg.type == "human" else "상담사"
                formatted_history.append(f"{role}: {msg.content}")
        return "\n".join(formatted_history) if formatted_history else ""

    async def get_response(self, session_id: str, message: str) -> str:
        # MongoDB 기반 메시지 히스토리 설정
        message_history = MongoDBChatMessageHistory(
            connection_string=settings.MONGODB_URL,
            database_name=settings.MONGODB_DB_NAME,
            collection_name="chat_history",
            session_id=session_id
        )

        # 대화 메모리 설정
        memory = ConversationBufferMemory(
            chat_memory=message_history,
            return_messages=True
        )

        # 프롬프트 템플릿 설정
        template = """<|im_start|>system
당신은 한국의 IT 기술지원 상담사입니다.
절대로 영어를 사용하지 마세요.
항상 한국어로만 대화하세요.

응답 형식:
1. 먼저 고객의 문제에 공감을 표현합니다
2. 구체적인 해결 방법이나 추가 질문을 제시합니다

예시 응답:
- 프린터 문제: "프린터 연결 문제로 불편을 겪고 계시는군요. 프린터의 전원은 켜져 있는지 먼저 확인해 주시겠어요?"
- 키오스크 오류: "키오스크 작동 오류로 답답하시겠습니다. 화면에 표시되는 오류 메시지를 말씀해 주시겠어요?"
- 시스템 장애: "시스템 장애가 발생하여 불편을 드려 죄송합니다. 언제부터 이런 증상이 나타났나요?"

주의사항:
- 반드시 한국어로만 답변하세요
- 영어 사용 금지
- 2-3문장으로 짧게 답변하세요
- 전문 용어는 쉽게 설명하세요

이전 대화:
{history}
<|im_end|>
<|im_start|>human
{input}
<|im_end|>
<|im_start|>assistant"""

        prompt = PromptTemplate(
            input_variables=["history", "input"],
            template=template
        )

        # 대화 체인 설정
        conversation = ConversationChain(
            llm=self.llm,
            memory=memory,
            prompt=prompt,
            verbose=True
        )

        try:
            # 이전 대화 내용 가져오기
            messages = memory.chat_memory.messages
            formatted_history = self.format_chat_history(messages)
            
            # 응답 생성
            response = await conversation.apredict(input=message)
            
            # 응답에서 불필요한 태그나 텍스트 제거
            response = response.replace("<|im_end|>", "").replace("<|im_start|>", "").strip()
            
            # 영어 응답이 나온 경우 기본 응답으로 대체
            if any(word in response.lower() for word in ['hello', 'hi', 'thank', 'please', 'sorry']):
                return "죄송합니다. 문제를 자세히 파악하고 도와드리도록 하겠습니다. 어떤 증상이 나타나시나요?"
            
            return response
            
        except Exception as e:
            print(f"Error in get_response: {str(e)}")
            return "죄송합니다. 일시적인 오류가 발생했습니다. 다시 한 번 말씀해 주시겠어요?" 