"""
FOS Survey Agent - Session Management
Manages survey sessions and state
"""

import uuid
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from loguru import logger


class SessionState(Enum):
    """Session states"""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    ERROR = "error"


@dataclass
class SurveySession:
    """
    Survey session tracking.
    Tracks conversation state, responses, and progress.
    """
    session_id: str
    survey_id: int
    employee_id: int
    survey: Any  # Survey object
    employee: Any  # Employee object
    questions: List[Any]  # List of Question objects
    
    state: SessionState = SessionState.CREATED
    current_question_index: int = 0
    responses: Dict[int, str] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    @property
    def current_question(self) -> Optional[Any]:
        """Get current question or None if done"""
        if 0 <= self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None
    
    @property
    def is_complete(self) -> bool:
        """Check if all questions answered"""
        return (
            self.current_question_index >= len(self.questions) or
            self.state == SessionState.COMPLETED
        )
    
    @property
    def progress_percent(self) -> float:
        """Get progress percentage"""
        if not self.questions:
            return 0.0
        return (self.current_question_index / len(self.questions)) * 100
    
    def record_response(self, question_id: int, answer: str):
        """Record a response"""
        self.responses[question_id] = answer
        self.retry_count = 0  # Reset retries on success
        logger.debug(f"Recorded response for question {question_id}")
    
    def advance_to_next_question(self):
        """Move to next question"""
        self.current_question_index += 1
        self.state = SessionState.IN_PROGRESS
        logger.debug(f"Advanced to question {self.current_question_index + 1}")
    
    def increment_retry(self) -> bool:
        """Increment retry count. Returns False if max retries exceeded."""
        self.retry_count += 1
        if self.retry_count > self.max_retries:
            self.state = SessionState.ABANDONED
            return False
        return True
    
    def complete(self):
        """Mark session as completed"""
        self.state = SessionState.COMPLETED
        self.completed_at = datetime.now()
        logger.info(f"Session {self.session_id} completed with {len(self.responses)} responses")
    
    def abandon(self):
        """Mark session as abandoned"""
        self.state = SessionState.ABANDONED
        logger.warning(f"Session {self.session_id} abandoned at question {self.current_question_index}")


class SessionManager:
    """
    Manages active survey sessions.
    Provides session creation, lookup, and cleanup.
    """
    
    def __init__(self):
        self._sessions: Dict[str, SurveySession] = {}
    
    def create_session(
        self,
        survey: Any,
        employee: Any,
        questions: List[Any]
    ) -> SurveySession:
        """Create a new survey session"""
        session_id = str(uuid.uuid4())[:8]
        
        session = SurveySession(
            session_id=session_id,
            survey_id=survey.id,
            employee_id=employee.id,
            survey=survey,
            employee=employee,
            questions=questions,
            state=SessionState.CREATED
        )
        
        self._sessions[session_id] = session
        logger.info(f"Created session {session_id} for survey {survey.id}, employee {employee.id}")
        
        return session
    
    def get_session(self, session_id: str) -> Optional[SurveySession]:
        """Get session by ID"""
        return self._sessions.get(session_id)
    
    def remove_session(self, session_id: str):
        """Remove a session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.debug(f"Removed session {session_id}")
    
    def get_active_sessions(self) -> List[SurveySession]:
        """Get all active sessions"""
        return [
            s for s in self._sessions.values()
            if s.state in (SessionState.CREATED, SessionState.IN_PROGRESS)
        ]
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove sessions older than max_age_hours"""
        now = datetime.now()
        to_remove = []
        
        for sid, session in self._sessions.items():
            age_hours = (now - session.started_at).total_seconds() / 3600
            if age_hours > max_age_hours:
                to_remove.append(sid)
        
        for sid in to_remove:
            del self._sessions[sid]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old sessions")


# Global session manager
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
