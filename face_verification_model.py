from datetime import datetime, timezone


# ==========================================================
# FACE VERIFICATION RECORD
# ==========================================================
#
# This document stores the student's enrolled face
# verification information.
#
# IMPORTANT:
#
# We do NOT store the student's raw camera image here.
#
# The actual face representation/embedding will be added
# when we connect the face-verification engine.
# ==========================================================


def face_verification_document(
    data: dict
) -> dict:

    now = datetime.now(
        timezone.utc
    )

    document = {

        # --------------------------------------------------
        # STUDENT
        # --------------------------------------------------

        "student_id":
            data["student_id"],

        # --------------------------------------------------
        # VERIFICATION STATUS
        # --------------------------------------------------

        "enrolled":
            data.get(
                "enrolled",
                False
            ),

        "verified":
            data.get(
                "verified",
                False
            ),

        # --------------------------------------------------
        # FACE REPRESENTATION
        # --------------------------------------------------
        #
        # This will later contain the generated face
        # embedding/representation.
        #
        # For now it is None.
        #
        # --------------------------------------------------

        "face_embedding":
            data.get(
                "face_embedding"
            ),

        # --------------------------------------------------
        # VERIFICATION INFORMATION
        # --------------------------------------------------

        "last_verified_at":
            data.get(
                "last_verified_at"
            ),

        "verification_attempts":
            data.get(
                "verification_attempts",
                0
            ),

        "failed_verifications":
            data.get(
                "failed_verifications",
                0
            ),

        # --------------------------------------------------
        # TIMESTAMPS
        # --------------------------------------------------

        "created_at":
            now,

        "updated_at":
            now
    }

    return document