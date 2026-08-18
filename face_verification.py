
import os

import cv2
import numpy as np

from insightface.app import FaceAnalysis


# ==========================================================
# INSIGHTFACE CONFIGURATION
# ==========================================================

FACE_MODEL_NAME = "buffalo_s"

FACE_DETECTION_SIZE = (
    320,
    320
)

# Cosine similarity threshold.
#
# Higher = stricter verification.
#
# Keep this configurable so it can be tuned later
# using real verification tests.
FACE_MATCH_THRESHOLD = 0.45


# ==========================================================
# LOAD INSIGHTFACE MODEL
# ==========================================================

try:

    face_app = FaceAnalysis(
        name=FACE_MODEL_NAME,
        providers=[
            "CPUExecutionProvider"
        ]
    )

    face_app.prepare(
        ctx_id=-1,
        det_size=FACE_DETECTION_SIZE
    )

except Exception as e:

    raise RuntimeError(
        "Unable to load the InsightFace model. "
        f"Original error: {str(e)}"
    )


# ==========================================================
# LOAD IMAGE
# ==========================================================

def load_image(
    image_path: str
):
    """
    Load an image from disk.

    Returns:
        numpy image array

    Raises:
        ValueError if image cannot be loaded.
    """

    if not os.path.exists(
        image_path
    ):

        raise ValueError(
            "Reference image was not found."
        )

    image = cv2.imread(
        image_path
    )

    if image is None:

        raise ValueError(
            "Unable to read reference image."
        )

    return image


# ==========================================================
# GET FACE EMBEDDING
# ==========================================================

def get_face_embedding(
    image
):
    """
    Detect exactly one usable face and return
    its normalized face embedding.

    For assessment verification we intentionally
    require exactly one face.

    This prevents situations where:
    - no face is visible
    - multiple people are visible
    """

    if image is None:

        raise ValueError(
            "Invalid image supplied for face verification."
        )

    faces = face_app.get(
        image
    )

    if len(faces) == 0:

        raise ValueError(
            "No face detected in the image."
        )

    if len(faces) > 1:

        raise ValueError(
            "Multiple faces detected. "
            "Only one person must be visible."
        )

    face = faces[0]

    embedding = face.embedding

    if embedding is None:

        raise ValueError(
            "Unable to generate face embedding."
        )

    embedding = np.asarray(
        embedding,
        dtype=np.float32
    )

    norm = np.linalg.norm(
        embedding
    )

    if norm == 0:

        raise ValueError(
            "Invalid face embedding."
        )

    embedding = (
        embedding / norm
    )

    return embedding


# ==========================================================
# COSINE SIMILARITY
# ==========================================================

def cosine_similarity(
    embedding_a,
    embedding_b
) -> float:

    a = np.asarray(
        embedding_a,
        dtype=np.float32
    )

    b = np.asarray(
        embedding_b,
        dtype=np.float32
    )

    norm_a = np.linalg.norm(
        a
    )

    norm_b = np.linalg.norm(
        b
    )

    if (
        norm_a == 0
        or
        norm_b == 0
    ):

        raise ValueError(
            "Cannot compare invalid face embeddings."
        )

    return float(
        np.dot(
            a,
            b
        )
        /
        (
            norm_a
            *
            norm_b
        )
    )


# ==========================================================
# VERIFY FACE
# ==========================================================

def verify_face(
    reference_image_path: str,
    live_image
):
    """
    Compare the registered student photograph
    against the live webcam image.

    Returns:

    {
        "verified": bool,
        "similarity": float
    }
    """

    # ------------------------------------------------------
    # LOAD REGISTERED PHOTO
    # ------------------------------------------------------

    reference_image = load_image(
        reference_image_path
    )

    # ------------------------------------------------------
    # CREATE REFERENCE EMBEDDING
    # ------------------------------------------------------

    reference_embedding = (
        get_face_embedding(
            reference_image
        )
    )

    # ------------------------------------------------------
    # CREATE LIVE EMBEDDING
    # ------------------------------------------------------

    live_embedding = (
        get_face_embedding(
            live_image
        )
    )

    # ------------------------------------------------------
    # COMPARE
    # ------------------------------------------------------

    similarity = cosine_similarity(
        reference_embedding,
        live_embedding
    )

    verified = (
        similarity
        >=
        FACE_MATCH_THRESHOLD
    )

    return {

        "verified":
            verified,

        "similarity":
            round(
                similarity,
                4
            )
    }

