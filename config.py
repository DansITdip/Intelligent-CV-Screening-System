import os

# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


# =========================================================
# APPLICATION CONFIGURATION
# =========================================================

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "intelligent-cv-screening-secret-key-2026"
)

DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

APP_NAME = "Intelligent CV Screening System"
APP_VERSION = "1.0.0"
ORGANIZATION_NAME = "AI Recruitment Intelligence"


# =========================================================
# FILE UPLOAD CONFIGURATION
# =========================================================

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

MAX_CONTENT_LENGTH = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "pdf",
    "docx"
}


# =========================================================
# DATABASE CONFIGURATION
# =========================================================
# Local computer:
#     Uses XAMPP/MySQL localhost by default.
#
# Render:
#     Uses the environment variables configured in Render.
# =========================================================

DB_HOST = os.environ.get(
    "DB_HOST",
    "localhost"
)

DB_PORT = int(
    os.environ.get(
        "DB_PORT",
        "3306"
    )
)

DB_NAME = os.environ.get(
    "DB_NAME",
    "cv_screening_system"
)

DB_USER = os.environ.get(
    "DB_USER",
    "root"
)

DB_PASSWORD = os.environ.get(
    "DB_PASSWORD",
    ""
)


# =========================================================
# AI MATCHING WEIGHTS
# =========================================================

TECHNICAL_SKILLS_WEIGHT = 40
WORK_EXPERIENCE_WEIGHT = 25
EDUCATION_WEIGHT = 15
JOB_RELEVANCE_WEIGHT = 20


# =========================================================
# AI FEATURES
# =========================================================

AUTO_SKILL_EXTRACTION = True
AUTO_CANDIDATE_SCORING = True
AI_RECOMMENDATION = True


# =========================================================
# CREATE REQUIRED DIRECTORIES
# =========================================================

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================================
# CONFIGURATION INFORMATION
# =========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("INTELLIGENT CV SCREENING SYSTEM")
    print("=" * 60)

    print(f"Application      : {APP_NAME}")
    print(f"Version          : {APP_VERSION}")
    print(f"Organization     : {ORGANIZATION_NAME}")

    print()
    print("Database Configuration")
    print("-" * 60)

    print(f"Host             : {DB_HOST}")
    print(f"Port             : {DB_PORT}")
    print(f"Database         : {DB_NAME}")
    print(f"User             : {DB_USER}")

    print()
    print("AI Matching Weights")
    print("-" * 60)

    print(f"Technical Skills : {TECHNICAL_SKILLS_WEIGHT}%")
    print(f"Experience       : {WORK_EXPERIENCE_WEIGHT}%")
    print(f"Education        : {EDUCATION_WEIGHT}%")
    print(f"Job Relevance    : {JOB_RELEVANCE_WEIGHT}%")

    print()
    print(f"Upload Folder    : {UPLOAD_FOLDER}")
    print("Maximum CV Size  : 10 MB")

    print("=" * 60)