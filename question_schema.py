from enum import Enum
from typing import Optional, Union, Literal

from pydantic import (
    BaseModel,
    Field,
    model_validator
)


# ==========================================================
# QUESTION TYPE
# ==========================================================

class QuestionType(str, Enum):

    MCQ = "MCQ"

    DESCRIPTIVE = "DESCRIPTIVE"

    PDF = "PDF"


# ==========================================================
# MCQ OPTION
# ==========================================================

class MCQOption(BaseModel):

    option: str = Field(
        min_length=1,
        max_length=1
    )

    text: str = Field(
        min_length=1,
        max_length=1000
    )

    @model_validator(mode="after")
    def validate_option(self):

        self.option = self.option.upper()

        if self.option not in {
            "A",
            "B",
            "C",
            "D"
        }:

            raise ValueError(
                "MCQ option must be A, B, C, or D."
            )

        return self


# ==========================================================
# BASE QUESTION FIELDS
# ==========================================================

class QuestionBase(BaseModel):

    question_text: str = Field(
        min_length=1,
        max_length=10000
    )

    marks: float = Field(
        gt=0
    )

    negative_marks: float = Field(
        ge=0
    )


# ==========================================================
# MCQ QUESTION
# ==========================================================

class MCQQuestionCreate(QuestionBase):

    question_type: Literal[
        QuestionType.MCQ
    ]

    options: list[MCQOption]

    expected_answer: str

    @model_validator(mode="after")
    def validate_mcq(self):

        # --------------------------------------------------
        # EXACTLY FOUR OPTIONS
        # --------------------------------------------------

        if len(self.options) != 4:

            raise ValueError(
                "MCQ must contain exactly four options."
            )

        # --------------------------------------------------
        # REQUIRED A B C D
        # --------------------------------------------------

        option_names = {
            option.option.upper()
            for option in self.options
        }

        if option_names != {
            "A",
            "B",
            "C",
            "D"
        }:

            raise ValueError(
                "MCQ options must contain exactly A, B, C, and D."
            )

        # --------------------------------------------------
        # EXPECTED ANSWER
        # --------------------------------------------------

        self.expected_answer = (
            self.expected_answer
            .strip()
            .upper()
        )

        if self.expected_answer not in {
            "A",
            "B",
            "C",
            "D"
        }:

            raise ValueError(
                "MCQ expected answer must be A, B, C, or D."
            )

        return self


# ==========================================================
# DESCRIPTIVE / PDF QUESTION
# ==========================================================

class ModelAnswerQuestionCreate(QuestionBase):

    question_type: Literal[
        QuestionType.DESCRIPTIVE,
        QuestionType.PDF
    ]

    # ------------------------------------------------------
    # TEACHER MODEL ANSWER
    #
    # Exactly ONE must be supplied:
    #
    # 1. Typed answer
    # OR
    # 2. Uploaded PDF URL
    # ------------------------------------------------------

    model_answer_text: Optional[str] = None

    model_answer_pdf_url: Optional[str] = None

    @model_validator(mode="after")
    def validate_model_answer(self):

        has_text = bool(
            self.model_answer_text
            and self.model_answer_text.strip()
        )

        has_pdf = bool(
            self.model_answer_pdf_url
            and self.model_answer_pdf_url.strip()
        )

        # --------------------------------------------------
        # NEITHER
        # --------------------------------------------------

        if not has_text and not has_pdf:

            raise ValueError(
                "Provide either a typed model answer "
                "or upload a model answer PDF."
            )

        # --------------------------------------------------
        # BOTH
        # --------------------------------------------------

        if has_text and has_pdf:

            raise ValueError(
                "Provide either a typed model answer "
                "or upload a model answer PDF, not both."
            )

        return self


# ==========================================================
# CREATE QUESTION
# ==========================================================

QuestionCreate = Union[
    MCQQuestionCreate,
    ModelAnswerQuestionCreate
]


# ==========================================================
# UPDATE QUESTION
# ==========================================================

class QuestionUpdate(BaseModel):

    question_text: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=10000
    )

    marks: Optional[float] = Field(
        default=None,
        gt=0
    )

    negative_marks: Optional[float] = Field(
        default=None,
        ge=0
    )

    # ------------------------------------------------------
    # MCQ FIELDS
    # ------------------------------------------------------

    options: Optional[list[MCQOption]] = None

    expected_answer: Optional[str] = None

    # ------------------------------------------------------
    # DESCRIPTIVE / PDF MODEL ANSWER
    # ------------------------------------------------------

    model_answer_text: Optional[str] = None

    model_answer_pdf_url: Optional[str] = None

    @model_validator(mode="after")
    def validate_update(self):

        # --------------------------------------------------
        # MCQ EXPECTED ANSWER
        # --------------------------------------------------

        if self.expected_answer is not None:

            answer = (
                self.expected_answer
                .strip()
                .upper()
            )

            if answer not in {
                "A",
                "B",
                "C",
                "D"
            }:

                raise ValueError(
                    "MCQ expected answer must be A, B, C, or D."
                )

            self.expected_answer = answer

        # --------------------------------------------------
        # MODEL ANSWER
        #
        # If both are explicitly supplied, reject.
        # --------------------------------------------------

        has_text = bool(
            self.model_answer_text
            and self.model_answer_text.strip()
        )

        has_pdf = bool(
            self.model_answer_pdf_url
            and self.model_answer_pdf_url.strip()
        )

        if has_text and has_pdf:

            raise ValueError(
                "Provide either a typed model answer "
                "or a model answer PDF, not both."
            )

        return self


# ==========================================================
# QUESTION RESPONSE
# ==========================================================

class QuestionResponse(BaseModel):

    id: str

    assessment_id: str

    section_id: str

    question_type: QuestionType

    question_text: str

    marks: float

    negative_marks: float

    options: Optional[list[MCQOption]] = None

    expected_answer: Optional[str] = None

    model_answer_text: Optional[str] = None

    model_answer_pdf_url: Optional[str] = None

    order: int

    created_at: object

    updated_at: object