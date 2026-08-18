import os

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status
)

import cv2
import numpy as np

from app.dependencies.auth_dependencies import (
    require_student
)

from app.crud.user_crud import (
    get_user_by_id
)

from app.crud.session_crud import (
    get_session_by_id,
    start_session_after_face_verification
)

from app.crud.assessment_crud import (
    get_assessment_by_id
)

from app.services.face_verification import (
    verify_face
)


# ==========================================================
# ROUTER
# ==========================================================

router = APIRouter(
    prefix="/student",
    tags=["Face Verification"]
)


# ==========================================================
# PROFILE PHOTO DIRECTORY
# ==========================================================

PROFILE_PHOTO_DIRECTORY = os.path.join(
    "uploads",
    "profile_photos"
)


# ==========================================================
# ALLOWED IMAGE TYPES
# ==========================================================

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png"
}


# ==========================================================
# VERIFY FACE
# ==========================================================
#
# Flow:
#
# 1. Student sends live webcam image.
# 2. Backend identifies the logged-in student.
# 3. Backend gets the student's registered profile photo.
# 4. Backend compares:
#
#       registered photo
#              VS
#       live webcam image
#
# 5. If the faces match:
#
#       face_verified = True
#       timer starts
#       deadline is calculated
#
# 6. If the faces do not match:
#
#       timer does NOT start.
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

    # ======================================================
    # GET STUDENT ID
    # ======================================================

    student_id = str(
        current_student["_id"]
    )

    # ======================================================
    # GET SESSION
    # ======================================================

    session = get_session_by_id(
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
    # VERIFY SESSION OWNERSHIP
    # ======================================================

    if (
        session.get("student_id")
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
    # FACE ALREADY VERIFIED
    # ======================================================

    if session.get(
        "face_verified",
        False
    ):

        return {

            "message":
                "Face has already been verified.",

            "verified":
                True,

            "session_id":
                session_id,

            "face_verified":
                True
        }

    # ======================================================
    # VALIDATE UPLOADED IMAGE
    # ======================================================

    if not live_image.filename:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Live webcam image is required."
        )

    if (
        live_image.content_type
        not in
        ALLOWED_CONTENT_TYPES
    ):

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Only JPG, JPEG, and PNG images are allowed."
        )

    # ======================================================
    # GET REGISTERED STUDENT
    # ======================================================

    student = get_user_by_id(
        student_id
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

    reference_image_path = os.path.join(

        PROFILE_PHOTO_DIRECTORY,

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

            raise HTTPException(

                status_code=
                    status.HTTP_400_BAD_REQUEST,

                detail=
                    "The webcam image is empty."
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

            raise HTTPException(

                status_code=
                    status.HTTP_400_BAD_REQUEST,

                detail=
                    "Unable to read the webcam image."
            )

    finally:

        await live_image.close()

    # ======================================================
    # FACE VERIFICATION
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

    except Exception as e:

        raise HTTPException(

            status_code=
                status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=(
                "Face verification failed: "
                f"{str(e)}"
            )
        )

    # ======================================================
    # CHECK RESULT
    # ======================================================

    verified = verification_result[
        "verified"
    ]

    similarity = verification_result[
        "similarity"
    ]

    # ======================================================
    # FACE DOES NOT MATCH
    # ======================================================

    if not verified:

        return {

            "message":
                "Face verification failed.",

            "verified":
                False,

            "similarity":
                similarity,

            "timer_started":
                False,

            "session_id":
                session_id
        }

    # ======================================================
    # GET ASSESSMENT
    # ======================================================

    assessment = get_assessment_by_id(

        session[
            "assessment_id"
        ]
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

    if duration_minutes is None:

        raise HTTPException(

            status_code=
                status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=
                "Assessment duration is not configured."
        )

    try:

        duration_minutes = int(
            duration_minutes
        )

    except (
        TypeError,
        ValueError
    ):

        raise HTTPException(

            status_code=
                status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=
                "Assessment duration is invalid."
        )

    if duration_minutes <= 0:

        raise HTTPException(

            status_code=
                status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=
                "Assessment duration must be greater than zero."
        )

    # ======================================================
    # START TIMER
    # ======================================================
    #
    # IMPORTANT:
    #
    # This is the first point at which the assessment timer
    # starts.
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
                "but the assessment session could not "
                "be started. Please try again."
            )
        )

    # ======================================================
    # SUCCESS
    # ======================================================

    return {

        "message":
            "Face verified successfully. Assessment timer started.",

        "verified":
            True,

        "similarity":
            similarity,

        "timer_started":
            True,

        "session_id":
            str(
                updated_session["_id"]
            ),

        "face_verified":
            updated_session[
                "face_verified"
            ],

        "started_at":
            updated_session[
                "started_at"
            ],

        "deadline":
            updated_session[
                "deadline"
            ]
    }