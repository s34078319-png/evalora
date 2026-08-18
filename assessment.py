
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from app.schemas.assessment_schema import (
    AssessmentCreate,
    AssessmentUpdate,
    AssessmentResponse
)

from app.crud.assessment_crud import (
    create_assessment,
    get_assessment_by_id,
    get_teacher_assessments,
    update_assessment,
    delete_assessment,
    publish_assessment
)

from app.crud.section_crud import (
    get_assessment_sections
)

from app.dependencies.auth_dependencies import (
    require_teacher
)


router = APIRouter(
    prefix="/teacher/assessments",
    tags=["Teacher Assessments"]
)


# ==========================================================
# SERIALIZE ASSESSMENT
# ==========================================================

def serialize_assessment(
    assessment: dict
):

    return {

        "id":
            str(
                assessment["_id"]
            ),

        "teacher_id":
            assessment["teacher_id"],

        "title":
            assessment["title"],

        "description":
            assessment.get(
                "description"
            ),

        # --------------------------------------------------
        # TARGET
        # --------------------------------------------------

        "branch":
            assessment["branch"],

        "semester":
            assessment["semester"],

        # --------------------------------------------------
        # TIMING
        # --------------------------------------------------

        "opening_time":
            assessment["opening_time"],

        "closing_time":
            assessment["closing_time"],

        "duration_minutes":
            assessment["duration_minutes"],

        # --------------------------------------------------
        # PDF UPLOAD DURATION
        #
        # Old assessments that do not have this field
        # are treated as having 0 minutes.
        # --------------------------------------------------

        "pdf_upload_duration_minutes":
            assessment.get(
                "pdf_upload_duration_minutes",
                0
            ),

        # --------------------------------------------------
        # PROCTORING
        # --------------------------------------------------

        "max_proctoring_flags":
            assessment["max_proctoring_flags"],

        # --------------------------------------------------
        # ANSWER EVALUATION
        # --------------------------------------------------

        "keyword_matching_weight":
            assessment[
                "keyword_matching_weight"
            ],

        "semantic_similarity_weight":
            assessment[
                "semantic_similarity_weight"
            ],

        # --------------------------------------------------
        # STATUS
        # --------------------------------------------------

        "status":
            assessment["status"],

        # --------------------------------------------------
        # TIMESTAMPS
        # --------------------------------------------------

        "created_at":
            assessment["created_at"],

        "updated_at":
            assessment["updated_at"],

        "published_at":
            assessment.get(
                "published_at"
            )
    }


# ==========================================================
# CREATE ASSESSMENT
# ==========================================================

@router.post(
    "",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_assessment(

    data: AssessmentCreate,

    current_teacher: dict = Depends(
        require_teacher
    )
):

    assessment = create_assessment(

        {
            "teacher_id":
                str(
                    current_teacher["_id"]
                ),

            "title":
                data.title,

            "description":
                data.description,

            "branch":
                data.branch.value,

            "semester":
                data.semester,

            "opening_time":
                data.opening_time,

            "closing_time":
                data.closing_time,

            "duration_minutes":
                data.duration_minutes,

            # --------------------------------------------------
            # PDF UPLOAD DURATION
            # --------------------------------------------------

            "pdf_upload_duration_minutes":
                data.pdf_upload_duration_minutes,

            "max_proctoring_flags":
                data.max_proctoring_flags
        }
    )

    return serialize_assessment(
        assessment
    )


# ==========================================================
# GET MY ASSESSMENTS
# ==========================================================

@router.get(
    "",
    response_model=list[AssessmentResponse]
)
def get_my_assessments(

    current_teacher: dict = Depends(
        require_teacher
    )
):

    assessments = get_teacher_assessments(

        str(
            current_teacher["_id"]
        )
    )

    return [

        serialize_assessment(
            assessment
        )

        for assessment in assessments
    ]


# ==========================================================
# GET ONE OF MY ASSESSMENTS
# ==========================================================

@router.get(
    "/{assessment_id}",
    response_model=AssessmentResponse
)
def get_my_assessment(

    assessment_id: str,

    current_teacher: dict = Depends(
        require_teacher
    )
):

    assessment = get_assessment_by_id(
        assessment_id
    )

    if not assessment:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found."
        )

    if assessment["teacher_id"] != str(
        current_teacher["_id"]
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have access "
                "to this assessment."
            )
        )

    return serialize_assessment(
        assessment
    )


# ==========================================================
# UPDATE DRAFT ASSESSMENT
# ==========================================================
#
# Only DRAFT assessments can be edited.
#
# Important:
#
# If teacher changes ONLY pdf_upload_duration_minutes,
# we compare it against the existing duration_minutes.
#
# If teacher changes ONLY duration_minutes,
# we compare the existing pdf_upload_duration_minutes
# against the new duration_minutes.
#
# Therefore both cases are validated correctly.
# ==========================================================

@router.put(
    "/{assessment_id}",
    response_model=AssessmentResponse
)
def update_my_assessment(

    assessment_id: str,

    data: AssessmentUpdate,

    current_teacher: dict = Depends(
        require_teacher
    )
):

    # ======================================================
    # GET ASSESSMENT
    # ======================================================

    assessment = get_assessment_by_id(
        assessment_id
    )

    if not assessment:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found."
        )

    # ======================================================
    # TEACHER OWNERSHIP
    # ======================================================

    if assessment["teacher_id"] != str(
        current_teacher["_id"]
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have access "
                "to this assessment."
            )
        )

    # ======================================================
    # ONLY DRAFT CAN BE UPDATED
    # ======================================================

    if assessment["status"] != "DRAFT":

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only draft assessments "
                "can be edited."
            )
        )

    # ======================================================
    # GET UPDATE DATA
    # ======================================================

    updates = data.model_dump(
        exclude_unset=True
    )

    # ------------------------------------------------------
    # Nothing changed
    # ------------------------------------------------------

    if not updates:

        return serialize_assessment(
            assessment
        )

    # ======================================================
    # BRANCH ENUM -> STRING
    # ======================================================

    if "branch" in updates:

        updates["branch"] = (
            updates["branch"].value
        )

    # ======================================================
    # DETERMINE FINAL DURATION VALUES
    # ======================================================
    #
    # We need the values that will actually exist after
    # the update.
    #
    # Example 1:
    #
    # Existing:
    # duration = 60
    # pdf = 10
    #
    # Update:
    # pdf = 20
    #
    # Final:
    # duration = 60
    # pdf = 20
    #
    # Example 2:
    #
    # Existing:
    # duration = 60
    # pdf = 50
    #
    # Update:
    # duration = 40
    #
    # Final:
    # duration = 40
    # pdf = 50
    #
    # This second case must fail.
    # ======================================================

    final_duration = updates.get(
        "duration_minutes",
        assessment["duration_minutes"]
    )

    final_pdf_duration = updates.get(
        "pdf_upload_duration_minutes",
        assessment.get(
            "pdf_upload_duration_minutes",
            0
        )
    )

    # ======================================================
    # VALIDATE PDF DURATION
    # ======================================================
    #
    # PDF duration of 0 is allowed here because the
    # assessment may currently have no PDF section.
    #
    # If PDF duration > 0:
    #
    #     pdf duration < overall duration
    #
    # Publish endpoint will additionally check whether
    # a PDF section actually exists.
    # ======================================================

    if final_pdf_duration > 0:

        if final_pdf_duration >= final_duration:

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "PDF upload duration must be "
                    "greater than 0 and less than "
                    "the overall assessment duration."
                )
            )

    # ======================================================
    # UPDATE DATABASE
    # ======================================================

    updated = update_assessment(

        assessment_id,

        str(
            current_teacher["_id"]
        ),

        updates
    )

    if not updated:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Assessment could not "
                "be updated."
            )
        )

    # ======================================================
    # RESPONSE
    # ======================================================

    return serialize_assessment(
        updated
    )


# ==========================================================
# DELETE ASSESSMENT
# ==========================================================
#
# Teacher can delete only DRAFT assessments.
#
# Published assessments cannot be deleted.
# ==========================================================

@router.delete(
    "/{assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_my_assessment(

    assessment_id: str,

    current_teacher: dict = Depends(
        require_teacher
    )
):

    # ======================================================
    # GET ASSESSMENT
    # ======================================================

    assessment = get_assessment_by_id(
        assessment_id
    )

    if not assessment:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found."
        )

    # ======================================================
    # TEACHER OWNERSHIP
    # ======================================================

    if assessment["teacher_id"] != str(
        current_teacher["_id"]
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have access "
                "to this assessment."
            )
        )

    # ======================================================
    # ONLY DRAFT CAN BE DELETED
    # ======================================================

    if assessment["status"] != "DRAFT":

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Published assessments "
                "cannot be deleted."
            )
        )

    # ======================================================
    # DELETE ASSESSMENT
    # ======================================================

    deleted = delete_assessment(

        assessment_id,

        str(
            current_teacher["_id"]
        )
    )

    if not deleted:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Assessment could not "
                "be deleted."
            )
        )

    # ======================================================
    # DELETE SECTIONS
    # ======================================================
    #
    # Questions are handled by the question module.
    # ======================================================

    from app.database.mongodb import db

    db.sections.delete_many(
        {
            "assessment_id":
                assessment_id
        }
    )

    return None


# ==========================================================
# PUBLISH ASSESSMENT
# ==========================================================
#
# Assessment can be published ONLY when:
#
# 1. At least one section exists.
#
# 2. Every section contains at least one question.
#
# 3. Section order is:
#
#       MCQ -> DESCRIPTIVE -> PDF
#
#    Missing types are allowed.
#
# 4. PDF duration rules are satisfied.
#
# ==========================================================

@router.post(
    "/{assessment_id}/publish",
    response_model=AssessmentResponse
)
def publish_my_assessment(

    assessment_id: str,

    current_teacher: dict = Depends(
        require_teacher
    )
):

    # ======================================================
    # GET ASSESSMENT
    # ======================================================

    assessment = get_assessment_by_id(
        assessment_id
    )

    if not assessment:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found."
        )

    # ======================================================
    # TEACHER OWNERSHIP
    # ======================================================

    if assessment["teacher_id"] != str(
        current_teacher["_id"]
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have access "
                "to this assessment."
            )
        )

    # ======================================================
    # ONLY DRAFT CAN BE PUBLISHED
    # ======================================================

    if assessment["status"] != "DRAFT":

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only draft assessments "
                "can be published."
            )
        )

    # ======================================================
    # GET SECTIONS
    # ======================================================

    sections = get_assessment_sections(
        assessment_id
    )

    # ======================================================
    # MUST HAVE AT LEAST ONE SECTION
    # ======================================================

    if not sections:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Assessment must contain "
                "at least one section before "
                "it can be published."
            )
        )

    # ======================================================
    # VALIDATE SECTION ORDER
    # ======================================================

    priority = {

        "MCQ": 1,

        "DESCRIPTIVE": 2,

        "PDF": 3
    }

    previous_priority = 0

    for section in sections:

        section_type = section[
            "section_type"
        ]

        current_priority = priority.get(
            section_type
        )

        if current_priority is None:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid section type."
                )
            )

        if current_priority < previous_priority:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid section order. "
                    "Sections must follow "
                    "MCQ -> DESCRIPTIVE -> PDF."
                )
            )

        previous_priority = (
            current_priority
        )

    # ======================================================
    # DETERMINE WHETHER PDF SECTION EXISTS
    # ======================================================

    has_pdf_section = any(

        section["section_type"] == "PDF"

        for section in sections
    )

    # ======================================================
    # GET DURATIONS
    # ======================================================

    overall_duration = assessment[
        "duration_minutes"
    ]

    pdf_upload_duration = assessment.get(
        "pdf_upload_duration_minutes",
        0
    )

    # ======================================================
    # PDF DURATION VALIDATION
    # ======================================================
    #
    # CASE 1:
    #
    # No PDF section
    #
    #     pdf duration MUST be 0
    #
    #
    # CASE 2:
    #
    # PDF section exists
    #
    #     pdf duration MUST be > 0
    #
    #     pdf duration MUST be < overall duration
    #
    # ======================================================

    if has_pdf_section:

        if pdf_upload_duration <= 0:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "PDF upload duration must be "
                    "greater than 0 when the assessment "
                    "contains a PDF section."
                )
            )

        if pdf_upload_duration >= overall_duration:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "PDF upload duration must be "
                    "less than the overall assessment "
                    "duration."
                )
            )

    else:

        if pdf_upload_duration != 0:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "PDF upload duration must be 0 "
                    "when the assessment has no PDF section."
                )
            )

    # ======================================================
    # QUESTION VALIDATION
    # ======================================================

    from app.database.mongodb import db

    for section in sections:

        question_count = (
            db.questions.count_documents(
                {
                    "assessment_id":
                        assessment_id,

                    "section_id":
                        str(
                            section["_id"]
                        )
                }
            )
        )

        if question_count == 0:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f'Section "{section["title"]}" '
                    "must contain at least one "
                    "question before the assessment "
                    "can be published."
                )
            )

    # ======================================================
    # PUBLISH
    # ======================================================

    published = publish_assessment(

        assessment_id,

        str(
            current_teacher["_id"]
        )
    )

    if not published:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Assessment could not "
                "be published."
            )
        )

    # ======================================================
    # RESPONSE
    # ======================================================

    return serialize_assessment(
        published
    )

