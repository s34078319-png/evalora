import asyncio
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi.staticfiles import StaticFiles

from app.database.mongodb import (
    test_database_connection
)

from app.database.indexes import (
    create_all_indexes
)

from app.routes.upload import (
    router as upload_router
)

from app.routes.student_assessment import (
    router as student_assessment_router
)

from app.routes.notification import (
    router as notification_router
)

from app.routes.student_attempt import (
    router as student_attempt_router
)

from app.routes.student_session import (
    router as student_session_router
)

from app.routes.section import (
    router as section_router
)

from app.routes.assessment import (
    router as assessment_router
)

from app.routes.question import (
    router as question_router
)

from app.routes.auth import (
    router as auth_router
)

from app.routes.test_auth import (
    router as test_auth_router
)
from app.routes.face_verification import (
    router as face_verification_router
)

from app.services.session_expiration_service import (
    session_expiration_worker
)


# ==========================================================
# APPLICATION LIFESPAN
# ==========================================================

@asynccontextmanager
async def lifespan(
    app: FastAPI
):

    # ------------------------------------------------------
    # DATABASE INDEXES
    # ------------------------------------------------------

    create_all_indexes()

    # ------------------------------------------------------
    # START SESSION EXPIRATION WORKER
    # ------------------------------------------------------

    expiration_task = asyncio.create_task(
        session_expiration_worker()
    )

    print(
        "Session expiration worker started."
    )

    try:

        yield

    finally:

        # --------------------------------------------------
        # STOP BACKGROUND WORKER
        # --------------------------------------------------

        expiration_task.cancel()

        try:

            await expiration_task

        except asyncio.CancelledError:

            pass

        print(
            "Session expiration worker stopped."
        )


# ==========================================================
# FASTAPI APPLICATION
# ==========================================================

app = FastAPI(

    title="Evalora Backend",

    description="Backend API for Evalora",

    version="1.0.0",

    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# STATIC UPLOADS
# ==========================================================

app.mount(

    "/uploads",

    StaticFiles(
        directory="uploads"
    ),

    name="uploads"
)


# ==========================================================
# AUTH ROUTES
# ==========================================================

app.include_router(
    auth_router
)

app.include_router(
    test_auth_router
)


# ==========================================================
# TEACHER / ASSESSMENT ROUTES
# ==========================================================

app.include_router(
    assessment_router
)

app.include_router(
    section_router
)

app.include_router(
    question_router
)

app.include_router(
    upload_router
)
app.include_router(
    face_verification_router
)

# ==========================================================
# STUDENT ROUTES
# ==========================================================

app.include_router(
    student_assessment_router
)

app.include_router(
    notification_router
)

app.include_router(
    student_attempt_router
)

app.include_router(
    student_session_router
)

# ==========================================================
# ROOT
# ==========================================================

@app.get("/")
def root():

    return {

        "message":
            "Evalora backend is running.",

        "database":
            "MongoDB"
    }


# ==========================================================
# DATABASE HEALTH
# ==========================================================

@app.get(
    "/health/database"
)
def database_health():

    connected = (
        test_database_connection()
    )

    if not connected:

        return {

            "status":
                "error",

            "database":
                "MongoDB",

            "connected":
                False
        }

    return {

        "status":
            "ok",

        "database":
            "MongoDB",

        "connected":
            True
    }