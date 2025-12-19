"""
FOS Survey Agent - Core Agent Logic
Replicates exact call agent behavior via web
State machine for conducting Urdu voice surveys
"""

from typing import Optional, Tuple
from enum import Enum
from loguru import logger

from app.database import Database, get_db, Question
from app.agent.session import SurveySession, SessionState, get_session_manager
from app.agent import prompts


class ConversationPhase(Enum):
    """Conversation phases matching call agent flow"""
    GREETING = "greeting"                    # "السلام علیکم! کیا آپ احمد صاحب..."
    WAIT_IDENTITY = "wait_identity"          # Waiting for "جی ہاں"
    CONFIRMED = "confirmed"                  # "شکریہ احمد صاحب"
    INTRO = "intro"                          # Survey introduction
    ASK_QUESTION = "ask_question"            # "سوال نمبر 1: آپ کا عہدہ کیا ہے؟"
    WAIT_ANSWER = "wait_answer"              # Listening to worker's response
    ACKNOWLEDGE = "acknowledge"              # "شکریہ، اگلا سوال سنیں"
    CLOSING = "closing"                      # "بہت شکریہ آپ کے وقت کا..."
    DONE = "done"


class SurveyAgent:
    """
    Core survey agent that replicates call agent behavior.
    
    Flow:
    1. GREETING → Agent greets and asks to confirm identity
    2. WAIT_IDENTITY → Worker says "جی ہاں"
    3. CONFIRMED → Agent thanks worker
    4. INTRO → Agent introduces survey
    5. ASK_QUESTION → Agent asks question
    6. WAIT_ANSWER → Worker speaks answer
    7. ACKNOWLEDGE → Agent acknowledges, moves to next
    8. (Repeat 5-7 for all questions)
    9. CLOSING → Agent thanks and says goodbye
    """
    
    def __init__(self, session: SurveySession):
        self.session = session
        self.db = get_db()
        self.phase = ConversationPhase.GREETING
    
    @classmethod
    def create_for_survey(
        cls,
        survey_id: int,
        employee_id: int
    ) -> Optional['SurveyAgent']:
        """
        Factory method to create a new agent for a survey.
        
        Args:
            survey_id: ID of the survey to conduct
            employee_id: ID of the employee to survey
            
        Returns:
            SurveyAgent instance or None if setup fails
        """
        db = get_db()
        
        # Get survey
        survey = db.get_survey(survey_id)
        if not survey:
            logger.error(f"Survey {survey_id} not found")
            return None
        
        # Get employee
        employee = db.get_employee(employee_id)
        if not employee:
            logger.error(f"Employee {employee_id} not found")
            return None
        
        # Get questions
        questions = db.get_questions(survey_id)
        if not questions:
            logger.error(f"No questions found for survey {survey_id}")
            return None
        
        # Create session
        session_manager = get_session_manager()
        session = session_manager.create_session(survey, employee, questions)
        
        # Create database session record
        db.create_session(session.session_id, survey_id, employee_id)
        
        logger.info(
            f"Created survey agent: session={session.session_id}, "
            f"survey={survey_id}, employee={employee_id}, questions={len(questions)}"
        )
        
        return cls(session)
    
    def get_next_utterance(self) -> str:
        """
        Get the agent's next utterance based on current phase.
        This is what the agent will speak.
        
        Returns:
            Text for TTS to speak
        """
        phase = self.phase
        
        # GREETING: "السلام علیکم! کیا آپ احمد صاحب سے بات ہو رہی ہے؟"
        if phase == ConversationPhase.GREETING:
            self.phase = ConversationPhase.WAIT_IDENTITY
            return prompts.format_greeting(self.session.employee.name)
        
        # CONFIRMED: "شکریہ احمد صاحب۔"
        elif phase == ConversationPhase.CONFIRMED:
            self.phase = ConversationPhase.INTRO
            return prompts.format_identity_confirmed(self.session.employee.name)
        
        # INTRO: Survey introduction
        elif phase == ConversationPhase.INTRO:
            self.phase = ConversationPhase.ASK_QUESTION
            return prompts.SURVEY_INTRO
        
        # ASK_QUESTION: "سوال نمبر 1: آپ کا عہدہ کیا ہے؟"
        elif phase == ConversationPhase.ASK_QUESTION:
            question = self.session.current_question
            if question:
                self.phase = ConversationPhase.WAIT_ANSWER
                return prompts.format_question(
                    question_number=self.session.current_question_index + 1,
                    question_text=question.text_ur or question.text
                )
            else:
                # No more questions
                self.phase = ConversationPhase.CLOSING
                return prompts.CLOSING
        
        # ACKNOWLEDGE: "شکریہ، اگلا سوال سنیں۔"
        elif phase == ConversationPhase.ACKNOWLEDGE:
            # Move to next question or closing
            if self.session.current_question_index >= len(self.session.questions):
                self.phase = ConversationPhase.CLOSING
                return prompts.CLOSING
            else:
                self.phase = ConversationPhase.ASK_QUESTION
                # Return acknowledge + next question
                question = self.session.current_question
                return f"{prompts.ACKNOWLEDGE_NEXT}\n\n{prompts.format_question(self.session.current_question_index + 1, question.text_ur or question.text)}"
        
        # CLOSING: Thank you and goodbye
        elif phase == ConversationPhase.CLOSING:
            self.session.complete()
            self.db.complete_session(self.session.session_id)
            self.phase = ConversationPhase.DONE
            return prompts.CLOSING
        
        elif phase == ConversationPhase.DONE:
            return ""
        
        return ""
    
    def process_response(self, transcription: str) -> Tuple[bool, str]:
        """
        Process a transcribed response from the worker.
        
        Args:
            transcription: Transcribed text from STT
            
        Returns:
            Tuple of (success, next_utterance)
        """
        phase = self.phase
        clean_text = transcription.strip()
        
        if not clean_text:
            # Empty response - ask to repeat
            if self.session.increment_retry():
                return False, prompts.REPEAT_REQUEST
            else:
                return False, prompts.CALL_LATER
        
        # WAIT_IDENTITY: Worker confirms "جی ہاں"
        if phase == ConversationPhase.WAIT_IDENTITY:
            # Accept any response as confirmation
            self.phase = ConversationPhase.CONFIRMED
            # Return confirmed + intro + first question
            confirmed = prompts.format_identity_confirmed(self.session.employee.name)
            intro = prompts.SURVEY_INTRO
            question = self.session.current_question
            first_q = prompts.format_question(1, question.text_ur or question.text)
            self.phase = ConversationPhase.WAIT_ANSWER
            return True, f"{confirmed}\n\n{intro}\n\n{first_q}"
        
        # WAIT_ANSWER: Worker speaks answer
        elif phase == ConversationPhase.WAIT_ANSWER:
            # Save the response (transcription is saved verbatim)
            question = self.session.current_question
            if question:
                self._save_response(question, clean_text)
                
                # Move to next question
                self.session.advance_to_next_question()
                
                # Check if more questions
                if self.session.current_question_index >= len(self.session.questions):
                    return True, prompts.CLOSING
                else:
                    # Acknowledge and ask next question
                    next_q = self.session.current_question
                    self.phase = ConversationPhase.WAIT_ANSWER
                    response = f"{prompts.ACKNOWLEDGE_NEXT}\n\n{prompts.format_question(self.session.current_question_index + 1, next_q.text_ur or next_q.text)}"
                    return True, response
            else:
                return False, prompts.TECHNICAL_ERROR
        
        else:
            logger.warning(f"Received response in unexpected phase: {phase}")
            return False, prompts.REPEAT_REQUEST
    
    def _save_response(self, question: Question, answer: str):
        """Save a response to the database"""
        # Record in session
        self.session.record_response(question.id, answer)
        
        # Save to database
        self.db.save_response(
            survey_id=self.session.survey_id,
            question_id=question.id,
            employee_id=self.session.employee_id,
            answer_text=answer,
            session_id=self.session.session_id
        )
        
        logger.info(
            f"Saved response: session={self.session.session_id}, "
            f"question={question.id}, answer_length={len(answer)}"
        )
    
    def skip_question(self) -> str:
        """Skip the current question (if optional)"""
        question = self.session.current_question
        
        if question and not question.required:
            self.session.advance_to_next_question()
            
            if self.session.current_question_index >= len(self.session.questions):
                return prompts.CLOSING
            else:
                next_q = self.session.current_question
                return f"{prompts.SKIPPING}\n\n{prompts.format_question(self.session.current_question_index + 1, next_q.text_ur or next_q.text)}"
        else:
            return prompts.format_question(
                self.session.current_question_index + 1,
                question.text_ur if question else ""
            )
    
    def get_status(self) -> dict:
        """Get current agent/session status"""
        return {
            'session_id': self.session.session_id,
            'phase': self.phase.value,
            'current_question': self.session.current_question_index + 1,
            'total_questions': len(self.session.questions),
            'progress': f"{self.session.progress_percent:.0f}%",
            'responses_collected': len(self.session.responses)
        }
