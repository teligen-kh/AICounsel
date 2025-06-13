from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class LLMService:
    def __init__(self):
        self.model_name = "meta-llama/Llama-2-7b-chat-hf"  # 또는 8B 버전
        self.tokenizer = None
        self.model = None
        
    async def load_model(self):
        # 4비트 양자화를 사용하여 메모리 사용량 감소
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            load_in_4bit=True,
            torch_dtype=torch.float32,
            device_map="auto"
        )
        
    async def generate_response(self, prompt: str) -> str:
        if not self.model or not self.tokenizer:
            await self.load_model()
            
        inputs = self.tokenizer(prompt, return_tensors="pt")
        
        # 생성 설정
        outputs = self.model.generate(
            inputs["input_ids"],
            max_length=2048,
            temperature=0.7,
            top_p=0.95,
            do_sample=True
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response

# 싱글톤 인스턴스
llm_service = LLMService() 