from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ==========================================================
# START ASSESSMENT RESPONSE
# ==========================================================

class StartAssessmentResponse(BaseModel):

    attempt_id: str

    session_id: str

    assessment_id: str

    # Timer has NOT started before face verification.
    started_at: Optional[datetime] = None

    deadline: Optional[datetime] = None

    current_section_order: int

    completed: bool

    active: bool

    face_verified: bool


# ==========================================================
# AVAILABLE ASSESSMENT
# ==========================================================

class StudentAssessmentResponse(BaseModel):

    id: str

    title: str

    description: Optional[str] = None

    branch: str

    semester: int

    opening_time: datetime

    closing_time: datetime

    duration_minutes: int

    status: str

    published_at: Optional[datetime] = None

    attempt_started: bool

    attempt_completed: bool


# ==========================================================
# ATTEMPT RESPONSE
# ==========================================================

class AttemptResponse(BaseModel):

    id: str

    student_id: str

    assessment_id: str

    # These are None until face verification succeeds.
    started_at: Optional[datetime] = None

    deadline: Optional[datetime] = None

    current_section_order: int

    completed: bool

    submitted_at: Optional[datetime] = None

    completion_reason: Optional[str] = None

    created_at: datetime

    updated_at: datetime