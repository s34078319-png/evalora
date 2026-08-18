from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ==========================================================
# START SESSION RESPONSE
# ==========================================================

class StartSessionResponse(BaseModel):

    session_id: str

    attempt_id: str

    assessment_id: str

    # Timer has NOT started before face verification.
    started_at: Optional[datetime] = None

    deadline: Optional[datetime] = None

    current_section_order: int

    active: bool

    face_verified: bool


# ==========================================================
# SESSION RESPONSE
# ==========================================================

class SessionResponse(BaseModel):

    id: str

    attempt_id: str

    student_id: str

    assessment_id: str

    # These remain None until successful face verification.
    started_at: Optional[datetime] = None

    deadline: Optional[datetime] = None

    ended_at: Optional[datetime] = None

    active: bool

    face_verified: bool

    proctoring_flags: int

    current_section_order: int

    created_at: datetime

    updated_at: datetime