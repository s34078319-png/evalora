from datetime import datetime, timezone


def user_document(user: dict):

    now = datetime.now(timezone.utc)

    document = {

        "name":
            user["name"],

        "username":
            user["username"],

        "email":
            user["email"],

        "hashed_password":
            user["hashed_password"],

        "role":
            user["role"],

        "bio":
            user.get("bio"),

        "profile_photo":
            user.get("profile_photo"),

        "created_at":
            now,

        "updated_at":
            now
    }

    # ======================================================
    # STUDENT-SPECIFIC DATA
    # ======================================================

    if user["role"] == "student":

        document["branch"] = user["branch"]

        document["semester"] = user["semester"]

    # ======================================================
    # TEACHER-SPECIFIC DATA
    # ======================================================

    if user["role"] == "teacher":

        document["department"] = user["department"]

    return document