import asyncio
from datetime import datetime, timezone

from app.database.mongodb import db
from app.crud.session_crud import expire_session_if_needed


# ==========================================================
# SESSION EXPIRATION CHECK INTERVAL
# ==========================================================

SESSION_EXPIRATION_CHECK_INTERVAL = 1


# ==========================================================
# EXPIRE ALL DUE SESSIONS
# ==========================================================

def expire_due_sessions():

    now = datetime.now(
        timezone.utc
    )

    # ------------------------------------------------------
    # Find active sessions whose deadline has passed.
    # ------------------------------------------------------

    sessions = list(
        db.sessions.find(
            {
                "active": True,
                "deadline": {
                    "$lte": now
                }
            }
        )
    )

    expired_count = 0

    # ------------------------------------------------------
    # Expire each session.
    # ------------------------------------------------------

    for session in sessions:

        result = expire_session_if_needed(
            session
        )

        if (
            result
            and
            result.get("active") is False
        ):

            expired_count += 1

    return expired_count


# ==========================================================
# BACKGROUND EXPIRATION WORKER
# ==========================================================

async def session_expiration_worker():

    while True:

        try:

            expire_due_sessions()

        except Exception as exc:

            print(
                "Session expiration worker error:",
                exc
            )

        await asyncio.sleep(
            SESSION_EXPIRATION_CHECK_INTERVAL
        )