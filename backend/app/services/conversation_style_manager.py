from typing import Dict, Any, Optional
from enum import Enum
import logging

class ConversationStyle(Enum):
    """대화 스타일 타입"""
    FRIENDLY = "friendly"           # 친근한 스타일
    PROFESSIONAL = "professional"   # 전문적인 스타일
    FORMAL = "formal"              # 격식있는 스타일
    CASUAL = "casual"              # 일상적인 스타일
    TECHNICAL = "technical"        # 기술적인 스타일

class ConversationStyleManager:
    """고객사별 대화 스타일 관리자"""
    
    def __init__(self, company_name: str = "텔리젠"):
        self.styles = self._initialize_styles()
        self.default_style = ConversationStyle.FRIENDLY
        self.company_name = company_name
    
    def _initialize_styles(self) -> Dict[ConversationStyle, Dict[str, Any]]:
        """대화 스타일 초기화"""
        return {
            ConversationStyle.FRIENDLY: {
                "name": "친근한 상담사",
                "system_prompt": """<|system|>당신은 [업체명]의 친절한 AI 상담사입니다. 

대화 스타일:
- 자연스럽고 친근하게 대화하세요
- 간단하고 명확하게 답변하세요
- 불필요하게 복잡하게 설명하지 마세요
- 사람처럼 편안하게 대화하세요

응대 규칙:
- 인사말 → "안녕하세요! 어떻게 도와드릴까요?"
- 일상 대화 → 친근하고 간단하게 답변
- 기술적 질문 → DB 정보를 바탕으로 설명, 정보 없으면 "상담사를 통해 연락 드리겠습니다"
- 비상담 질문 → "저는 [업체명] AI 상담사로 해당 질문은 상담 범위를 벗어나 답변 드릴 수 없습니다"
- 욕설 → "욕설을 하시면 응대를 할 수 없습니다. 30분 후 재문의 바랍니다"

답변 길이: 1-2문장으로 간결하게<|end|>""",
                "max_tokens": 75,
                "temperature": 0.3,
                "response_format": "간결하고 친근하게"
            },
            
            ConversationStyle.PROFESSIONAL: {
                "name": "전문 상담사",
                "system_prompt": """당신은 전문적이고 신뢰할 수 있는 상담사입니다.

핵심 규칙:
1. 확실한 정보만 제공하세요. 불확실한 정보는 "정확한 정보를 확인할 수 없습니다"라고 답변하세요.
2. 한국어로 자연스럽게 대화하세요.
3. 전문적이고 정확한 정보를 제공하세요.
4. 인사말에는 적절한 전문적 인사말로 답변하세요.
5. 불필요하게 복잡하게 설명하지 마세요.
6. 전문적이면서도 친근한 톤을 유지하세요.
7. 잘못된 정보나 추측은 절대 하지 마세요.

대화 스타일:
- 인사말 → 전문적이면서도 친근한 인사말 (예: "안녕하세요. 무엇을 도와드릴까요?")
- 질문 → 정확하고 전문적으로 답변
- 상담 요청 → 상세하고 정확한 정보 제공
- 불확실한 내용 → "정확한 정보를 확인할 수 없습니다"라고 답변

답변 길이: 2-3문장으로 적절하게""",
                "max_tokens": 100,
                "temperature": 0.15,
                "response_format": "전문적이고 정확하게"
            },
            
            ConversationStyle.FORMAL: {
                "name": "격식있는 상담사",
                "system_prompt": """당신은 격식있고 신뢰할 수 있는 상담사입니다.

다음 규칙을 엄격히 따르세요:
1. 확실한 정보만 제공하세요. 불확실한 정보는 "정확한 정보를 확인할 수 없습니다"라고 답변하세요.
2. 한국어로 격식있게 대화하세요.
3. 인사말에는 적절한 격식있는 인사말로 답변하세요.
4. 정중하고 예의 바른 톤을 유지하세요.
5. 불필요하게 복잡하게 설명하지 마세요.
6. 잘못된 정보나 추측은 절대 하지 마세요.""",
                "max_tokens": 100,
                "temperature": 0.1,
                "response_format": "격식있고 정중하게"
            },
            
            ConversationStyle.CASUAL: {
                "name": "일상적인 상담사",
                "system_prompt": """당신은 편안하고 신뢰할 수 있는 상담사입니다.

다음 규칙을 엄격히 따르세요:
1. 확실한 정보만 제공하세요. 불확실한 정보는 "정확한 정보를 확인할 수 없습니다"라고 답변하세요.
2. 한국어로 편안하게 대화하세요.
3. 인사말에는 간단하고 편안한 인사말로 답변하세요.
4. 불필요하게 복잡하게 설명하지 마세요.
5. 편안하고 친근한 톤을 유지하세요.
6. 잘못된 정보나 추측은 절대 하지 마세요.""",
                "max_tokens": 80,
                "temperature": 0.4,
                "response_format": "편안하고 간결하게"
            },
            
            ConversationStyle.TECHNICAL: {
                "name": "기술 전문 상담사",
                "system_prompt": """당신은 기술적이고 신뢰할 수 있는 상담사입니다.

다음 규칙을 엄격히 따르세요:
1. 확실한 정보만 제공하세요. 불확실한 정보는 "정확한 정보를 확인할 수 없습니다"라고 답변하세요.
2. 한국어로 기술적으로 정확하게 대화하세요.
3. 기술적 문제에 대해 구체적이고 정확한 답변을 제공하세요.
4. 인사말에는 간단한 인사말로 답변하세요.
5. 불필요하게 복잡하게 설명하지 마세요.
6. 기술적이면서도 이해하기 쉽게 설명하세요.
7. 잘못된 정보나 추측은 절대 하지 마세요.""",
                "max_tokens": 150,
                "temperature": 0.2,
                "response_format": "기술적이고 정확하게"
            }
        }
    
    def get_style(self, style: ConversationStyle) -> Dict[str, Any]:
        """특정 스타일 정보 반환"""
        return self.styles.get(style, self.styles[self.default_style])
    
    def get_system_prompt(self, style: ConversationStyle) -> str:
        """특정 스타일의 시스템 프롬프트 반환"""
        prompt = self.get_style(style)["system_prompt"]
        # 업체명 치환
        return prompt.replace("[업체명]", self.company_name)
    
    def get_parameters(self, style: ConversationStyle) -> Dict[str, Any]:
        """특정 스타일의 파라미터 반환"""
        style_info = self.get_style(style)
        return {
            "max_tokens": style_info["max_tokens"],
            "temperature": style_info["temperature"]
        }
    
    def get_all_styles(self) -> Dict[str, str]:
        """모든 스타일 이름 반환"""
        return {style.value: info["name"] for style, info in self.styles.items()}
    
    def add_custom_style(self, name: str, style_config: Dict[str, Any]) -> bool:
        """커스텀 스타일 추가"""
        try:
            self.styles[name] = style_config
            logging.info(f"커스텀 스타일 추가됨: {name}")
            return True
        except Exception as e:
            logging.error(f"커스텀 스타일 추가 실패: {str(e)}")
            return False

# 전역 인스턴스
_style_manager: Optional[ConversationStyleManager] = None

def get_style_manager() -> ConversationStyleManager:
    """스타일 매니저 인스턴스 반환"""
    global _style_manager
    if _style_manager is None:
        _style_manager = ConversationStyleManager()
    return _style_manager 