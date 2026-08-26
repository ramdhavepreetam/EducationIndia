from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TeacherStudentSchema(BaseModel):
    id: UUID
    full_name: str
    email: Optional[str] = None
    std_class: Optional[int] = None
    medium: Optional[str] = None
    school_name: Optional[str] = None
    district: Optional[str] = None
    total_attempts: int = 0
    avg_percentage: Optional[float] = None
    last_attempt_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssignExamRequest(BaseModel):
    student_id: UUID
    exam_id: int
    max_attempts: int = Field(default=10, ge=1, le=50)


class AssignmentSchema(BaseModel):
    id: int
    exam_id: int
    student_id: UUID
    student_name: Optional[str] = None
    exam_title: Optional[str] = None
    paper_code: Optional[str] = None
    max_attempts: int
    attempts_used: int
    is_active: bool
    assigned_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StudentAttemptSummary(BaseModel):
    attempt_id: UUID
    exam_title: Optional[str] = None
    paper_code: Optional[str] = None
    status: str
    total_score: Optional[int] = None
    total_correct: Optional[int] = None
    total_wrong: Optional[int] = None
    total_skipped: Optional[int] = None
    percentage: Optional[float] = None
    grade: Optional[str] = None
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None


class StudentDetailSchema(BaseModel):
    id: UUID
    full_name: str
    email: Optional[str] = None
    std_class: Optional[int] = None
    medium: Optional[str] = None
    school_name: Optional[str] = None
    district: Optional[str] = None
    total_attempts: int = 0
    avg_percentage: Optional[float] = None
    best_percentage: Optional[float] = None
    last_attempt_at: Optional[datetime] = None
    assignments: list[AssignmentSchema] = []
    recent_attempts: list[StudentAttemptSummary] = []


class TeacherDashboardSchema(BaseModel):
    total_students_assigned: int = 0
    total_assignments_active: int = 0
    total_exams_available: int = 0
    recent_assignments: list[AssignmentSchema] = []
