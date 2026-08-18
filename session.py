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

from app.crud.session_crud import (
    get_session_by_session_id,
    update_session,
    end_session
)

from app.schemas.session_schema import (
    SessionResponse
)


router = APIRouter(
    prefix="/student",
    tags=["Student Sessions"]
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

        return value.astimezone(
            timezone.utc
        )

    return value.replace(
        tzinfo=timezone.utc
    )


# ==========================================================
# SERIALIZE SESSION
# ==========================================================


def serialize_session(
    session: dict
):

    return {

        "id":
            str(
                session["_id"]
            ),

        "session_id":
            session[
                "session_id"
            ],

        "attempt_id":
            session[
                "attempt_id"
            ],

        "student_id":
            session[
                "student_id"
            ],

        "assessment_id":
            session[
                "assessment_id"
            ],

        "started_at":
            ensure_utc(
                session[
                    "started_at"
                ]
            ),

        "deadline":
            ensure_utc(
                session[
                    "deadline"
                ]
            ),

        "ended_at":
            (
                ensure_utc(
                    session[
                        "ended_at"
                    ]
                )
                if session.get(
                    "ended_at"
                )
                else None
            ),

        "active":
            session.get(
                "active",
                True
            ),

        "face_verified":
            session.get(
                "face_verified",
                False
            ),

        "proctoring_flags":
            session.get(
                "proctoring_flags",
                0
            ),

        "current_section_order":
            session.get(
                "current_section_order",
                1
            ),

        "created_at":
            ensure_utc(
                session[
                    "created_at"
                ]
            ),

        "updated_at":
            ensure_utc(
                session[
                    "updated_at"
                ]
            )
    }


# ==========================================================
# GET MY SESSION
# ==========================================================
#
# GET /student/sessions/{session_id}
#
# The student can only access their own session.
# ==========================================================


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse
)
def get_my_session(

    session_id: str,

    current_student: dict = Depends(
        require_student
    )
):

    student_id = str(
        current_student["_id"]
    )

    # ======================================================
    # GET SESSION
    # ======================================================

    session = get_session_by_session_id(
        session_id
    )

    if not session:

        raise HTTPException(

            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Assessment session not found."
        )

    # ======================================================
    # OWNERSHIP
    # ======================================================

    if (
        session["student_id"]
        !=
        student_id
    ):

        raise HTTPException(

            status_code=
                status.HTTP_403_FORBIDDEN,

            detail=
                "You do not have access to this assessment session."
        )

    # ======================================================
    # AUTOMATIC EXPIRATION CHECK
    # ======================================================

    if session.get(
        "active",
        False
    ):

        deadline = ensure_utc(
            session[
                "deadline"
            ]
        )

        now = datetime.now(
            timezone.utc
        )

        if now > deadline:

            session = update_session(

                str(
                    session["_id"]
                ),

                {
                    "active":
                        False,

                    "ended_at":
                        now
                }
            )

    return serialize_session(
        session
    )


# ==========================================================
# END MY SESSION
# ==========================================================
#
# POST /student/sessions/{session_id}/end
#
# This is useful later for explicit submission/session
# termination.
#
# Actual assessment submission will be handled separately.
# ==========================================================


@router.post(
    "/sessions/{session_id}/end",
    response_model=SessionResponse
)
def end_my_session(

    session_id: str,

    current_student: dict = Depends(
        require_student
    )
):

    student_id = str(
        current_student["_id"]
    )

    # ======================================================
    # GET SESSION
    # ======================================================

    session = get_session_by_session_id(
        session_id
    )

    if not session:

        raise HTTPException(

            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Assessment session not found."
        )

    # ======================================================
    # OWNERSHIP
    # ======================================================

    if (
        session["student_id"]
        !=
        student_id
    ):

        raise HTTPException(

            status_code=
                status.HTTP_403_FORBIDDEN,

            detail=
                "You do not have access to this assessment session."
        )

    # ======================================================
    # ALREADY ENDED
    # ======================================================

    if not session.get(
        "active",
        False
    ):

        return serialize_session(
            session
        )

    # ======================================================
    # END SESSION
    # ======================================================

    updated = update_session(

        str(
            session["_id"]
        ),

        {
            "active":
                False,

            "ended_at":
                datetime.now(
                    timezone.utc
                )
        }
    )

    if not updated:

        raise HTTPException(

            status_code=
                status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=
                "Could not end the assessment session."
        )

    return serialize_session(
        updated
    )