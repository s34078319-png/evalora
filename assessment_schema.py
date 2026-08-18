from datetime import datetime
from typing import Optional, Literal

from pydantic import (
    BaseModel,
    Field,
    model_validator
)

from app.constants.academic import (
    Branch,
    MIN_SEMESTER,
    MAX_SEMESTER
)


# ==========================================================
# ASSESSMENT CREATE
# ==========================================================

class AssessmentCreate(BaseModel):

    title: str = Field(
        min_length=3,
        max_length=200
    )

    description: Optional[str] = None

    # ------------------------------------------------------
    # TARGET STUDENTS
    # ------------------------------------------------------

    branch: Branch

    semester: int = Field(
        ge=MIN_SEMESTER,
        le=MAX_SEMESTER
    )

    # ------------------------------------------------------
    # TIMING
    # ------------------------------------------------------

    opening_time: datetime

    closing_time: datetime

    # Overall assessment duration.
    #
    # Example:
    #
    # 60 minutes overall
    #
    duration_minutes: int = Field(
        ge=1,
        le=600
    )

    # ------------------------------------------------------
    # PDF UPLOAD DURATION
    #
    # 0 means there is currently no PDF section.
    #
    # If a PDF section exists, publish validation will
    # require this value to be:
    #
    #     greater than 0
    #     less than duration_minutes
    #
    # Example:
    #
    # duration = 60
    # pdf upload = 20
    #
    # Remaining assessment time = 40 minutes
    # ------------------------------------------------------

    pdf_upload_duration_minutes: int = Field(
        ge=0,
        le=600
    )

    # ------------------------------------------------------
    # PROCTORING
    # ------------------------------------------------------

    max_proctoring_flags: int = Field(
        ge=1,
        le=100
    )

    # ======================================================
    # VALIDATE TIMES
    # ======================================================

    @model_validator(mode="after")
    def validate_times(self):

        if self.closing_time <= self.opening_time:

            raise ValueError(
                "Closing time must be after opening time."
            )

        # --------------------------------------------------
        # If PDF duration is greater than 0, it must be
        # smaller than the overall assessment duration.
        # --------------------------------------------------

        if (
            self.pdf_upload_duration_minutes > 0
            and
            self.pdf_upload_duration_minutes
            >= self.duration_minutes
        ):

            raise ValueError(
                "PDF upload duration must be greater than 0 "
                "and less than the overall assessment duration."
            )

        return self


# ==========================================================
# ASSESSMENT UPDATE
# ==========================================================

class AssessmentUpdate(BaseModel):

    title: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=200
    )

    description: Optional[str] = None

    branch: Optional[Branch] = None

    semester: Optional[int] = Field(
        default=None,
        ge=MIN_SEMESTER,
        le=MAX_SEMESTER
    )

    opening_time: Optional[datetime] = None

    closing_time: Optional[datetime] = None

    duration_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        le=600
    )

    pdf_upload_duration_minutes: Optional[int] = Field(
        default=None,
        ge=0,
        le=600
    )

    max_proctoring_flags: Optional[int] = Field(
        default=None,
        ge=1,
        le=100
    )

    # ======================================================
    # VALIDATE UPDATE DURATIONS
    # ======================================================

    @model_validator(mode="after")
    def validate_update_durations(self):

        # --------------------------------------------------
        # When both values are supplied in the same update,
        # validate them immediately.
        # --------------------------------------------------

        if (
            self.pdf_upload_duration_minutes is not None
            and
            self.duration_minutes is not None
        ):

            if (
                self.pdf_upload_duration_minutes > 0
                and
                self.pdf_upload_duration_minutes
                >= self.duration_minutes
            ):

                raise ValueError(
                    "PDF upload duration must be greater than 0 "
                    "and less than the overall assessment duration."
                )

        return self


# ==========================================================
# ASSESSMENT RESPONSE
# ==========================================================

class AssessmentResponse(BaseModel):

    id: str

    teacher_id: str

    title: str

    description: Optional[str] = None

    # ------------------------------------------------------
    # TARGET
    # ------------------------------------------------------

    branch: Branch

    semester: int

    # ------------------------------------------------------
    # TIMING
    # ------------------------------------------------------

    opening_time: datetime

    closing_time: datetime

    duration_minutes: int

    pdf_upload_duration_minutes: int

    # ------------------------------------------------------
    # PROCTORING
    # ------------------------------------------------------

    max_proctoring_flags: int

    # ------------------------------------------------------
    # ANSWER EVALUATION
    #
    # Teacher does NOT provide these values.
    # Evalora controls them internally.
    # ------------------------------------------------------

    keyword_matching_weight: float

    semantic_similarity_weight: float

    # ------------------------------------------------------
    # STATUS
    # ------------------------------------------------------

    status: Literal[
        "DRAFT",
        "PUBLISHED",
        "CLOSED"
    ]

    # ------------------------------------------------------
    # TIMESTAMPS
    # ------------------------------------------------------

    created_at: datetime

    updated_at: datetime

    published_at: Optional[datetime] = None