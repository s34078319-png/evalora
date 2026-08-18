from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.database.mongodb import db

from app.models.assessment_model import (
    assessment_document
)

from app.crud.notification_crud import (
    create_notification,
    notification_exists
)


# ==========================================================
# CREATE ASSESSMENT
# ==========================================================
#
# A new assessment is considered a duplicate when the same
# teacher already has an assessment with ALL of these values:
#
# title
# description
# branch
# semester
# opening_time
# closing_time
# duration_minutes
# pdf_upload_duration_minutes
# max_proctoring_flags
#
# Therefore changing PDF upload duration creates a different
# assessment.
# ==========================================================

def create_assessment(
    assessment: dict
):

    # ------------------------------------------------------
    # PDF DURATION
    # ------------------------------------------------------

    pdf_upload_duration = assessment.get(
        "pdf_upload_duration_minutes",
        0
    )

    duration_minutes = assessment[
        "duration_minutes"
    ]

    # ------------------------------------------------------
    # VALIDATE PDF DURATION
    #
    # 0 is allowed because the assessment may not contain
    # a PDF section yet.
    #
    # If greater than 0, it must be less than the overall
    # assessment duration.
    # ------------------------------------------------------

    if pdf_upload_duration < 0:

        raise ValueError(
            "PDF upload duration cannot be negative."
        )

    if (
        pdf_upload_duration > 0
        and
        pdf_upload_duration >= duration_minutes
    ):

        raise ValueError(
            "PDF upload duration must be greater than 0 "
            "and less than the overall assessment duration."
        )

    # ======================================================
    # DUPLICATE CHECK
    # ======================================================

    duplicate_query = {

        "teacher_id":
            assessment["teacher_id"],

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
            assessment["opening_time"],

        "closing_time":
            assessment["closing_time"],

        "duration_minutes":
            duration_minutes,

        "pdf_upload_duration_minutes":
            pdf_upload_duration,

        "max_proctoring_flags":
            assessment[
                "max_proctoring_flags"
            ]
    }

    existing = db.assessments.find_one(
        duplicate_query
    )

    if existing:

        raise ValueError(
            "An identical assessment already exists."
        )

    # ======================================================
    # CREATE DOCUMENT
    # ======================================================

    # Make sure the value is explicitly present before
    # sending the data to the model.
    assessment[
        "pdf_upload_duration_minutes"
    ] = pdf_upload_duration

    document = assessment_document(
        assessment
    )

    try:

        result = db.assessments.insert_one(
            document
        )

    except DuplicateKeyError:

        # --------------------------------------------------
        # In case a unique database index catches the same
        # assessment concurrently.
        # --------------------------------------------------

        raise ValueError(
            "An identical assessment already exists."
        )

    document["_id"] = result.inserted_id

    return document


# ==========================================================
# GET ASSESSMENT BY ID
# ==========================================================

def get_assessment_by_id(
    assessment_id: str
):

    try:

        return db.assessments.find_one(
            {
                "_id":
                    ObjectId(
                        assessment_id
                    )
            }
        )

    except Exception:

        return None


# ==========================================================
# GET TEACHER ASSESSMENTS
# ==========================================================

def get_teacher_assessments(
    teacher_id: str
):

    return list(

        db.assessments.find(

            {
                "teacher_id":
                    teacher_id
            }

        ).sort(

            "created_at",
            -1
        )
    )


# ==========================================================
# UPDATE ASSESSMENT
# ==========================================================
#
# Only DRAFT assessments can be updated.
#
# Published assessments are immutable.
#
# PDF duration is also validated against the EXISTING
# overall assessment duration.
#
# This is important when the teacher changes only:
#
#     pdf_upload_duration_minutes
#
# without changing:
#
#     duration_minutes
# ==========================================================

def update_assessment(
    assessment_id: str,
    teacher_id: str,
    updates: dict
):

    if not updates:

        return get_assessment_by_id(
            assessment_id
        )

    # ======================================================
    # GET EXISTING ASSESSMENT
    # ======================================================

    existing = get_assessment_by_id(
        assessment_id
    )

    if not existing:

        return None

    # ======================================================
    # OWNERSHIP
    # ======================================================

    if existing.get(
        "teacher_id"
    ) != teacher_id:

        return None

    # ======================================================
    # ONLY DRAFT
    # ======================================================

    if existing.get(
        "status"
    ) != "DRAFT":

        return None

    # ======================================================
    # DETERMINE FINAL DURATION
    # ======================================================
    #
    # If teacher is changing duration_minutes, use the new
    # value.
    #
    # Otherwise use the existing value.
    # ======================================================

    final_duration_minutes = updates.get(

        "duration_minutes",

        existing.get(
            "duration_minutes"
        )
    )

    # ======================================================
    # DETERMINE FINAL PDF DURATION
    # ======================================================

    final_pdf_upload_duration = updates.get(

        "pdf_upload_duration_minutes",

        existing.get(
            "pdf_upload_duration_minutes",
            0
        )
    )

    # ======================================================
    # VALIDATE PDF DURATION
    # ======================================================

    if final_pdf_upload_duration is None:

        final_pdf_upload_duration = existing.get(
            "pdf_upload_duration_minutes",
            0
        )

    if final_pdf_upload_duration < 0:

        raise ValueError(
            "PDF upload duration cannot be negative."
        )

    if (
        final_pdf_upload_duration > 0
        and
        final_pdf_upload_duration >= final_duration_minutes
    ):

        raise ValueError(
            "PDF upload duration must be greater than 0 "
            "and less than the overall assessment duration."
        )

    # ======================================================
    # PUT FINAL PDF DURATION INTO UPDATES
    # ======================================================

    updates[
        "pdf_upload_duration_minutes"
    ] = final_pdf_upload_duration

    # ======================================================
    # BUILD FINAL ASSESSMENT VALUES
    #
    # These values are used for duplicate detection.
    # ======================================================

    final_values = {

        "teacher_id":
            existing["teacher_id"],

        "title":
            updates.get(
                "title",
                existing["title"]
            ),

        "description":
            updates.get(
                "description",
                existing.get("description")
            ),

        "branch":
            updates.get(
                "branch",
                existing["branch"]
            ),

        "semester":
            updates.get(
                "semester",
                existing["semester"]
            ),

        "opening_time":
            updates.get(
                "opening_time",
                existing["opening_time"]
            ),

        "closing_time":
            updates.get(
                "closing_time",
                existing["closing_time"]
            ),

        "duration_minutes":
            final_duration_minutes,

        "pdf_upload_duration_minutes":
            final_pdf_upload_duration,

        "max_proctoring_flags":
            updates.get(
                "max_proctoring_flags",
                existing["max_proctoring_flags"]
            )
    }

    # ======================================================
    # DUPLICATE CHECK
    #
    # IMPORTANT:
    #
    # Exclude the current assessment itself.
    #
    # Otherwise updating an assessment could detect itself
    # as a duplicate.
    # ======================================================

    duplicate_query = {

        "_id":
            {
                "$ne":
                    existing["_id"]
            },

        "teacher_id":
            final_values["teacher_id"],

        "title":
            final_values["title"],

        "description":
            final_values["description"],

        "branch":
            final_values["branch"],

        "semester":
            final_values["semester"],

        "opening_time":
            final_values["opening_time"],

        "closing_time":
            final_values["closing_time"],

        "duration_minutes":
            final_values["duration_minutes"],

        "pdf_upload_duration_minutes":
            final_values[
                "pdf_upload_duration_minutes"
            ],

        "max_proctoring_flags":
            final_values[
                "max_proctoring_flags"
            ]
    }

    duplicate = db.assessments.find_one(
        duplicate_query
    )

    if duplicate:

        raise ValueError(
            "An identical assessment already exists."
        )

    # ======================================================
    # UPDATED TIMESTAMP
    # ======================================================

    updates["updated_at"] = (
        datetime.now(
            timezone.utc
        )
    )

    # ======================================================
    # UPDATE
    # ======================================================

    try:

        result = db.assessments.find_one_and_update(

            {
                "_id":
                    existing["_id"],

                "teacher_id":
                    teacher_id,

                "status":
                    "DRAFT"
            },

            {
                "$set":
                    updates
            },

            return_document=
                ReturnDocument.AFTER
        )

        return result

    except DuplicateKeyError:

        raise ValueError(
            "An identical assessment already exists."
        )


# ==========================================================
# DELETE ASSESSMENT
# ==========================================================
#
# Only DRAFT assessments can be deleted.
#
# Published assessments cannot be deleted.
# ==========================================================

def delete_assessment(
    assessment_id: str,
    teacher_id: str
):

    try:

        result = db.assessments.delete_one(

            {
                "_id":
                    ObjectId(
                        assessment_id
                    ),

                "teacher_id":
                    teacher_id,

                "status":
                    "DRAFT"
            }
        )

        return (
            result.deleted_count
            == 1
        )

    except Exception:

        return False


# ==========================================================
# CREATE NOTIFICATIONS FOR ELIGIBLE STUDENTS
# ==========================================================

def create_assessment_notifications(
    assessment: dict
):

    assessment_id = str(
        assessment["_id"]
    )

    students = list(

        db.users.find(

            {
                "role":
                    "student",

                "branch":
                    assessment["branch"],

                "semester":
                    assessment["semester"]
            }
        )
    )

    created_notifications = []

    for student in students:

        student_id = str(
            student["_id"]
        )

        # --------------------------------------------------
        # PREVENT DUPLICATE NOTIFICATION
        # --------------------------------------------------

        if notification_exists(

            student_id,

            assessment_id
        ):

            continue

        # --------------------------------------------------
        # CREATE NOTIFICATION
        # --------------------------------------------------

        notification = create_notification(

            {

                "student_id":
                    student_id,

                "assessment_id":
                    assessment_id,

                "notification_type":
                    "ASSESSMENT_PUBLISHED",

                "title":
                    "New assessment available",

                "message":
                    (
                        f'{assessment["title"]} '
                        "has been published and is "
                        "available for you."
                    )
            }
        )

        created_notifications.append(
            notification
        )

    return created_notifications


# ==========================================================
# PUBLISH ASSESSMENT
# ==========================================================
#
# Only DRAFT assessments can be published.
#
# Student notifications are created only after successful
# publication.
# ==========================================================

def publish_assessment(
    assessment_id: str,
    teacher_id: str
):

    now = datetime.now(
        timezone.utc
    )

    try:

        result = db.assessments.find_one_and_update(

            {
                "_id":
                    ObjectId(
                        assessment_id
                    ),

                "teacher_id":
                    teacher_id,

                "status":
                    "DRAFT"
            },

            {
                "$set": {

                    "status":
                        "PUBLISHED",

                    "published_at":
                        now,

                    "updated_at":
                        now
                }
            },

            return_document=
                ReturnDocument.AFTER
        )

        # --------------------------------------------------
        # ASSESSMENT COULD NOT BE PUBLISHED
        # --------------------------------------------------

        if not result:

            return None

        # --------------------------------------------------
        # CREATE STUDENT NOTIFICATIONS
        # --------------------------------------------------

        create_assessment_notifications(
            result
        )

        return result

    except Exception:

        return None