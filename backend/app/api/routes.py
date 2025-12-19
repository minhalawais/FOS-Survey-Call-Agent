"""
FOS Survey Agent - API Routes
REST API endpoints for survey management
"""

from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from app.database import get_db, Survey, Employee
from app.agent.survey_agent import SurveyAgent
from app.agent.session import get_session_manager


router = APIRouter()


# Pydantic models
class SurveyResponse(BaseModel):
    id: int
    title: str
    title_ur: str
    description: str = ""
    description_ur: str = ""
    question_count: int = 0


class EmployeeResponse(BaseModel):
    id: int
    name: str
    name_en: str = ""
    designation: str = ""
    branch: str = ""


class SessionCreateRequest(BaseModel):
    survey_id: int
    employee_id: int


class SessionResponse(BaseModel):
    session_id: str
    survey_id: int
    employee_id: int
    employee_name: str
    total_questions: int
    current_question: int
    status: str
    progress: float


# =============================================================================
# Survey Endpoints
# =============================================================================

@router.get("/surveys", response_model=List[SurveyResponse])
def get_surveys():
    """Get all available surveys"""
    db = get_db()
    surveys = db.get_all_surveys()
    
    result = []
    for s in surveys:
        questions = db.get_questions(s.id)
        result.append(SurveyResponse(
            id=s.id,
            title=s.title,
            title_ur=s.title_ur,
            description=s.description or "",
            description_ur=s.description_ur or "",
            question_count=len(questions)
        ))
    
    return result


@router.get("/surveys/{survey_id}")
def get_survey(survey_id: int):
    """Get survey details with questions"""
    db = get_db()
    survey = db.get_survey(survey_id)
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    questions = db.get_questions(survey_id)
    
    return {
        "id": survey.id,
        "title": survey.title,
        "title_ur": survey.title_ur,
        "description": survey.description,
        "description_ur": survey.description_ur,
        "questions": [
            {
                "id": q.id,
                "order": q.order,
                "text": q.text,
                "text_ur": q.text_ur,
                "type": q.type,
                "required": q.required
            }
            for q in questions
        ]
    }


# =============================================================================
# Employee Endpoints
# =============================================================================

@router.get("/employees", response_model=List[EmployeeResponse])
def get_employees():
    """Get all employees"""
    db = get_db()
    employees = db.get_all_employees()
    
    return [
        EmployeeResponse(
            id=e.id,
            name=e.name,
            name_en=e.name_en or "",
            designation=e.designation or "",
            branch=e.branch or ""
        )
        for e in employees
    ]


@router.get("/employees/{employee_id}")
def get_employee(employee_id: int):
    """Get employee details"""
    db = get_db()
    employee = db.get_employee(employee_id)
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return {
        "id": employee.id,
        "name": employee.name,
        "name_en": employee.name_en,
        "designation": employee.designation,
        "branch": employee.branch,
        "phone": employee.phone
    }


# =============================================================================
# Agent Session Endpoints
# =============================================================================

@router.post("/agent/start")
def start_agent_session(request: SessionCreateRequest):
    """
    Start a new agent session.
    This creates a session that can then be used with WebSocket for voice.
    """
    agent = SurveyAgent.create_for_survey(request.survey_id, request.employee_id)
    
    if not agent:
        raise HTTPException(
            status_code=400, 
            detail="Could not create session. Check survey and employee IDs."
        )
    
    # Get the initial greeting
    greeting = agent.get_next_utterance()
    
    return {
        "session_id": agent.session.session_id,
        "survey_id": request.survey_id,
        "employee_id": request.employee_id,
        "employee_name": agent.session.employee.name,
        "survey_title": agent.session.survey.title_ur or agent.session.survey.title,
        "total_questions": len(agent.session.questions),
        "utterance": greeting,
        "status": "started"
    }


@router.post("/agent/respond")
def process_agent_response(session_id: str, text: str):
    """
    Process a text response (for testing without voice).
    Use WebSocket for real-time voice interaction.
    """
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Create agent with existing session
    agent = SurveyAgent(session)
    success, response_text = agent.process_response(text)
    
    return {
        "success": success,
        "utterance": response_text,
        "question_number": session.current_question_index + 1,
        "total_questions": len(session.questions),
        "is_complete": session.is_complete
    }


@router.get("/agent/session/{session_id}")
def get_session_status(session_id: str):
    """Get current session status"""
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "survey_id": session.survey_id,
        "employee_id": session.employee_id,
        "employee_name": session.employee.name,
        "current_question": session.current_question_index + 1,
        "total_questions": len(session.questions),
        "progress": f"{session.progress_percent:.0f}%",
        "status": session.state.value,
        "responses_collected": len(session.responses)
    }


@router.get("/agent/session/{session_id}/results")
def get_session_results(session_id: str):
    """Get responses collected in a session"""
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    
    if not session:
        # Try to fetch from database
        db = get_db()
        # Return empty if not found
        return {"session_id": session_id, "responses": []}
    
    # Build response list
    responses = []
    for q in session.questions:
        if q.id in session.responses:
            responses.append({
                "question_id": q.id,
                "question_text": q.text,
                "question_text_ur": q.text_ur,
                "answer_text": session.responses[q.id]
            })
    
    return {
        "session_id": session_id,
        "survey_id": session.survey_id,
        "employee_id": session.employee_id,
        "employee_name": session.employee.name,
        "status": session.state.value,
        "responses": responses
    }


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "FOS Survey Agent"
    }
