"""
FOS Survey Agent - Database Module
SQLite database for standalone development
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from contextlib import contextmanager
from datetime import datetime

from loguru import logger

from app.config import settings


@dataclass
class Survey:
    """Survey model"""
    id: int
    title: str
    title_ur: str
    description: str = ""
    description_ur: str = ""


@dataclass 
class Question:
    """Question model"""
    id: int
    survey_id: int
    order: int
    text: str
    text_ur: str
    type: str = "text"
    required: bool = True
    help_text: str = ""


@dataclass
class Employee:
    """Employee model"""
    id: int
    name: str
    name_en: str
    designation: str
    branch: str = ""
    phone: str = ""


@dataclass
class Response:
    """Survey response model"""
    id: int
    survey_id: int
    question_id: int
    employee_id: int
    answer_text: str
    created_at: datetime


class Database:
    """SQLite database manager"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_path
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Get synchronous database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database schema and load dummy data"""
        logger.info(f"Initializing database at {self.db_path}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS surveys (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    title_ur TEXT,
                    description TEXT,
                    description_ur TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY,
                    survey_id INTEGER NOT NULL,
                    question_order INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    text_ur TEXT,
                    type TEXT DEFAULT 'text',
                    required BOOLEAN DEFAULT 1,
                    help_text TEXT,
                    FOREIGN KEY (survey_id) REFERENCES surveys(id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    name_en TEXT,
                    designation TEXT,
                    branch TEXT,
                    phone TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    survey_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    employee_id INTEGER NOT NULL,
                    session_id TEXT,
                    answer_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (survey_id) REFERENCES surveys(id),
                    FOREIGN KEY (question_id) REFERENCES questions(id),
                    FOREIGN KEY (employee_id) REFERENCES employees(id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    survey_id INTEGER NOT NULL,
                    employee_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'in_progress',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (survey_id) REFERENCES surveys(id)
                )
            """)
            
            conn.commit()
            
            # Load dummy data
            self._load_dummy_data(conn)
            
            logger.info("Database initialized successfully")
    
    def _load_dummy_data(self, conn: sqlite3.Connection):
        """Load dummy data from JSON files"""
        cursor = conn.cursor()
        dummy_path = settings.dummy_data_dir
        
        logger.info(f"Loading dummy data from: {dummy_path}")
        
        # Check if dummy_path exists
        if not dummy_path.exists():
            logger.warning(f"Dummy data directory not found: {dummy_path}")
            return
        
        # Load surveys
        surveys_file = dummy_path / "surveys.json"
        if surveys_file.exists():
            try:
                surveys = json.loads(surveys_file.read_text(encoding='utf-8'))
                for s in surveys:
                    cursor.execute("""
                        INSERT OR REPLACE INTO surveys (id, title, title_ur, description, description_ur)
                        VALUES (?, ?, ?, ?, ?)
                    """, (s["id"], s["title"], s.get("title_ur", ""), 
                          s.get("description", ""), s.get("description_ur", "")))
                logger.info(f"Loaded {len(surveys)} surveys")
            except Exception as e:
                logger.error(f"Failed to load surveys: {e}")
        else:
            logger.warning(f"Surveys file not found: {surveys_file}")
        
        # Load questions
        questions_file = dummy_path / "questions.json"
        if questions_file.exists():
            try:
                questions = json.loads(questions_file.read_text(encoding='utf-8'))
                for q in questions:
                    cursor.execute("""
                        INSERT OR REPLACE INTO questions 
                        (id, survey_id, question_order, text, text_ur, type, required, help_text)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (q["id"], q["survey_id"], q["order"], q["text"], 
                          q.get("text_ur", ""), q.get("type", "text"),
                          q.get("required", True), q.get("help_text", "")))
                logger.info(f"Loaded {len(questions)} questions")
            except Exception as e:
                logger.error(f"Failed to load questions: {e}")
        else:
            logger.warning(f"Questions file not found: {questions_file}")
        
        # Load employees
        employees_file = dummy_path / "employees.json"
        if employees_file.exists():
            try:
                employees = json.loads(employees_file.read_text(encoding='utf-8'))
                for e in employees:
                    cursor.execute("""
                        INSERT OR REPLACE INTO employees 
                        (id, name, name_en, designation, branch, phone)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (e["id"], e["name"], e.get("name_en", ""),
                          e.get("designation", ""), e.get("branch", ""),
                          e.get("phone", "")))
                logger.info(f"Loaded {len(employees)} employees")
            except Exception as e:
                logger.error(f"Failed to load employees: {e}")
        else:
            logger.warning(f"Employees file not found: {employees_file}")
        
        conn.commit()
    
    # Survey operations
    def get_survey(self, survey_id: int) -> Optional[Survey]:
        """Get survey by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,))
            row = cursor.fetchone()
            if row:
                return Survey(**dict(row))
            return None
    
    def get_all_surveys(self) -> List[Survey]:
        """Get all surveys"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM surveys")
            return [Survey(**dict(row)) for row in cursor.fetchall()]
    
    # Question operations
    def get_questions(self, survey_id: int) -> List[Question]:
        """Get questions for a survey ordered by question_order"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, survey_id, question_order as 'order', text, text_ur, 
                       type, required, help_text
                FROM questions 
                WHERE survey_id = ? 
                ORDER BY question_order
            """, (survey_id,))
            return [Question(**dict(row)) for row in cursor.fetchall()]
    
    # Employee operations
    def get_employee(self, employee_id: int) -> Optional[Employee]:
        """Get employee by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
            row = cursor.fetchone()
            if row:
                return Employee(**dict(row))
            return None
    
    def get_all_employees(self) -> List[Employee]:
        """Get all employees"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees")
            return [Employee(**dict(row)) for row in cursor.fetchall()]
    
    # Response operations
    def save_response(
        self,
        survey_id: int,
        question_id: int,
        employee_id: int,
        answer_text: str,
        session_id: str = None
    ) -> int:
        """Save a survey response"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO responses (survey_id, question_id, employee_id, session_id, answer_text)
                VALUES (?, ?, ?, ?, ?)
            """, (survey_id, question_id, employee_id, session_id, answer_text))
            conn.commit()
            return cursor.lastrowid
    
    def get_responses(self, survey_id: int, employee_id: int) -> List[Dict]:
        """Get all responses for a survey and employee"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, q.text as question_text, q.text_ur as question_text_ur
                FROM responses r
                JOIN questions q ON r.question_id = q.id
                WHERE r.survey_id = ? AND r.employee_id = ?
                ORDER BY q.question_order
            """, (survey_id, employee_id))
            return [dict(row) for row in cursor.fetchall()]
    
    # Session operations
    def create_session(self, session_id: str, survey_id: int, employee_id: int):
        """Create a new survey session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (id, survey_id, employee_id)
                VALUES (?, ?, ?)
            """, (session_id, survey_id, employee_id))
            conn.commit()
    
    def complete_session(self, session_id: str):
        """Mark a session as completed"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions 
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (session_id,))
            conn.commit()


# Global database instance
db = Database()


def init_db():
    """Initialize database (call on startup)"""
    db.init_database()


def get_db() -> Database:
    """Get database instance"""
    return db
