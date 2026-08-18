from datetime import datetime

from pydantic import BaseModel


# ==========================================================
# NOTIFICATION RESPONSE
# ==========================================================

class NotificationResponse(BaseModel):

    id: str

    student_id: str

    assessment_id: str

    notification_type: str

    title: str

    message: str

    is_read: bool

    created_at: datetime

    updated_at: datetime