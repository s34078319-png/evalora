from datetime import (
    datetime,
    timezone,
    timedelta
)

from bson import ObjectId
from pymongo import ReturnDocument

from app.database.mongodb import db

from app.models.session_model import (
    session_document
)

from app.crud.attempt_crud import (
    complete_attempt,
    update_attempt
)


# ==========================================================
# CREATE SESSION
# ==========================================================

def create_session(
    session: dict
):

    document = session_document(
        session
    )

    result = db.sessions.insert_one(
        document
    )

    document["_id"] = (
        result.inserted_id
    )

    return document


# ==========================================================
# GET SESSION BY ID
# ==========================================================

def get_session_by_id(
    session_id: str
):

    try:

        return db.sessions.find_one(

            {
                "_id":
                    ObjectId(
                        session_id
                    )
            }
        )

    except Exception:

        return None


# ==========================================================
# GET SESSION BY ATTEMPT
# ==========================================================

def get_session_by_attempt(
    attempt_id: str
):

    return db.sessions.find_one(

        {
            "attempt_id":
                attempt_id
        }
    )


# ==========================================================
# GET ACTIVE SESSION
# ==========================================================

def get_active_session(
    student_id: str,
    assessment_id: str
):

    session = db.sessions.find_one(

        {
            "student_id":
                student_id,

            "assessment_id":
                assessment_id,

            "active":
                True
        }
    )

    if not session:

        return None

    return expire_session_if_needed(
        session
    )


# ==========================================================
# NORMALIZE UTC DATETIME
# ==========================================================

def normalize_utc(
    value: datetime
):

    if value is None:

        return None

    if value.tzinfo is None:

        return value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


# ==========================================================
# EXPIRE SESSION IF NEEDED
# ==========================================================
#
# IMPORTANT:
#
# The session does NOT expire before face verification.
#
# Timer starts only after:
#
#     face_verified = True
#
# Once deadline is reached:
#
#     session.active = False
#     session.ended_at = now
#
# AND:
#
#     attempt.completed = True
#     attempt.completion_reason = TIME_EXPIRED
#
# ==========================================================

def expire_session_if_needed(
    session: dict
):

    if not session:

        return None

    # ------------------------------------------------------
    # Already inactive
    # ------------------------------------------------------

    if not session.get(
        "active",
        False
    ):

        return session

    # ------------------------------------------------------
    # Face not verified
    #
    # Timer has not started.
    # ------------------------------------------------------

    if not session.get(
        "face_verified",
        False
    ):

        return session

    # ------------------------------------------------------
    # Get deadline
    # ------------------------------------------------------

    deadline = session.get(
        "deadline"
    )

    if not deadline:

        return session

    deadline = normalize_utc(
        deadline
    )

    # ------------------------------------------------------
    # Current UTC time
    # ------------------------------------------------------

    now = datetime.now(
        timezone.utc
    )

    # ------------------------------------------------------
    # Still active
    # ------------------------------------------------------

    if now < deadline:

        return session

    # ======================================================
    # SESSION EXPIRED
    # ======================================================

    try:

        result = (
            db.sessions.find_one_and_update(

                {
                    "_id":
                        session["_id"],

                    "active":
                        True,

                    "face_verified":
                        True
                },

                {
                    "$set": {

                        "active":
                            False,

                        "ended_at":
                            now,

                        "updated_at":
                            now
                    }
                },

                return_document=
                    ReturnDocument.AFTER
            )
        )

        # --------------------------------------------------
        # Finalize corresponding attempt
        # --------------------------------------------------

        if result:

            attempt_id = result.get(
                "attempt_id"
            )

            if attempt_id:

                complete_attempt(

                    attempt_id,

                    "TIME_EXPIRED"
                )

        return result or session

    except Exception:

        return session


# ==========================================================
# GET SESSION WITH EXPIRATION CHECK
# ==========================================================

def get_session_with_expiration_check(
    session_id: str
):

    session = get_session_by_id(
        session_id
    )

    if not session:

        return None

    return expire_session_if_needed(
        session
    )


# ==========================================================
# START SESSION AFTER FACE VERIFICATION
# ==========================================================
#
# THIS IS THE MAIN CHANGE.
#
# Before face verification:
#
#     session.face_verified = False
#
# After successful verification:
#
#     session.face_verified = True
#     session.started_at = NOW
#     session.deadline = NOW + duration
#     session.active = True
#
# AND THE ATTEMPT IS UPDATED WITH THE SAME TIMER:
#
#     attempt.started_at = NOW
#     attempt.deadline = NOW + duration
#
# ==========================================================

def start_session_after_face_verification(
    session_id: str,
    duration_minutes: int
):

    # ======================================================
    # VALIDATE DURATION
    # ======================================================

    if duration_minutes is None:

        return None

    try:

        duration_minutes = int(
            duration_minutes
        )

    except (
        TypeError,
        ValueError
    ):

        return None

    if duration_minutes <= 0:

        return None

    # ======================================================
    # SESSION ID
    # ======================================================

    try:

        session_object_id = ObjectId(
            session_id
        )

    except Exception:

        return None

    # ======================================================
    # CURRENT UTC TIME
    # ======================================================

    now = datetime.now(
        timezone.utc
    )

    # ======================================================
    # CALCULATE DEADLINE
    # ======================================================

    deadline = (

        now

        +

        timedelta(
            minutes=duration_minutes
        )
    )

    # ======================================================
    # START SESSION ATOMICALLY
    # ======================================================
    #
    # Only a session that is:
    #
    # active = True
    # face_verified = False
    #
    # can start.
    #
    # Therefore repeated webcam requests cannot restart
    # the timer.
    #
    # ======================================================

    try:

        result = (
            db.sessions.find_one_and_update(

                {
                    "_id":
                        session_object_id,

                    "active":
                        True,

                    "face_verified":
                        False
                },

                {
                    "$set": {

                        "face_verified":
                            True,

                        "started_at":
                            now,

                        "deadline":
                            deadline,

                        "ended_at":
                            None,

                        "updated_at":
                            now
                    }
                },

                return_document=
                    ReturnDocument.AFTER
            )
        )

    except Exception:

        return None

    # ======================================================
    # SESSION COULD NOT BE STARTED
    # ======================================================

    if not result:

        return None

    # ======================================================
    # UPDATE CORRESPONDING ATTEMPT
    # ======================================================
    #
    # The attempt must use the SAME timer as the session.
    #
    # ======================================================

    attempt_id = result.get(
        "attempt_id"
    )

    if attempt_id:

        try:

            updated_attempt = update_attempt(

                attempt_id,

                {
                    "started_at":
                        now,

                    "deadline":
                        deadline,

                    "completed":
                        False,

                    "submitted_at":
                        None,

                    "completion_reason":
                        None
                }
            )

            # ------------------------------------------------
            # If attempt update failed, roll session back.
            # ------------------------------------------------

            if not updated_attempt:

                db.sessions.find_one_and_update(

                    {
                        "_id":
                            session_object_id,

                        "active":
                            True,

                        "face_verified":
                            True
                    },

                    {
                        "$set": {

                            "face_verified":
                                False,

                            "started_at":
                                None,

                            "deadline":
                                None,

                            "ended_at":
                                None,

                            "updated_at":
                                datetime.now(
                                    timezone.utc
                                )
                        }
                    },

                    return_document=
                        ReturnDocument.AFTER
                )

                return None

        except Exception:

            # ----------------------------------------------
            # Roll back session if attempt update fails.
            # ----------------------------------------------

            db.sessions.find_one_and_update(

                {
                    "_id":
                        session_object_id,

                    "active":
                        True,

                    "face_verified":
                        True
                },

                {
                    "$set": {

                        "face_verified":
                            False,

                        "started_at":
                            None,

                        "deadline":
                            None,

                        "ended_at":
                            None,

                        "updated_at":
                            datetime.now(
                                timezone.utc
                            )
                    }
                },

                return_document=
                    ReturnDocument.AFTER
            )

            return None

    # ======================================================
    # RETURN UPDATED SESSION
    # ======================================================

    return result


# ==========================================================
# UPDATE SESSION
# ==========================================================

def update_session(
    session_id: str,
    updates: dict
):

    if not updates:

        return get_session_by_id(
            session_id
        )

    updates["updated_at"] = (
        datetime.now(
            timezone.utc
        )
    )

    try:

        result = (
            db.sessions.find_one_and_update(

                {
                    "_id":
                        ObjectId(
                            session_id
                        )
                },

                {
                    "$set":
                        updates
                },

                return_document=
                    ReturnDocument.AFTER
            )
        )

        return result

    except Exception:

        return None


# ==========================================================
# END SESSION
# ==========================================================

def end_session(
    session_id: str
):

    now = datetime.now(
        timezone.utc
    )

    try:

        result = (
            db.sessions.find_one_and_update(

                {
                    "_id":
                        ObjectId(
                            session_id
                        ),

                    "active":
                        True
                },

                {
                    "$set": {

                        "active":
                            False,

                        "ended_at":
                            now,

                        "updated_at":
                            now
                    }
                },

                return_document=
                    ReturnDocument.AFTER
            )
        )

        # --------------------------------------------------
        # Finalize attempt
        # --------------------------------------------------

        if result:

            attempt_id = result.get(
                "attempt_id"
            )

            if attempt_id:

                complete_attempt(

                    attempt_id,

                    "SESSION_ENDED"
                )

        return result

    except Exception:

        return None


# ==========================================================
# INCREMENT PROCTORING FLAGS
# ==========================================================

def increment_proctoring_flags(
    session_id: str
):

    try:

        result = (
            db.sessions.find_one_and_update(

                {
                    "_id":
                        ObjectId(
                            session_id
                        )
                },

                {
                    "$inc": {

                        "proctoring_flags":
                            1

                    },

                    "$set": {

                        "updated_at":
                            datetime.now(
                                timezone.utc
                            )

                    }
                },

                return_document=
                    ReturnDocument.AFTER
            )
        )

        return result

    except Exception:

        return None