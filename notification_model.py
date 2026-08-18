from datetime import datetime, timezone


# ==========================================================
# NOTIFICATION DOCUMENT
# ==========================================================

def notification_document(
    notification: dict
) -> dict:

    now = datetime.now(
        timezone.utc
    )

    return {

        # --------------------------------------------------
        # STUDENT
        # --------------------------------------------------

        "student_id":
            notification["student_id"],

        # --------------------------------------------------
        # ASSESSMENT
        # --------------------------------------------------

        "assessment_id":
            notification["assessment_id"],

        # --------------------------------------------------
        # NOTIFICATION INFORMATION
        # --------------------------------------------------

        "notification_type":
            notification["notification_type"],

        "title":
            notification["title"],

        "message":
            notification["message"],

        # --------------------------------------------------
        # READ STATUS
        # --------------------------------------------------

        "is_read":
            False,

        # --------------------------------------------------
        # TIMESTAMPS
        # --------------------------------------------------

        "created_at":
            now,

        "updated_at":
            now
    }