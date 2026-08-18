from datetime import datetime, timezone

from bson import ObjectId

from app.database.mongodb import db

from app.models.notification_model import (
    notification_document
)


# ==========================================================
# CREATE NOTIFICATION
# ==========================================================

def create_notification(
    notification: dict
):

    document = notification_document(
        notification
    )

    result = db.notifications.insert_one(
        document
    )

    document["_id"] = result.inserted_id

    return document


# ==========================================================
# CHECK IF NOTIFICATION ALREADY EXISTS
# ==========================================================

def notification_exists(
    student_id: str,
    assessment_id: str
) -> bool:

    notification = db.notifications.find_one({

        "student_id":
            student_id,

        "assessment_id":
            assessment_id
    })

    return notification is not None


# ==========================================================
# GET STUDENT NOTIFICATIONS
# ==========================================================

def get_student_notifications(
    student_id: str
):

    return list(

        db.notifications.find({

            "student_id":
                student_id

        }).sort(

            "created_at",
            -1
        )
    )


# ==========================================================
# GET UNREAD NOTIFICATIONS
# ==========================================================

def get_unread_student_notifications(
    student_id: str
):

    return list(

        db.notifications.find({

            "student_id":
                student_id,

            "is_read":
                False

        }).sort(

            "created_at",
            -1
        )
    )


# ==========================================================
# MARK NOTIFICATION AS READ
# ==========================================================

def mark_notification_read(
    notification_id: str,
    student_id: str
):

    try:

        return db.notifications.find_one_and_update(

            {
                "_id":
                    ObjectId(
                        notification_id
                    ),

                "student_id":
                    student_id
            },

            {
                "$set": {

                    "is_read":
                        True,

                    "updated_at":
                        datetime.now(
                            timezone.utc
                        )
                }
            },

            return_document=True
        )

    except Exception:

        return None