from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

@dataclass
class ResponseData:
    question_no: int
    question_id: int
    selected_option: Optional[int]   # None = skipped
    correct_option: int
    topic_id: int
    topic_name_en: str
    topic_name_mr: Optional[str]
    section_id: int
    section_label: str
    subject_en: str
    marks: int
    time_taken_seconds: Optional[int]

class FastSlowItem(BaseModel):
    question_no: int
    seconds: int

class TimeAnalysisSchema(BaseModel):
    total_time_seconds: int
    avg_per_question: float
    fastest: Optional[FastSlowItem]
    slowest: Optional[FastSlowItem]
    skipped_count: int
    overtime_questions: List[int]

class SectionScoreSchema(BaseModel):
    section_id: int
    label: str
    subject_en: str
    subject_mr: Optional[str] = None
    correct: int
    total_questions: int
    score: int
    total_marks: int
    percentage: float

class TopicScoreSchema(BaseModel):
    topic_id: int
    name_en: str
    name_mr: Optional[str] = None
    correct: int
    total: int
    percentage: float
    status: str

class ReportSchema(BaseModel):
    attempt_id: str
    exam_id: int
    status: str
    attempt_number: int
    submitted_at: str
    total_score: int
    total_correct: int
    total_wrong: int
    total_skipped: int
    percentage: float
    grade: str
    section_scores: List[Any]
    topic_scores: List[Any]
    time_analysis: Any
    recommendations: List[str]
    tier: str = "paid"
    upgrade_prompt: bool = False


class ReportFreeSchema(BaseModel):
    """Free-tier response — score summary only, no detailed analysis."""
    attempt_id: str
    exam_id: int
    status: str
    attempt_number: int
    submitted_at: str
    total_score: int
    total_correct: int
    total_wrong: int
    total_skipped: int
    percentage: float
    grade: str
    tier: str = "free"
    upgrade_prompt: bool = True
