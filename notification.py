from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from app.schemas.notification_schema import (
    NotificationResponse
)

from app.crud.notification_crud import (
    get_student_notifications,
    get_unread_student_notifications,
    mark_notification_read
)

from app.dependencies.auth_dependencies import (
    require_student
)


router = APIRouter(
    prefix="/student",
    tags=["Student Notifications"]
)


# ==========================================================
# SERIALIZE NOTIFICATION
# ==========================================================

def serialize_notification(
    notification: dict
):

    return {

        "id":
            str(
                notification["_id"]
            ),

        "student_id":
            notification["student_id"],

        "assessment_id":
            notification["assessment_id"],

        "notification_type":
            notification["notification_type"],

        "title":
            notification["title"],

        "message":
            notification["message"],

        "is_read":
            notification["is_read"],

        "created_at":
            notification["created_at"],

        "updated_at":
            notification["updated_at"]
    }


# ==========================================================
# GET ALL STUDENT NOTIFICATIONS
# ==========================================================

@router.get(
    "/notifications",
    response_model=list[NotificationResponse]
)
def get_notifications(

    current_student: dict = Depends(
        require_student
    )
):

    student_id = str(
        current_student["_id"]
    )

    notifications = (
        get_student_notifications(
            student_id
        )
    )

    return [

        serialize_notification(
            notification
        )

        for notification in notifications
    ]


# ==========================================================
# GET UNREAD NOTIFICATIONS
# ==========================================================

@router.get(
    "/notifications/unread",
    response_model=list[NotificationResponse]
)
def get_unread_notifications(

    current_student: dict = Depends(
        require_student
    )
):

    student_id = str(
        current_student["_id"]
    )

    notifications = (
        get_unread_student_notifications(
            student_id
        )
    )

    return [

        serialize_notification(
            notification
        )

        for notification in notifications
    ]


# ==========================================================
# MARK NOTIFICATION AS READ
# ==========================================================

@router.put(
    "/notifications/{notification_id}/read",
    response_model=NotificationResponse
)
def read_notification(

    notification_id: str,

    current_student: dict = Depends(
        require_student
    )
):

    student_id = str(
        current_student["_id"]
    )

    notification = mark_notification_read(

        notification_id,

        student_id
    )

    if not notification:

        raise HTTPException(

            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Notification not found."
        )

    return serialize_notification(
        notification
    )