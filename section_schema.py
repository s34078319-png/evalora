from enum import Enum
from typing import Optional

from pydantic import (
    BaseModel,
    Field
)


# ==========================================================
# SECTION TYPE
# ==========================================================

class SectionType(str, Enum):

    MCQ = "MCQ"

    DESCRIPTIVE = "DESCRIPTIVE"

    PDF = "PDF"


# ==========================================================
# CREATE SECTION
# ==========================================================

class SectionCreate(BaseModel):

    title: str = Field(
        min_length=1,
        max_length=200
    )

    section_type: SectionType


# ==========================================================
# UPDATE SECTION
# ==========================================================

class SectionUpdate(BaseModel):

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200
    )


# ==========================================================
# SECTION RESPONSE
# ==========================================================

class SectionResponse(BaseModel):

    id: str

    assessment_id: str

    title: str

    section_type: SectionType

    order: int

    created_at: object

    updated_at: object