from datetime import datetime, timezone


# ==========================================================
# ATTEMPT DOCUMENT
# ==========================================================

def attempt_document(
    attempt: dict
) -> dict:

    now = datetime.now(
        timezone.utc
    )

    document = {

        # --------------------------------------------------
        # RELATIONSHIPS
        # --------------------------------------------------

        "student_id":
            attempt["student_id"],

        "assessment_id":
            attempt["assessment_id"],

        # --------------------------------------------------
        # TIMING
        #
        # IMPORTANT:
        #
        # Timer starts ONLY after successful face
        # verification.
        #
        # Therefore these can initially be None.
        # --------------------------------------------------

        "started_at":
            attempt.get(
                "started_at"
            ),

        "deadline":
            attempt.get(
                "deadline"
            ),

        # --------------------------------------------------
        # SECTION PROGRESSION
        # --------------------------------------------------

        "current_section_order":
            attempt.get(
                "current_section_order",
                1
            ),

        # --------------------------------------------------
        # COMPLETION
        # --------------------------------------------------

        "completed":
            attempt.get(
                "completed",
                False
            ),

        "submitted_at":
            attempt.get(
                "submitted_at"
            ),

        "completion_reason":
            attempt.get(
                "completion_reason"
            ),

        # --------------------------------------------------
        # ANSWERS
        # --------------------------------------------------

        "answers":
            attempt.get(
                "answers",
                {}
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