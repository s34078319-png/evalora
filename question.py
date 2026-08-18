from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from app.schemas.question_schema import (
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    MCQQuestionCreate,
    ModelAnswerQuestionCreate
)

from app.crud.question_crud import (
    create_question,
    get_question_by_id,
    get_section_questions,
    get_next_question_order,
    update_question,
    delete_question
)

from app.crud.assessment_crud import (
    get_assessment_by_id
)

from app.crud.section_crud import (
    get_section_by_id
)

from app.dependencies.auth_dependencies import (
    require_teacher
)


router = APIRouter(
    prefix="/teacher",
    tags=["Teacher Questions"]
)


# ==========================================================
# SERIALIZE QUESTION
# ==========================================================

def serialize_question(
    question: dict
):

    return {

        "id":
            str(
                question["_id"]
            ),

        "assessment_id":
            question["assessment_id"],

        "section_id":
            question["section_id"],

        "question_type":
            question["question_type"],

        "question_text":
            question["question_text"],

        "marks":
            question["marks"],

        "negative_marks":
            question["negative_marks"],

        "options":
            question.get(
                "options"
            ),

        "expected_answer":
            question.get(
                "expected_answer"
            ),

        "model_answer_text":
            question.get(
                "model_answer_text"
            ),

        "model_answer_pdf_url":
            question.get(
                "model_answer_pdf_url"
            ),

        "order":
            question["order"],

        "created_at":
            question["created_at"],

        "updated_at":
            question["updated_at"]
    }


# ==========================================================
# VALIDATE TEACHER OWNS DRAFT ASSESSMENT
# ==========================================================

def validate_draft_assessment(
    assessment_id: str,
    teacher_id: str
):

    assessment = get_assessment_by_id(
        assessment_id
    )

    if not assessment:

        raise HTTPException(

            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Assessment not found."
        )

    if assessment["teacher_id"] != teacher_id:

        raise HTTPException(

            status_code=
                status.HTTP_403_FORBIDDEN,

            detail=
                "You do not have access to this assessment."
        )

    if assessment["status"] != "DRAFT":

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Questions can only be modified "
                "while the assessment is in DRAFT status."
        )

    return assessment


# ==========================================================
# VALIDATE SECTION
# ==========================================================

def validate_section(
    section_id: str,
    assessment_id: str
):

    section = get_section_by_id(
        section_id
    )

    if not section:

        raise HTTPException(

            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Section not found."
        )

    if section["assessment_id"] != assessment_id:

        raise HTTPException(

            status_code=
                status.HTTP_403_FORBIDDEN,

            detail=
                "This section does not belong "
                "to this assessment."
        )

    return section


# ==========================================================
# CREATE QUESTION
# ==========================================================

@router.post(
    "/assessments/{assessment_id}"
    "/sections/{section_id}"
    "/questions",

    response_model=QuestionResponse,

    status_code=
        status.HTTP_201_CREATED
)
def create_new_question(

    assessment_id: str,

    section_id: str,

    data: QuestionCreate,

    current_teacher: dict = Depends(
        require_teacher
    )
):

    teacher_id = str(
        current_teacher["_id"]
    )

    # ------------------------------------------------------
    # VALIDATE ASSESSMENT
    # ------------------------------------------------------

    validate_draft_assessment(

        assessment_id,

        teacher_id
    )

    # ------------------------------------------------------
    # VALIDATE SECTION
    # ------------------------------------------------------

    section = validate_section(

        section_id,

        assessment_id
    )

    # ------------------------------------------------------
    # ENSURE QUESTION TYPE MATCHES SECTION
    # ------------------------------------------------------

    if (
        data.question_type.value
        != section["section_type"]
    ):

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=(
                "Question type must match "
                "the section type."
            )
        )

    # ======================================================
    # PREPARE QUESTION DATA
    # ======================================================

    question_data = {

        "assessment_id":
            assessment_id,

        "section_id":
            section_id,

        "question_type":
            data.question_type.value,

        "question_text":
            data.question_text,

        "marks":
            data.marks,

        "negative_marks":
            data.negative_marks,

        "order":
            get_next_question_order(
                section_id
            )
    }

    # ======================================================
    # MCQ
    # ======================================================

    if isinstance(
        data,
        MCQQuestionCreate
    ):

        question_data.update({

            "options": [

                option.model_dump()

                for option in data.options
            ],

            "expected_answer":
                data.expected_answer,

            # ------------------------------------------------
            # MCQ NEVER HAS MODEL ANSWER
            # ------------------------------------------------

            "model_answer_text":
                None,

            "model_answer_pdf_url":
                None
        })

    # ======================================================
    # DESCRIPTIVE / PDF
    # ======================================================

    elif isinstance(
        data,
        ModelAnswerQuestionCreate
    ):

        question_data.update({

            # ------------------------------------------------
            # DESCRIPTIVE/PDF HAS NO MCQ DATA
            # ------------------------------------------------

            "options":
                None,

            "expected_answer":
                None,

            # ------------------------------------------------
            # EXACTLY ONE MODEL ANSWER
            # ------------------------------------------------

            "model_answer_text":
                data.model_answer_text,

            "model_answer_pdf_url":
                data.model_answer_pdf_url
        })

    # ======================================================
    # SAFETY CHECK
    # ======================================================

    else:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Invalid question type."
        )

    # ======================================================
    # CREATE
    # ======================================================

    question = create_question(
        question_data
    )

    return serialize_question(
        question
    )


# ==========================================================
# GET QUESTIONS
# ==========================================================

@router.get(
    "/assessments/{assessment_id}"
    "/sections/{section_id}"
    "/questions",

    response_model=list[QuestionResponse]
)
def get_questions(

    assessment_id: str,

    section_id: str,

    current_teacher: dict = Depends(
        require_teacher
    )
):

    teacher_id = str(
        current_teacher["_id"]
    )

    # ------------------------------------------------------
    # ASSESSMENT
    # ------------------------------------------------------

    assessment = get_assessment_by_id(
        assessment_id
    )

    if not assessment:

        raise HTTPException(

            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Assessment not found."
        )

    if assessment["teacher_id"] != teacher_id:

        raise HTTPException(

            status_code=
                status.HTTP_403_FORBIDDEN,

            detail=
                "You do not have access to this assessment."
        )

    # ------------------------------------------------------
    # SECTION
    # ------------------------------------------------------

    validate_section(

        section_id,

        assessment_id
    )

    # ------------------------------------------------------
    # QUESTIONS
    # ------------------------------------------------------

    questions = get_section_questions(
        section_id
    )

    return [

        serialize_question(
            question
        )

        for question in questions
    ]


# ==========================================================
# GET ONE QUESTION
# ==========================================================

@router.get(
    "/assessments/{assessment_id}"
    "/sections/{section_id}"
    "/questions/{question_id}",

    response_model=QuestionResponse
)
def get_one_question(

    assessment_id: str,

    section_id: str,

    question_id: str,

    current_teacher: dict = Depends(
        require_teacher
    )
):

    teacher_id = str(
        current_teacher["_id"]
    )

    # ------------------------------------------------------
    # ASSESSMENT
    # ------------------------------------------------------

    assessment = get_assessment_by_id(
        assessment_id
    )

    if not assessment:

        raise HTTPException(

            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Assessment not found."
        )

    if assessment["teacher_id"] != teacher_id:

        raise HTTPException(

            status_code=
                status.HTTP_403_FORBIDDEN,

            detail=
                "You do not have access to this assessment."
        )

    # ------------------------------------------------------
    # SECTION
    # ------------------------------------------------------

    validate_section(

        section_id,

        assessment_id
    )

    # ------------------------------------------------------
    # QUESTION
    # ------------------------------------------------------

    question = get_question_by_id(
        question_id
    )

    if not question:

        raise HTTPException(

            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Question not found."
        )

    if question["section_id"] != section_id:

        raise HTTPException(

            status_code=
                status.HTTP_403_FORBIDDEN,

            detail=
                "Question does not belong to this section."
        )

    return serialize_question(
        question
    )


# ==========================================================
# UPDATE QUESTION
# ==========================================================

@router.put(
    "/assessments/{assessment_id}"
    "/sections/{section_id}"
    "/questions/{question_id}",

    response_model=QuestionResponse
)
def update_existing_question(

    assessment_id: str,

    section_id: str,

    question_id: str,

    data: QuestionUpdate,

    current_teacher: dict = Depends(
        require_teacher
    )
):

    teacher_id = str(
        current_teacher["_id"]
    )

    # ------------------------------------------------------
    # ASSESSMENT MUST BE DRAFT
    # ------------------------------------------------------

    validate_draft_assessment(

        assessment_id,

        teacher_id
    )

    # ------------------------------------------------------
    # SECTION
    # ------------------------------------------------------

    section = validate_section(

        section_id,

        assessment_id
    )

    # ------------------------------------------------------
    # QUESTION
    # ------------------------------------------------------

    question = get_question_by_id(
        question_id
    )

    if not question:

        raise HTTPException(

            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Question not found."
        )

    if question["section_id"] != section_id:

        raise HTTPException(

            status_code=
                status.HTTP_403_FORBIDDEN,

            detail=
                "Question does not belong to this section."
        )

    # ======================================================
    # PREPARE UPDATES
    # ======================================================

    updates = data.model_dump(
        exclude_unset=True
    )

    # ------------------------------------------------------
    # OPTIONS
    # ------------------------------------------------------

    if "options" in updates:

        if updates["options"]:

            updates["options"] = [

                option
                if isinstance(
                    option,
                    dict
                )
                else option.model_dump()

                for option
                in updates["options"]
            ]

    # ======================================================
    # MCQ SECTION
    # ======================================================

    if section["section_type"] == "MCQ":

        # --------------------------------------------------
        # MODEL ANSWER NOT ALLOWED
        # --------------------------------------------------

        if (
            "model_answer_text"
            in updates
            or
            "model_answer_pdf_url"
            in updates
        ):

            raise HTTPException(

                status_code=
                    status.HTTP_400_BAD_REQUEST,

                detail=
                    "MCQ questions cannot have "
                    "a model answer."
            )

        # --------------------------------------------------
        # EXPECTED ANSWER
        # --------------------------------------------------

        if "expected_answer" in updates:

            if not updates["expected_answer"]:

                raise HTTPException(

                    status_code=
                        status.HTTP_422_UNPROCESSABLE_ENTITY,

                    detail=
                        "MCQ expected answer is required."
                )

            updates["expected_answer"] = (

                updates["expected_answer"]
                .strip()
                .upper()
            )

            if updates["expected_answer"] not in {

                "A",
                "B",
                "C",
                "D"

            }:

                raise HTTPException(

                    status_code=
                        status.HTTP_422_UNPROCESSABLE_ENTITY,

                    detail=
                        "MCQ expected answer must be A, B, C, or D."
                )

        # --------------------------------------------------
        # OPTIONS
        # --------------------------------------------------

        if "options" in updates:

            if not updates["options"]:

                raise HTTPException(

                    status_code=
                        status.HTTP_422_UNPROCESSABLE_ENTITY,

                    detail=
                        "MCQ must contain options."
                )

            if len(updates["options"]) != 4:

                raise HTTPException(

                    status_code=
                        status.HTTP_422_UNPROCESSABLE_ENTITY,

                    detail=
                        "MCQ must contain exactly four options."
                )

    # ======================================================
    # DESCRIPTIVE / PDF SECTION
    # ======================================================

    else:

        # --------------------------------------------------
        # MCQ FIELDS NOT ALLOWED
        # --------------------------------------------------

        if "options" in updates:

            raise HTTPException(

                status_code=
                    status.HTTP_400_BAD_REQUEST,

                detail=
                    "Only MCQ questions can contain options."
            )

        if "expected_answer" in updates:

            raise HTTPException(

                status_code=
                    status.HTTP_400_BAD_REQUEST,

                detail=
                    "Only MCQ questions can contain "
                    "an expected answer."
            )

        # --------------------------------------------------
        # MODEL ANSWER
        #
        # If teacher is changing either answer field,
        # make sure both are not supplied together.
        # --------------------------------------------------

        if (
            "model_answer_text"
            in updates
            and
            "model_answer_pdf_url"
            in updates
        ):

            if (
                updates["model_answer_text"]
                and
                updates["model_answer_pdf_url"]
            ):

                raise HTTPException(

                    status_code=
                        status.HTTP_422_UNPROCESSABLE_ENTITY,

                    detail=
                        "Provide either a typed model answer "
                        "or a model answer PDF, not both."
                )

    # ======================================================
    # UPDATE
    # ======================================================

    updated = update_question(

        question_id,

        section_id,

        updates
    )

    if not updated:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Question could not be updated."
        )

    return serialize_question(
        updated
    )


# ==========================================================
# DELETE QUESTION
# ==========================================================

@router.delete(
    "/assessments/{assessment_id}"
    "/sections/{section_id}"
    "/questions/{question_id}",

    status_code=
        status.HTTP_204_NO_CONTENT
)
def delete_existing_question(

    assessment_id: str,

    section_id: str,

    question_id: str,

    current_teacher: dict = Depends(
        require_teacher
    )
):

    teacher_id = str(
        current_teacher["_id"]
    )

    # ------------------------------------------------------
    # ASSESSMENT MUST BE DRAFT
    # ------------------------------------------------------

    validate_draft_assessment(

        assessment_id,

        teacher_id
    )

    # ------------------------------------------------------
    # SECTION
    # ------------------------------------------------------

    validate_section(

        section_id,

        assessment_id
    )

    # ------------------------------------------------------
    # QUESTION
    # ------------------------------------------------------

    question = get_question_by_id(
        question_id
    )

    if not question:

        raise HTTPException(

            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Question not found."
        )

    if question["section_id"] != section_id:

        raise HTTPException(

            status_code=
                status.HTTP_403_FORBIDDEN,

            detail=
                "Question does not belong to this section."
        )

    # ------------------------------------------------------
    # DELETE
    # ------------------------------------------------------

    deleted = delete_question(

        question_id,

        section_id
    )

    if not deleted:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Question could not be deleted."
        )

    return None