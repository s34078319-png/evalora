from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from app.schemas.student_assessment_schema import (
    StudentAssessmentListResponse,
    StudentAssessmentDetailResponse,
    StudentSectionResponse
)

from app.crud.student_assessment_crud import (
    get_student_assessments,
    get_student_assessment_by_id,
    get_student_assessment_sections,
    get_student_assessment_status
)

from app.dependencies.auth_dependencies import (
    require_student
)


# ==========================================================
# ROUTER
# ==========================================================

router = APIRouter(
    prefix="/student",
    tags=["Student Assessments"]
)


# ==========================================================
# SERIALIZE ASSESSMENT
# ==========================================================

def serialize_student_assessment(
    assessment: dict
):

    return {

        "id":
            str(
                assessment["_id"]
            ),

        "title":
            assessment["title"],

        "description":
            assessment.get(
                "description"
            ),

        "branch":
            assessment["branch"],

        "semester":
            assessment["semester"],

        "opening_time":
            assessment["opening_time"],

        "closing_time":
            assessment["closing_time"],

        "duration_minutes":
            assessment["duration_minutes"],

        "max_proctoring_flags":
            assessment[
                "max_proctoring_flags"
            ],

        "status":
            get_student_assessment_status(
                assessment
            )
    }


# ==========================================================
# SERIALIZE SECTION
# ==========================================================

def serialize_student_section(
    section: dict
):

    return {

        "id":
            str(
                section["_id"]
            ),

        "assessment_id":
            section["assessment_id"],

        "title":
            section["title"],

        "section_type":
            section["section_type"],

        "order":
            section["order"]
    }


# ==========================================================
# GET STUDENT ASSESSMENTS
# ==========================================================

@router.get(
    "/assessments",

    response_model=
        list[
            StudentAssessmentListResponse
        ]
)
def get_available_assessments(

    current_student: dict = Depends(
        require_student
    )
):

    # ------------------------------------------------------
    # GET STUDENT ACADEMIC INFORMATION
    # ------------------------------------------------------

    branch = current_student.get(
        "branch"
    )

    semester = current_student.get(
        "semester"
    )

    if branch is None or semester is None:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Student academic information is incomplete."
        )

    # ------------------------------------------------------
    # GET ELIGIBLE ASSESSMENTS
    # ------------------------------------------------------

    assessments = get_student_assessments(

        branch=branch,

        semester=semester
    )

    # ------------------------------------------------------
    # SERIALIZE
    # ------------------------------------------------------

    return [

        serialize_student_assessment(
            assessment
        )

        for assessment
        in assessments
    ]


# ==========================================================
# GET STUDENT ASSESSMENT DETAILS
# ==========================================================

@router.get(
    "/assessments/{assessment_id}",

    response_model=
        StudentAssessmentDetailResponse
)
def get_assessment_details(

    assessment_id: str,

    current_student: dict = Depends(
        require_student
    )
):

    # ------------------------------------------------------
    # STUDENT INFORMATION
    # ------------------------------------------------------

    branch = current_student.get(
        "branch"
    )

    semester = current_student.get(
        "semester"
    )

    if branch is None or semester is None:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Student academic information is incomplete."
        )

    # ------------------------------------------------------
    # GET ELIGIBLE ASSESSMENT
    #
    # This simultaneously checks:
    #
    # - assessment exists
    # - published
    # - branch matches
    # - semester matches
    # ------------------------------------------------------

    assessment = get_student_assessment_by_id(

        assessment_id=assessment_id,

        branch=branch,

        semester=semester
    )

    if not assessment:

        raise HTTPException(

            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Assessment not found or you are not eligible for this assessment."
        )

    # ------------------------------------------------------
    # GET SECTIONS
    # ------------------------------------------------------

    sections = get_student_assessment_sections(

        assessment_id
    )

    # ------------------------------------------------------
    # SERIALIZE ASSESSMENT
    # ------------------------------------------------------

    response = serialize_student_assessment(
        assessment
    )

    # ------------------------------------------------------
    # ADD SECTIONS
    #
    # Sections are already sorted by their
    # teacher-defined automatic order.
    #
    # MCQ -> DESCRIPTIVE -> PDF
    # ------------------------------------------------------

    response["sections"] = [

        serialize_student_section(
            section
        )

        for section
        in sections
    ]

    return response