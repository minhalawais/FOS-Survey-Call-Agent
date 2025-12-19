"""
FOS Survey Agent - Survey Brain
State machine LLM for managing Urdu survey conversations.

Uses Qwen 2.5 via Ollama for:
- Survey state management
- Response extraction
- Natural Urdu dialogue
"""

import os
import json
from enum import Enum
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field

import ollama
from loguru import logger


class SurveyPhase(Enum):
    """Survey conversation phases."""
    GREETING = "greeting"
    IDENTITY_CONFIRM = "identity_confirm"
    INTRO = "intro"
    ASKING = "asking"
    WAITING = "waiting"
    CLOSING = "closing"
    DONE = "done"


@dataclass
class SurveyState:
    """Current state of the survey session."""
    phase: SurveyPhase = SurveyPhase.GREETING
    survey_id: int = 0
    employee_id: int = 0
    employee_name: str = ""
    questions: List[Dict] = field(default_factory=list)
    current_index: int = 0
    responses: Dict[int, str] = field(default_factory=dict)
    identity_confirmed: bool = False


# Urdu prompts for professional survey
PROMPTS = {
    "greeting": """السلام علیکم! میں FOS سروے سینٹر سے بول رہا ہوں۔
کیا آپ {name} صاحب سے بات ہو رہی ہے؟""",

    "identity_confirmed": """شکریہ {name} صاحب۔ آج میں آپ سے کچھ سوالات پوچھنا چاہتا ہوں۔
آپ کے جوابات مکمل طور پر رازدارانہ رہیں گے۔ شکایت لائن نمبر 0800-91299 ہے۔
آئیے شروع کرتے ہیں۔""",

    "ask_question": """سوال نمبر {num}: {text}""",

    "acknowledge": """شکریہ۔ اگلا سوال سنیں۔""",

    "closing": """بہت شکریہ آپ کے وقت کا۔ آپ کے جوابات محفوظ ہو گئے ہیں۔
اگر کوئی شکایت ہو تو FOS ہیلپ لائن پر کال کریں: 0800-91299
اللہ حافظ!""",

    "not_understood": """معذرت، میں سمجھ نہیں سکا۔ براہ کرم دوبارہ بتائیں۔""",

    "identity_negative": """کوئی بات نہیں۔ براہ کرم صحیح نمبر پر کال کریں۔ اللہ حافظ!"""
}


SYSTEM_PROMPT = """آپ ایک پیشہ ور سروے ایجنٹ ہیں جو اردو میں FOS سروے لیتے ہیں۔

اہم ہدایات:
1. ہمیشہ "آپ" استعمال کریں، "تم" نہیں (پیشہ ورانہ لہجہ)
2. مختصر اور واضح جوابات دیں
3. صرف سروے سے متعلق بات کریں
4. جوابات ریکارڈ کریں بالکل جیسے کہے گئے

Functions:
- save_response(question_id, answer_text): جواب محفوظ کریں
- skip_question(): موجودہ سوال چھوڑیں
- end_survey(): سروے ختم کریں

Current Survey State:
{state}

Respond in Urdu only. Be professional and respectful."""


class SurveyBrain:
    """
    Survey state machine with LLM brain.
    
    Manages conversation flow and extracts responses using Qwen 2.5.
    """
    
    def __init__(
        self,
        model: str = None,
        ollama_url: str = None
    ):
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        self.ollama_url = ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.state = SurveyState()
        self.client = None
        
        logger.info(f"Survey brain initialized with model: {self.model}")
    
    def initialize(
        self,
        survey_id: int,
        employee_id: int,
        employee_name: str,
        questions: List[Dict]
    ):
        """Initialize survey session with data."""
        self.state = SurveyState(
            survey_id=survey_id,
            employee_id=employee_id,
            employee_name=employee_name,
            questions=questions,
            phase=SurveyPhase.GREETING
        )
        logger.info(f"Survey initialized: {len(questions)} questions for {employee_name}")
    
    @property
    def is_complete(self) -> bool:
        """Check if survey is complete."""
        return self.state.phase == SurveyPhase.DONE
    
    def get_greeting(self) -> str:
        """Get initial greeting message."""
        return PROMPTS["greeting"].format(name=self.state.employee_name)
    
    async def process_input(self, user_text: str) -> Optional[str]:
        """
        Process user input and return agent response.
        
        Args:
            user_text: Transcribed Urdu speech from user
            
        Returns:
            Agent response in Urdu
        """
        logger.info(f"Processing: {user_text[:50]}...")
        
        phase = self.state.phase
        
        # Phase-specific handling
        if phase == SurveyPhase.GREETING:
            return self._handle_greeting_response(user_text)
        
        elif phase == SurveyPhase.IDENTITY_CONFIRM:
            return self._handle_identity_response(user_text)
        
        elif phase == SurveyPhase.INTRO:
            return self._handle_intro_response(user_text)
        
        elif phase in (SurveyPhase.ASKING, SurveyPhase.WAITING):
            return await self._handle_answer(user_text)
        
        elif phase == SurveyPhase.CLOSING:
            self.state.phase = SurveyPhase.DONE
            return None
        
        return PROMPTS["not_understood"]
    
    def _handle_greeting_response(self, text: str) -> str:
        """Handle response to initial greeting."""
        # Check for positive confirmation
        positive_words = ["جی", "ہاں", "yes", "جی ہاں", "بالکل"]
        text_lower = text.lower().strip()
        
        if any(word in text_lower for word in positive_words):
            self.state.identity_confirmed = True
            self.state.phase = SurveyPhase.INTRO
            
            # Return confirmation + intro + first question
            intro = PROMPTS["identity_confirmed"].format(name=self.state.employee_name)
            first_q = self._get_current_question_text()
            
            return f"{intro}\n\n{first_q}"
        else:
            # Identity not confirmed
            self.state.phase = SurveyPhase.DONE
            return PROMPTS["identity_negative"]
    
    def _handle_identity_response(self, text: str) -> str:
        """Handle identity confirmation phase."""
        return self._handle_greeting_response(text)
    
    def _handle_intro_response(self, text: str) -> str:
        """Handle intro phase - move to first question."""
        self.state.phase = SurveyPhase.WAITING
        return self._get_current_question_text()
    
    async def _handle_answer(self, text: str) -> str:
        """
        Handle user answer to current question.
        
        Uses LLM to extract and validate answer.
        """
        # Save response verbatim
        current_q = self.state.questions[self.state.current_index]
        q_id = current_q.get("id", self.state.current_index)
        
        self.state.responses[q_id] = text.strip()
        logger.info(f"Saved response for Q{q_id}: {text[:30]}...")
        
        # Move to next question
        self.state.current_index += 1
        
        if self.state.current_index >= len(self.state.questions):
            # Survey complete
            self.state.phase = SurveyPhase.CLOSING
            return PROMPTS["closing"]
        else:
            # Next question
            self.state.phase = SurveyPhase.WAITING
            ack = PROMPTS["acknowledge"]
            next_q = self._get_current_question_text()
            return f"{ack}\n\n{next_q}"
    
    def _get_current_question_text(self) -> str:
        """Get formatted current question text."""
        if self.state.current_index >= len(self.state.questions):
            return ""
        
        q = self.state.questions[self.state.current_index]
        q_num = self.state.current_index + 1
        q_text = q.get("text_ur") or q.get("text", "")
        
        return PROMPTS["ask_question"].format(num=q_num, text=q_text)
    
    def get_responses(self) -> Dict[int, str]:
        """Get all collected responses."""
        return self.state.responses
    
    def get_state_json(self) -> str:
        """Get current state as JSON for LLM context."""
        return json.dumps({
            "phase": self.state.phase.value,
            "current_question": self.state.current_index + 1,
            "total_questions": len(self.state.questions),
            "responses_collected": len(self.state.responses)
        }, ensure_ascii=False)
    
    async def query_llm(self, user_input: str) -> str:
        """
        Query Qwen LLM for complex responses.
        
        Used for handling interruptions, clarifications, etc.
        """
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT.format(state=self.get_state_json())
                    },
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
            )
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            return PROMPTS["not_understood"]
