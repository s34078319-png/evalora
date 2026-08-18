from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from app.constants.academic import Branch


# ==========================================================
# STUDENT ASSESSMENT STATUS
# ==========================================================

class StudentAssessmentStatus(str, Enum):

    UPCOMING = "UPCOMING"

    LIVE = "LIVE"

    CLOSED = "CLOSED"


# ==========================================================
# STUDENT SECTION RESPONSE
# ==========================================================

class StudentSectionResponse(BaseModel):

    id: str

    assessment_id: str

    title: str

    section_type: str

    order: int


# ==========================================================
# STUDENT ASSESSMENT LIST RESPONSE
# ==========================================================

class StudentAssessmentListResponse(BaseModel):

    id: str

    title: str

    description: Optional[str] = None

    branch: Branch

    semester: int

    opening_time: datetime

    closing_time: datetime

    duration_minutes: int

    max_proctoring_flags: int

    status: StudentAssessmentStatus


# ==========================================================
# STUDENT ASSESSMENT DETAIL RESPONSE
# ==========================================================

class StudentAssessmentDetailResponse(BaseModel):

    id: str

    title: str

    description: Optional[str] = None

    branch: Branch

    semester: int

    opening_time: datetime

    closing_time: datetime

    duration_minutes: int

    max_proctoring_flags: int

    status: StudentAssessmentStatus

    sections: list[StudentSectionResponse]