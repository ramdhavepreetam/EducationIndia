from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

@dataclass
class ResponseData:
    question_no: int
    question_id: int
    selected_option: Optional[int]   # None = skipped
    correct_option: Optional[int]    # None if multi-answer question
    topic_id: int
    topic_name_en: str
    topic_name_mr: Optional[str]
    section_id: int
    section_label: str
    subject_en: str
    marks: int
    time_taken_seconds: Optional[int]
    selected_options: Optional[List[int]] = None
    is_multi_select: bool = False
    correct_options: Optional[List[int]] = None  # e.g. [1,3] for "1 OR 3" / "1 AND 3"

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


# ── Wrong Answers (used by parent dashboard + result page) ────────────────────

class OptionItemSchema(BaseModel):
    """One option (A/B/C/D) for a question."""
    option_no: int
    text_en: Optional[str] = None
    text_mr: Optional[str] = None
    image_url: Optional[str] = None
    is_correct: bool = False


class WrongAnswerItem(BaseModel):
    """One wrong question with full details for review."""
    question_no: int
    question_text_en: Optional[str] = None
    question_text_mr: Optional[str] = None
    question_image_url: Optional[str] = None
    selected_option: Optional[int] = None
    selected_options: Optional[List[int]] = None
    correct_option: Optional[int] = None
    correct_options: Optional[List[int]] = None
    is_multi_select: bool = False
    explanation_en: Optional[str] = None
    explanation_mr: Optional[str] = None
    section_subject_en: Optional[str] = None
    section_label: Optional[str] = None
    subject_mr: Optional[str] = None
    topic_name_en: Optional[str] = None
    topic_name_mr: Optional[str] = None
    options: List[OptionItemSchema] = []


class WrongAnswersSummary(BaseModel):
    """Summary of wrong answers for an attempt."""
    total_wrong: int
    total_skipped: int = 0
    items: List[WrongAnswerItem] = []
