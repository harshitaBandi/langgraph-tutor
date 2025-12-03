from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class QuestionType(str, Enum):
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    CODING = "coding"


class WebSocketMessageType(str, Enum):
    SESSION_START = "session.start"
    TUTOR_STEP = "tutor.step"
    TUTOR_COMPLETE = "tutor.complete"
    ASSESSMENT_READY = "assessment.ready"
    ERROR = "error"
    GRADING_COMPLETE = "grading.complete"
    RETRY_PROMPT = "retry.prompt"


class Question(BaseModel):
    id: str
    type: QuestionType
    question: str
    options: Optional[List[str]] = None
    expected_answer: str
    points: int = Field(default=10, ge=1, le=100)
    keywords: Optional[List[str]] = None
    test_cases: Optional[List[Dict[str, Any]]] = None
    rubric: Optional[List[str]] = None


class Assessment(BaseModel):
    id: str
    topic: str
    questions: List[Question]
    total_points: int
    pass_threshold: float = Field(default=0.7, ge=0, le=1)
    time_limit_minutes: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)


class AnswerSubmission(BaseModel):
    question_id: str
    answer: str


class AssessmentSubmission(BaseModel):
    assessment_id: str
    answers: List[AnswerSubmission]
    submitted_at: datetime = Field(default_factory=datetime.now)


class QuestionGrade(BaseModel):
    question_id: str
    score: float
    max_score: float
    is_correct: bool
    feedback: str
    remediation_steps: Optional[List[int]] = None


class GradeReport(BaseModel):
    assessment_id: str
    total_score: float
    max_score: float
    percentage: float
    passed: bool
    question_grades: List[QuestionGrade]
    feedback: str
    generated_at: datetime = Field(default_factory=datetime.now)


class WebSocketMessage(BaseModel):
    type: WebSocketMessageType
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class TutorStep(BaseModel):
    step_number: int
    title: str
    content: str
    is_complete: bool = False


class SessionState(BaseModel):
    topic: str
    steps_completed: List[TutorStep] = Field(default_factory=list)
    current_step: int = 0
    assessment_generated: bool = False
    assessment: Optional[Assessment] = None
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    session_id: str


class AssessmentGenerationRequest(BaseModel):
    topic: str
    question_count: int = Field(default=5, ge=3, le=10)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    question_types: Optional[List[QuestionType]] = None
    teaching_steps: Optional[List[Dict[str, Any]]] = None


class RetakeRequest(BaseModel):
    assessment_id: str
    generate_new: bool = True

