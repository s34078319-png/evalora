from bson import ObjectId

from app.database.mongodb import db
from app.models.user_model import user_document


# ==========================================================
# NORMALIZE USERNAME
# ==========================================================

def normalize_username(
    username: str
) -> str:

    return username.strip().lower()


# ==========================================================
# NORMALIZE EMAIL
# ==========================================================

def normalize_email(
    email: str
) -> str:

    return email.strip().lower()


# ==========================================================
# FIND USER BY USERNAME
# ==========================================================

def get_user_by_username(
    username: str
):

    return db.users.find_one(
        {
            "username":
                normalize_username(username)
        }
    )


# ==========================================================
# FIND USER BY EMAIL
# ==========================================================

def get_user_by_email(
    email: str
):

    return db.users.find_one(
        {
            "email":
                normalize_email(email)
        }
    )


# ==========================================================
# FIND USER BY LOGIN
#
# Login can be:
# - username
# - email
# ==========================================================

def get_user_by_login(
    login: str
):

    normalized_login = login.strip().lower()

    return db.users.find_one(
        {
            "$or": [
                {
                    "username":
                        normalized_login
                },
                {
                    "email":
                        normalized_login
                }
            ]
        }
    )


# ==========================================================
# FIND USER BY ID
# ==========================================================

def get_user_by_id(
    user_id: str
):

    try:

        object_id = ObjectId(
            user_id
        )

    except Exception:

        return None

    return db.users.find_one(
        {
            "_id":
                object_id
        }
    )


# ==========================================================
# CREATE USER
# ==========================================================

def create_user(
    user: dict
):

    # ------------------------------------------------------
    # Normalize identity fields before database insertion.
    # ------------------------------------------------------

    user["username"] = normalize_username(
        user["username"]
    )

    user["email"] = normalize_email(
        user["email"]
    )

    document = user_document(
        user
    )

    result = db.users.insert_one(
        document
    )

    document["_id"] = result.inserted_id

    return document