from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from app.dependencies.auth_dependencies import (
    require_student
)

from app.crud.assessment_crud import (
    get_assessment_by_id
)

from app.crud.attempt_crud import (
    create_attempt,
    get_student_attempt,
    get_attempt_by_id
)

from app.crud.session_crud import (
    create_session,
    get_session_by_attempt
)

from app.database.mongodb import db

from app.schemas.attempt_schema import (
    StudentAssessmentResponse,
    StartAssessmentResponse,
    AttemptResponse
)


router = APIRouter(
    prefix="/student",
    tags=["Student Assessments"]
)


# ==========================================================
# DATETIME NORMALIZATION
# ==========================================================

def ensure_utc(
    value: datetime
) -> datetime:

    if value is None:
        return value

    if value.tzinfo is not None:
        return value.astimezone(timezone.utc)

    return value.replace(
        tzinfo=timezone.utc
    )


# ==========================================================
# SERIALIZE ATTEMPT
# ==========================================================

def serialize_attempt(
    attempt: dict
):

    return {

        "id":
            str(
                attempt["_id"]
            ),

        "student_id":
            attempt["student_id"],

        "assessment_id":
            attempt["assessment_id"],

        "started_at":
            (
                ensure_utc(
                    attempt["started_at"]
                )
                if attempt.get("started_at")
                else None
            ),

        "deadline":
            (
                ensure_utc(
                    attempt["deadline"]
                )
                if attempt.get("deadline")
                else None
            ),

        "current_section_order":
            attempt.get(
                "current_section_order",
                1
            ),

        "completed":
            attempt.get(
                "completed",
                False
            ),

        "submitted_at":
            (
                ensure_utc(
                    attempt["submitted_at"]
                )
                if attempt.get(
                    "submitted_at"
                )
                else None
            ),

        "created_at":
            (
                ensure_utc(
                    attempt["created_at"]
                )
                if attempt.get("created_at")
                else None
            ),

        "updated_at":
            (
                ensure_utc(
                    attempt["updated_at"]
                )
                if attempt.get("updated_at")
                else None
            )
    }


# ==========================================================
# SERIALIZE START RESPONSE
# ==========================================================

def serialize_start_response(
    attempt: dict,
    session: dict
):

    return {

        "attempt_id":
            str(
                attempt["_id"]
            ),

        "session_id":
            str(
                session["_id"]
            ),

        "assessment_id":
            attempt["assessment_id"],

        "started_at":
            (
                ensure_utc(
                    session["started_at"]
                )
                if session.get("started_at")
                else None
            ),

        "deadline":
            (
                ensure_utc(
                    session["deadline"]
                )
                if session.get("deadline")
                else None
            ),

        "current_section_order":
            session.get(
                "current_section_order",
                attempt.get(
                    "current_section_order",
                    1
                )
            ),

        "completed":
            attempt.get(
                "completed",
                False
            ),

        "active":
            session.get(
                "active",
                False
            ),

        "face_verified":
            session.get(
                "face_verified",
                False
            )
    }


# ==========================================================
# GET ELIGIBLE ASSESSMENTS
# ==========================================================

@router.get(
    "/assessments",
    response_model=list[
        StudentAssessmentResponse
    ]
)
def get_student_assessments(

    current_student: dict = Depends(
        require_student
    )
):

    student_id = str(
        current_student["_id"]
    )

    student_branch = (
        current_student.get(
            "branch"
        )
    )

    student_semester = (
        current_student.get(
            "semester"
        )
    )

    if not student_branch:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Student branch is not configured."
        )

    if student_semester is None:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Student semester is not configured."
        )

    now = datetime.now(
        timezone.utc
    )

    assessments = list(

        db.assessments.find(

            {
                "status":
                    "PUBLISHED",

                "branch":
                    student_branch,

                "semester":
                    student_semester
            }

        ).sort(

            "opening_time",
            1
        )
    )

    response = []

    for assessment in assessments:

        assessment_id = str(
            assessment["_id"]
        )

        attempt = get_student_attempt(

            student_id,

            assessment_id
        )

        attempt_started = (
            attempt is not None
        )

        attempt_completed = (

            attempt is not None

            and

            attempt.get(
                "completed",
                False
            )
        )

        opening_time = ensure_utc(
            assessment[
                "opening_time"
            ]
        )

        closing_time = ensure_utc(
            assessment[
                "closing_time"
            ]
        )

        if now < opening_time:

            display_status = "UPCOMING"

        elif now <= closing_time:

            display_status = "LIVE"

        else:

            display_status = "CLOSED"

        response.append({

            "id":
                assessment_id,

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
                opening_time,

            "closing_time":
                closing_time,

            "duration_minutes":
                assessment[
                    "duration_minutes"
                ],

            "status":
                display_status,

            "published_at":
                (
                    ensure_utc(
                        assessment[
                            "published_at"
                        ]
                    )
                    if assessment.get(
                        "published_at"
                    )
                    else None
                ),

            "attempt_started":
                attempt_started,

            "attempt_completed":
                attempt_completed
        })

    return response


# ==========================================================
# START ASSESSMENT
# ==========================================================
#
# IMPORTANT:
#
# This endpoint DOES NOT start the assessment timer.
#
# It only creates the attempt/session and waits for:
#
#     face verification
#
# The actual timer starts inside:
#
#     start_session_after_face_verification()
#
# ==========================================================

@router.post(
    "/assessments/{assessment_id}/start",
    response_model=StartAssessmentResponse,
    status_code=status.HTTP_201_CREATED
)
def start_assessment(

    assessment_id: str,

    current_student: dict = Depends(
        require_student
    )
):

    student_id = str(
        current_student["_id"]
    )

    student_branch = (
        current_student.get(
            "branch"
        )
    )

    student_semester = (
        current_student.get(
            "semester"
        )
    )

    # ======================================================
    # GET ASSESSMENT
    # ======================================================

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

    # ======================================================
    # MUST BE PUBLISHED
    # ======================================================

    if assessment["status"] != "PUBLISHED":

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "This assessment is not published."
        )

    # ======================================================
    # BRANCH ELIGIBILITY
    # ======================================================

    if (
        assessment["branch"]
        !=
        student_branch
    ):

        raise HTTPException(

            status_code=
                status.HTTP_403_FORBIDDEN,

            detail=
                "You are not eligible for this assessment."
        )

    # ======================================================
    # SEMESTER ELIGIBILITY
    # ======================================================

    if (
        assessment["semester"]
        !=
        student_semester
    ):

        raise HTTPException(

            status_code=
                status.HTTP_403_FORBIDDEN,

            detail=
                "You are not eligible for this assessment."
        )

    # ======================================================
    # CURRENT TIME
    # ======================================================

    now = datetime.now(
        timezone.utc
    )

    # ======================================================
    # ASSESSMENT OPEN/CLOSE TIMES
    # ======================================================

    opening_time = ensure_utc(
        assessment[
            "opening_time"
        ]
    )

    closing_time = ensure_utc(
        assessment[
            "closing_time"
        ]
    )

    if now < opening_time:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "This assessment has not started yet."
        )

    if now > closing_time:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "This assessment is closed."
        )

    # ======================================================
    # CHECK EXISTING ATTEMPT
    # ======================================================

    existing_attempt = (
        get_student_attempt(

            student_id,

            assessment_id
        )
    )

    # ======================================================
    # EXISTING ATTEMPT
    # ======================================================

    if existing_attempt:

        # --------------------------------------------------
        # ALREADY COMPLETED
        # --------------------------------------------------

        if existing_attempt.get(
            "completed",
            False
        ):

            raise HTTPException(

                status_code=
                    status.HTTP_400_BAD_REQUEST,

                detail=
                    "You have already completed this assessment."
            )

        # --------------------------------------------------
        # GET EXISTING SESSION
        # --------------------------------------------------

        existing_session = (
            get_session_by_attempt(

                str(
                    existing_attempt["_id"]
                )
            )
        )

        # --------------------------------------------------
        # CREATE MISSING SESSION
        # --------------------------------------------------

        if not existing_session:

            existing_session = create_session({

                "attempt_id":
                    str(
                        existing_attempt["_id"]
                    ),

                "student_id":
                    student_id,

                "assessment_id":
                    assessment_id,

                # Timer has NOT started yet.
                "started_at":
                    None,

                "deadline":
                    None,

                "ended_at":
                    None,

                "active":
                    True,

                "face_verified":
                    False,

                "proctoring_flags":
                    0,

                "current_section_order":
                    existing_attempt.get(
                        "current_section_order",
                        1
                    )
            })

        # --------------------------------------------------
        # RETURN EXISTING SESSION
        # --------------------------------------------------

        return serialize_start_response(

            existing_attempt,

            existing_session
        )

    # ======================================================
    # VALIDATE ASSESSMENT DURATION
    # ======================================================

    duration_minutes = (
        assessment[
            "duration_minutes"
        ]
    )

    if (
        not duration_minutes
        or
        duration_minutes <= 0
    ):

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Assessment has an invalid duration."
        )

    # ======================================================
    # CREATE ATTEMPT
    # ======================================================
    #
    # IMPORTANT:
    #
    # Do NOT calculate the assessment deadline here.
    #
    # The timer begins after successful face verification.
    #
    # Therefore:
    #
    #     started_at = None
    #     deadline = None
    #
    # ======================================================

    attempt = create_attempt({

        "student_id":
            student_id,

        "assessment_id":
            assessment_id,

        "started_at":
            None,

        "deadline":
            None,

        "current_section_order":
            1,

        "completed":
            False,

        "submitted_at":
            None,

        "answers":
            {}
    })

    # ======================================================
    # CREATE SESSION
    # ======================================================
    #
    # Session is active while waiting for face verification.
    #
    # But the timer has NOT started.
    #
    # ======================================================

    session = create_session({

        "attempt_id":
            str(
                attempt["_id"]
            ),

        "student_id":
            student_id,

        "assessment_id":
            assessment_id,

        "started_at":
            None,

        "deadline":
            None,

        "ended_at":
            None,

        "active":
            True,

        "face_verified":
            False,

        "proctoring_flags":
            0,

        "current_section_order":
            1
    })

    # ======================================================
    # RESPONSE
    # ======================================================

    return serialize_start_response(

        attempt,

        session
    )


# ==========================================================
# GET MY ATTEMPT
# ==========================================================

@router.get(
    "/attempts/{attempt_id}",
    response_model=AttemptResponse
)
def get_my_attempt(

    attempt_id: str,

    current_student: dict = Depends(
        require_student
    )
):

    student_id = str(
        current_student["_id"]
    )

    attempt = get_attempt_by_id(
        attempt_id
    )

    if not attempt:

        raise HTTPException(

            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Assessment attempt not found."
        )

    if (
        attempt["student_id"]
        !=
        student_id
    ):

        raise HTTPException(

            status_code=
                status.HTTP_403_FORBIDDEN,

            detail=
                "You do not have access to this assessment attempt."
        )

    return serialize_attempt(
        attempt
    )