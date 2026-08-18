from datetime import datetime, timezone

from bson import ObjectId

from app.database.mongodb import db


# ==========================================================
# GET ELIGIBLE PUBLISHED ASSESSMENTS
# ==========================================================

def get_student_assessments(
    branch: str,
    semester: int
):

    return list(

        db.assessments.find(

            {
                "branch": branch,

                "semester": semester,

                "status": "PUBLISHED"
            }

        ).sort(

            "opening_time",
            1
        )
    )


# ==========================================================
# GET ELIGIBLE ASSESSMENT BY ID
# ==========================================================

def get_student_assessment_by_id(
    assessment_id: str,
    branch: str,
    semester: int
):

    try:

        return db.assessments.find_one(

            {
                "_id":
                    ObjectId(
                        assessment_id
                    ),

                "branch":
                    branch,

                "semester":
                    semester,

                "status":
                    "PUBLISHED"
            }
        )

    except Exception:

        return None


# ==========================================================
# GET ASSESSMENT SECTIONS
# ==========================================================

def get_student_assessment_sections(
    assessment_id: str
):

    return list(

        db.sections.find(

            {
                "assessment_id":
                    assessment_id
            }

        ).sort(

            "order",
            1
        )
    )


# ==========================================================
# CALCULATE STUDENT ASSESSMENT STATUS
# ==========================================================

def get_student_assessment_status(
    assessment: dict
):

    now = datetime.now(
        timezone.utc
    )

    opening_time = assessment[
        "opening_time"
    ]

    closing_time = assessment[
        "closing_time"
    ]

    # ------------------------------------------------------
    # HANDLE NAIVE DATETIME
    # ------------------------------------------------------

    if opening_time.tzinfo is None:

        opening_time = opening_time.replace(
            tzinfo=timezone.utc
        )

    if closing_time.tzinfo is None:

        closing_time = closing_time.replace(
            tzinfo=timezone.utc
        )

    # ------------------------------------------------------
    # UPCOMING
    # ------------------------------------------------------

    if now < opening_time:

        return "UPCOMING"

    # ------------------------------------------------------
    # LIVE
    # ------------------------------------------------------

    if (
        now >= opening_time
        and
        now < closing_time
    ):

        return "LIVE"

    # ------------------------------------------------------
    # CLOSED
    # ------------------------------------------------------

    return "CLOSED"