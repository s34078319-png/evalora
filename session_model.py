from datetime import datetime, timezone


# ==========================================================
# ASSESSMENT SESSION DOCUMENT
# ==========================================================
#
# An attempt represents the student's overall attempt.
#
# A session represents the actual active exam-taking session.
#
# This session will later be used for:
#
# - face verification
# - proctoring
# - activity tracking
# - section progression
# - session validity
#
# ==========================================================


def session_document(
    session: dict
) -> dict:

    now = datetime.now(
        timezone.utc
    )

    document = {

        # --------------------------------------------------
        # RELATIONSHIPS
        # --------------------------------------------------

        "attempt_id":
            session["attempt_id"],

        "student_id":
            session["student_id"],

        "assessment_id":
            session["assessment_id"],

        # --------------------------------------------------
        # SESSION TIMING
        # --------------------------------------------------

        "started_at":
            session["started_at"],

        "deadline":
            session["deadline"],

        "ended_at":
            session.get(
                "ended_at"
            ),

        # --------------------------------------------------
        # SESSION STATUS
        # --------------------------------------------------

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

        # --------------------------------------------------
        # PROCTORING
        #
        # These will be populated later.
        # --------------------------------------------------

        "proctoring_flags":
            session.get(
                "proctoring_flags",
                0
            ),

        # --------------------------------------------------
        # SECTION PROGRESSION
        # --------------------------------------------------

        "current_section_order":
            session.get(
                "current_section_order",
                1
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