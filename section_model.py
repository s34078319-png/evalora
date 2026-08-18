from datetime import datetime, timezone


# ==========================================================
# SECTION DOCUMENT
# ==========================================================

def section_document(
    section: dict
) -> dict:

    now = datetime.now(
        timezone.utc
    )

    document = {

        # --------------------------------------------------
        # ASSESSMENT
        # --------------------------------------------------

        "assessment_id":
            section["assessment_id"],

        # --------------------------------------------------
        # BASIC INFORMATION
        # --------------------------------------------------

        "title":
            section["title"],

        "section_type":
            section["section_type"],

        # --------------------------------------------------
        # AUTOMATIC ORDER
        # --------------------------------------------------

        "order":
            section["order"],

        # --------------------------------------------------
        # TIMESTAMPS
        # --------------------------------------------------

        "created_at":
            now,

        "updated_at":
            now
    }

    return document