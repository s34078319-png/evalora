from datetime import (
    datetime,
    timezone
)

import os
import cv2
import numpy as np

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File
)

from app.dependencies.auth_dependencies import (
    require_student
)

from app.crud.session_crud import (
    get_session_with_expiration_check,
    start_session_after_face_verification
)

from app.database.mongodb import db

from app.schemas.session_schema import (
    SessionResponse
)

from app.services.face_verification import (
    verify_face
)


# ==========================================================
# ROUTER
# ==========================================================

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

        "attempt_id":
            session["attempt_id"],

        "student_id":
            session["student_id"],

        "assessment_id":
            session["assessment_id"],

        "started_at":
            ensure_utc(
                session["started_at"]
            ),

        "deadline":
            ensure_utc(
                session["deadline"]
            ),

        "ended_at":
            (
                ensure_utc(
                    session["ended_at"]
                )
                if session.get(
                    "ended_at"
                )
                else None
            ),

        "active":
            session["active"],

        "face_verified":
            session["face_verified"],

        "proctoring_flags":
            session["proctoring_flags"],

        "current_section_order":
            session[
                "current_section_order"
            ],

        "created_at":
            ensure_utc(
                session["created_at"]
            ),

        "updated_at":
            ensure_utc(
                session["updated_at"]
            )
    }


# ==========================================================
# GET MY SESSION
# ==========================================================
#
# This endpoint:
#
# - gets the student's session
# - checks whether the timer has expired
# - automatically ends an expired session
#
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

    session = get_session_with_expiration_check(
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
    # CHECK OWNERSHIP
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
    # RETURN SESSION
    # ======================================================

    return serialize_session(
        session
    )


# ==========================================================
# FACE VERIFICATION
# ==========================================================
#
# The student already has a registered profile photo.
#
# We use:
#
#     registered profile photo
#             +
#     temporary live webcam image
#
# InsightFace compares the two faces.
#
# If verification succeeds:
#
#     face_verified = True
#     started_at = current time
#     deadline = current time + assessment duration
#
# Therefore the assessment timer starts ONLY after
# successful face verification.
#
# ==========================================================

@router.post(
    "/sessions/{session_id}/verify-face"
)
async def verify_student_face(

    session_id: str,

    live_image: UploadFile = File(...),

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

    session = get_session_with_expiration_check(
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
    # CHECK OWNERSHIP
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
    # SESSION MUST BE ACTIVE
    # ======================================================

    if not session.get(
        "active",
        False
    ):

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "This assessment session is no longer active."
        )

    # ======================================================
    # ALREADY VERIFIED
    # ======================================================
    #
    # If the student has already passed the initial
    # verification, we do not restart the timer.
    #
    # ======================================================

    if session.get(
        "face_verified",
        False
    ):

        return {

            "message":
                "Face is already verified.",

            "verified":
                True,

            "face_verified":
                True,

            "session_id":
                session_id,

            "timer_started":
                True,

            "started_at":
                ensure_utc(
                    session["started_at"]
                ),

            "deadline":
                ensure_utc(
                    session["deadline"]
                )
        }

    # ======================================================
    # LIVE IMAGE REQUIRED
    # ======================================================

    if not live_image.filename:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Live webcam image is required."
        )

    # ======================================================
    # VALIDATE IMAGE TYPE
    # ======================================================

    allowed_content_types = {

        "image/jpeg",
        "image/png",
        "image/jpg"
    }

    if live_image.content_type not in (
        allowed_content_types
    ):

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Live image must be a JPG, JPEG, or PNG image."
        )

    # ======================================================
    # GET STUDENT
    # ======================================================

    student = db.users.find_one(

        {
            "_id":
                current_student["_id"],

            "role":
                "student"
        }
    )

    if not student:

        raise HTTPException(

            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Student account not found."
        )

    # ======================================================
    # GET REGISTERED PROFILE PHOTO
    # ======================================================
    #
    # This is the photo uploaded during registration.
    #
    # We do NOT ask the student to register another photo.
    #
    # ======================================================

    profile_photo = student.get(
        "profile_photo"
    )

    if not profile_photo:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "No registered profile photo was found for this student."
        )

    # ======================================================
    # BUILD REFERENCE PHOTO PATH
    # ======================================================

    reference_image_path = os.path.join(

        "uploads",

        "profile_photos",

        profile_photo
    )

    if not os.path.exists(
        reference_image_path
    ):

        raise HTTPException(

            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Registered profile photo could not be found."
        )

    # ======================================================
    # READ LIVE WEBCAM IMAGE
    # ======================================================

    try:

        image_bytes = await live_image.read()

        if not image_bytes:

            raise ValueError(
                "Empty image."
            )

        image_array = np.frombuffer(

            image_bytes,

            dtype=np.uint8
        )

        live_image_cv = cv2.imdecode(

            image_array,

            cv2.IMREAD_COLOR
        )

        if live_image_cv is None:

            raise ValueError(
                "Unable to decode image."
            )

    except Exception:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Unable to read the live webcam image."
        )

    finally:

        await live_image.close()

    # ======================================================
    # VERIFY FACE
    # ======================================================

    try:

        verification_result = verify_face(

            reference_image_path,

            live_image_cv
        )

    except ValueError as e:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=str(e)
        )

    except Exception:

        raise HTTPException(

            status_code=
                status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=
                "Face verification failed unexpectedly."
        )

    # ======================================================
    # FACE VERIFICATION FAILED
    # ======================================================

    if not verification_result["verified"]:

        return {

            "message":
                "Face verification failed.",

            "verified":
                False,

            "face_verified":
                False,

            "similarity":
                verification_result[
                    "similarity"
                ],

            "session_id":
                session_id,

            "timer_started":
                False
        }

    # ======================================================
    # GET ASSESSMENT
    # ======================================================

    assessment = db.assessments.find_one(

        {
            "_id":
                session[
                    "assessment_id"
                ]
        }
    )

    if not assessment:

        raise HTTPException(

            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Assessment not found."
        )

    # ======================================================
    # GET ASSESSMENT DURATION
    # ======================================================

    duration_minutes = assessment.get(
        "duration_minutes"
    )

    if not duration_minutes:

        raise HTTPException(

            status_code=
                status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=
                "Assessment duration is not configured."
        )

    # ======================================================
    # START SESSION
    # ======================================================
    #
    # IMPORTANT:
    #
    # We do NOT use update_session() here.
    #
    # We use the dedicated atomic function:
    #
    #     start_session_after_face_verification()
    #
    # This ensures that the timer starts only once and only
    # when face_verified is currently False.
    #
    # ======================================================

    updated_session = (
        start_session_after_face_verification(

            session_id,

            duration_minutes
        )
    )

    if not updated_session:

        raise HTTPException(

            status_code=
                status.HTTP_409_CONFLICT,

            detail=(
                "Face verification succeeded, "
                "but the assessment session could "
                "not be started. It may already "
                "have been verified or ended."
            )
        )

    # ======================================================
    # SUCCESS
    # ======================================================

    return {

        "message":
            "Face verification successful. Assessment timer has started.",

        "verified":
            True,

        "face_verified":
            True,

        "similarity":
            verification_result[
                "similarity"
            ],

        "session_id":
            session_id,

        "timer_started":
            True,

        "started_at":
            ensure_utc(
                updated_session[
                    "started_at"
                ]
            ),

        "deadline":
            ensure_utc(
                updated_session[
                    "deadline"
                ]
            )
    }