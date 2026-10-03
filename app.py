from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session
)

from werkzeug.utils import secure_filename

import os
from datetime import datetime


# =========================================================
# CONFIGURATION
# =========================================================

from config import (
    SECRET_KEY,
    DEBUG,
    UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH,
    ALLOWED_EXTENSIONS,
    APP_NAME,
    APP_VERSION,
    ORGANIZATION_NAME
)


# =========================================================
# DATABASE
# =========================================================

try:

    from database.database import get_db

    DATABASE_AVAILABLE = True

except Exception as error:

    print(
        f"Database module import error: {error}"
    )

    DATABASE_AVAILABLE = False


# =========================================================
# AI SCREENING ENGINE
# =========================================================

try:

    from services.screening_engine import (
        extract_cv_text,
        calculate_match_score,
        JOB_PROFILES
    )

    SCREENING_ENGINE_AVAILABLE = True

    print(
        "AI screening engine loaded successfully."
    )

except Exception as error:

    print(
        f"AI screening engine import error: {error}"
    )

    extract_cv_text = None
    calculate_match_score = None
    JOB_PROFILES = {}

    SCREENING_ENGINE_AVAILABLE = False


# =========================================================
# APPLICATION INITIALIZATION
# =========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = SECRET_KEY
app.config["DEBUG"] = DEBUG
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


# =========================================================
# DIRECTORIES
# =========================================================

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# =========================================================
# DATABASE CONNECTION HELPER
# =========================================================

def get_database():
    """
    Return the application database object.
    """

    if not DATABASE_AVAILABLE:

        raise RuntimeError(
            "Database module is not available."
        )

    database = get_db()

    try:

        if hasattr(
            database,
            "reconnect"
        ):

            database.reconnect()

    except Exception:

        pass

    return database


# =========================================================
# GET UNDERLYING MYSQL CONNECTION
# =========================================================

def get_database_connection(database):
    """
    Recover the underlying MySQL connection
    from the database wrapper.
    """

    possible_attributes = (
        "connection",
        "conn",
        "_connection",
        "_conn"
    )

    for attribute in possible_attributes:

        try:

            if hasattr(
                database,
                attribute
            ):

                connection = getattr(
                    database,
                    attribute
                )

                if connection is not None:

                    return connection

        except Exception:

            pass

    return None


# =========================================================
# DATABASE WRITE HELPER
# =========================================================

def execute_database_write(
    query,
    parameters=()
):
    """
    Execute INSERT / UPDATE / DELETE operations.
    """

    database = get_database()

    connection = None
    cursor = None

    try:

        connection = get_database_connection(
            database
        )

        if connection is not None:

            cursor = connection.cursor()

            cursor.execute(
                query,
                parameters
            )

            connection.commit()

            return cursor.lastrowid


        for method_name in (
            "execute",
            "execute_query",
            "run_query"
        ):

            if hasattr(
                database,
                method_name
            ):

                method = getattr(
                    database,
                    method_name
                )

                result = method(
                    query,
                    parameters
                )

                if hasattr(
                    result,
                    "lastrowid"
                ):

                    try:

                        return result.lastrowid

                    except Exception:

                        pass

                if isinstance(
                    result,
                    int
                ):

                    return result

                return None


        raise RuntimeError(
            "No supported database write method was found."
        )

    except Exception:

        if connection is not None:

            try:

                connection.rollback()

            except Exception:

                pass

        raise

    finally:

        if cursor is not None:

            try:

                cursor.close()

            except Exception:

                pass


# =========================================================
# DATABASE TABLE COLUMNS
# =========================================================

def get_table_columns(
    table_name
):
    """
    Return actual columns from a MySQL table.
    """

    database = get_database()

    connection = None
    cursor = None

    try:

        connection = get_database_connection(
            database
        )

        if connection is not None:

            cursor = connection.cursor()

            cursor.execute(
                f"SHOW COLUMNS FROM `{table_name}`"
            )

            rows = cursor.fetchall()

            columns = []

            for row in rows or []:

                if isinstance(
                    row,
                    dict
                ):

                    column = (
                        row.get("Field")
                        or row.get("field")
                        or row.get("COLUMN_NAME")
                        or row.get("column_name")
                    )

                else:

                    column = (
                        row[0]
                        if row
                        else None
                    )

                if column:

                    columns.append(
                        str(column)
                    )

            return columns


        rows = database.fetch_all(
            """
            SELECT
                COLUMN_NAME
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = %s
            ORDER BY ordinal_position
            """,
            (
                table_name,
            )
        ) or []


        columns = []

        for row in rows:

            if isinstance(
                row,
                dict
            ):

                column = (
                    row.get("COLUMN_NAME")
                    or row.get("column_name")
                )

            else:

                column = (
                    row[0]
                    if row
                    else None
                )

            if column:

                columns.append(
                    str(column)
                )

        return columns


    except Exception as error:

        print(
            f"Could not inspect table {table_name}: {error}"
        )

        return []

    finally:

        if cursor is not None:

            try:

                cursor.close()

            except Exception:

                pass


# =========================================================
# FIND EXISTING COLUMN
# =========================================================

def find_existing_column(
    columns,
    options
):
    """
    Return the first matching column.
    """

    column_set = set(
        columns or []
    )

    for option in options:

        if option in column_set:

            return option

    return None


# =========================================================
# SCORE HELPER
# =========================================================

def safe_score(
    value
):
    """
    Convert a score safely to a 0-100 range.
    """

    try:

        value = float(
            value or 0
        )

    except Exception:

        value = 0.0

    return round(
        max(
            0.0,
            min(
                100.0,
                value
            )
        ),
        2
    )


# =========================================================
# FILE HELPERS
# =========================================================

def allowed_file(
    filename
):
    """
    Check supported CV file extension.
    """

    if not filename:

        return False

    if "." not in filename:

        return False

    extension = (
        filename
        .rsplit(
            ".",
            1
        )[1]
        .lower()
    )

    return extension in ALLOWED_EXTENSIONS


def get_file_size_mb(
    file
):
    """
    Return uploaded file size in MB.
    """

    try:

        file.seek(
            0,
            os.SEEK_END
        )

        size = file.tell()

        file.seek(
            0
        )

        return (
            size
            /
            (
                1024
                *
                1024
            )
        )

    except Exception:

        return 0


# =========================================================
# SAVE CV DOCUMENT METADATA
# =========================================================

def save_cv_document(
    candidate_id,
    original_filename,
    stored_filename,
    file_path
):
    """
    Save CV metadata according to the actual
    cv_documents database schema.
    """

    try:

        columns = get_table_columns(
            "cv_documents"
        )

        if not columns:

            print(
                "cv_documents table could not be inspected."
            )

            return False


        candidate_column = find_existing_column(
            columns,
            [
                "candidate_id",
                "candidateID",
                "candidateId"
            ]
        )


        path_column = find_existing_column(
            columns,
            [
                "file_path",
                "filepath",
                "path",
                "cv_path",
                "document_path",
                "stored_path"
            ]
        )


        uploaded_column = find_existing_column(
            columns,
            [
                "uploaded_at",
                "created_at",
                "date_uploaded",
                "upload_date"
            ]
        )


        original_column = find_existing_column(
            columns,
            [
                "original_filename",
                "original_name"
            ]
        )


        stored_column = find_existing_column(
            columns,
            [
                "stored_filename",
                "file_name",
                "filename",
                "document_name",
                "name"
            ]
        )


        if not candidate_column:

            print(
                "cv_documents has no candidate reference column."
            )

            return False


        if (
            not path_column
            and not original_column
            and not stored_column
        ):

            print(
                "cv_documents has no usable file column."
            )

            return False


        insert_columns = []
        values = []


        insert_columns.append(
            candidate_column
        )

        values.append(
            candidate_id
        )


        if original_column:

            insert_columns.append(
                original_column
            )

            values.append(
                original_filename
            )


        if stored_column:

            if stored_column not in insert_columns:

                insert_columns.append(
                    stored_column
                )

                values.append(
                    stored_filename
                )


        if path_column:

            insert_columns.append(
                path_column
            )

            values.append(
                file_path
            )


        if uploaded_column:

            insert_columns.append(
                uploaded_column
            )

            values.append(
                datetime.now()
            )


        placeholders = ", ".join(
            ["%s"] * len(values)
        )


        query = f"""
            INSERT INTO cv_documents
            (
                {", ".join(
                    f"`{column}`"
                    for column in insert_columns
                )}
            )
            VALUES
            (
                {placeholders}
            )
        """


        execute_database_write(
            query,
            tuple(values)
        )


        return True


    except Exception as error:

        print(
            "CV document metadata error:",
            error
        )

        return False


# =========================================================
# GET CV PATH FOR CANDIDATE
# =========================================================

def get_candidate_cv_path(
    candidate_id
):
    """
    Retrieve the latest physical CV file for a candidate.
    """

    try:

        database = get_database()

        columns = get_table_columns(
            "cv_documents"
        )

        if not columns:

            return None


        candidate_column = find_existing_column(
            columns,
            [
                "candidate_id",
                "candidateID",
                "candidateId"
            ]
        )


        path_column = find_existing_column(
            columns,
            [
                "file_path",
                "filepath",
                "path",
                "cv_path",
                "document_path",
                "stored_path"
            ]
        )


        original_column = find_existing_column(
            columns,
            [
                "original_filename",
                "original_name"
            ]
        )


        stored_column = find_existing_column(
            columns,
            [
                "stored_filename",
                "file_name",
                "filename",
                "document_name",
                "name"
            ]
        )


        id_column = find_existing_column(
            columns,
            [
                "id",
                "ID"
            ]
        )


        uploaded_column = find_existing_column(
            columns,
            [
                "uploaded_at",
                "created_at",
                "date_uploaded",
                "upload_date"
            ]
        )


        if not candidate_column:

            return None


        selected_columns = []


        if path_column:

            selected_columns.append(
                f"`{path_column}`"
            )


        if stored_column:

            selected_columns.append(
                f"`{stored_column}`"
            )


        if (
            original_column
            and original_column != stored_column
        ):

            selected_columns.append(
                f"`{original_column}`"
            )


        if not selected_columns:

            return None


        ordering = ""


        if id_column:

            ordering = (
                f" ORDER BY `{id_column}` DESC"
            )

        elif uploaded_column:

            ordering = (
                f" ORDER BY `{uploaded_column}` DESC"
            )


        row = database.fetch_one(

            f"""
            SELECT
                {", ".join(selected_columns)}
            FROM cv_documents
            WHERE `{candidate_column}` = %s
            {ordering}
            LIMIT 1
            """,

            (
                candidate_id,
            )

        )


        if not row:

            return None


        if path_column:

            saved_path = row.get(
                path_column
            )


            if saved_path:

                saved_path = str(
                    saved_path
                ).strip()


                if os.path.exists(
                    saved_path
                ):

                    return saved_path


                possible_path = os.path.join(
                    os.getcwd(),
                    saved_path
                )


                if os.path.exists(
                    possible_path
                ):

                    return possible_path


        filename_candidates = []


        if stored_column:

            value = row.get(
                stored_column
            )

            if value:

                filename_candidates.append(
                    str(value)
                )


        if original_column:

            value = row.get(
                original_column
            )

            if value:

                filename_candidates.append(
                    str(value)
                )


        for filename in filename_candidates:

            safe_name = secure_filename(
                filename
            )


            possible_path = os.path.join(
                UPLOAD_FOLDER,
                safe_name
            )


            if os.path.exists(
                possible_path
            ):

                return possible_path


            try:

                for saved_filename in os.listdir(
                    UPLOAD_FOLDER
                ):

                    if saved_filename.endswith(
                        "_" + safe_name
                    ):

                        candidate_path = os.path.join(
                            UPLOAD_FOLDER,
                            saved_filename
                        )

                        if os.path.isfile(
                            candidate_path
                        ):

                            return candidate_path

            except Exception:

                pass


        return None


    except Exception as error:

        print(
            "Candidate CV path error:",
            error
        )

        return None


# =========================================================
# CANDIDATE LOOKUP
# =========================================================

def get_candidate(
    candidate_id
):
    """
    Retrieve one candidate.
    """

    try:

        database = get_database()

        return database.fetch_one(

            """
            SELECT
                *
            FROM candidates
            WHERE id = %s
            LIMIT 1
            """,

            (
                candidate_id,
            )

        )

    except Exception as error:

        print(
            "Candidate lookup error:",
            error
        )

        return None


# =========================================================
# CANDIDATE DATABASE LIST
# =========================================================

def get_database_candidates():
    """
    Return real candidates and latest screening data.
    """

    try:

        database = get_database()

        rows = database.fetch_all(

            """
            SELECT
                id,
                full_name,
                email,
                target_position,
                status,
                created_at
            FROM candidates
            ORDER BY id DESC
            """

        ) or []


        for candidate in rows:

            candidate_id = candidate.get(
                "id"
            )


            candidate["match_score"] = 0
            candidate["recommendation"] = ""
            candidate["skills"] = []
            candidate["cv_uploaded"] = False
            candidate["compatibility_band"] = ""


            try:

                screening = database.fetch_one(

                    """
                    SELECT
                        *
                    FROM screening_results
                    WHERE candidate_id = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,

                    (
                        candidate_id,
                    )

                )


                if screening:

                    score = (

                        screening.get(
                            "overall_score"
                        )

                        if screening.get(
                            "overall_score"
                        ) is not None

                        else screening.get(
                            "match_score",
                            0
                        )

                    )


                    candidate["match_score"] = safe_score(
                        score
                    )


                    candidate["recommendation"] = (

                        screening.get(
                            "recommendation",
                            ""
                        )
                        or ""

                    )


                    candidate["compatibility_band"] = (

                        screening.get(
                            "compatibility_band",
                            ""
                        )
                        or ""

                    )


            except Exception as error:

                print(
                    "Candidate screening lookup error:",
                    error
                )


            try:

                skills_rows = database.fetch_all(

                    """
                    SELECT
                        *
                    FROM candidate_skills
                    WHERE candidate_id = %s
                    ORDER BY id ASC
                    """,

                    (
                        candidate_id,
                    )

                ) or []


                for row in skills_rows:

                    skill = (

                        row.get(
                            "skill_name"
                        )
                        or row.get(
                            "skill"
                        )
                        or row.get(
                            "name"
                        )

                    )


                    if skill:

                        candidate["skills"].append(
                            skill
                        )


            except Exception as error:

                print(
                    "Candidate skills lookup error:",
                    error
                )


            try:

                cv_result = database.fetch_one(

                    """
                    SELECT
                        COUNT(*) AS total
                    FROM cv_documents
                    WHERE candidate_id = %s
                    """,

                    (
                        candidate_id,
                    )

                )


                candidate["cv_uploaded"] = (

                    int(
                        cv_result.get(
                            "total",
                            0
                        ) or 0
                    ) > 0

                    if cv_result

                    else False

                )


            except Exception:

                candidate["cv_uploaded"] = False


        return rows


    except Exception as error:

        print(
            f"Candidate database error: {error}"
        )

        return []


# =========================================================
# JOB DATABASE
# =========================================================

def get_database_jobs():
    """
    Return real job profiles.
    """

    try:

        database = get_database()

        rows = database.fetch_all(

            """
            SELECT
                id,
                job_title,
                department,
                employment_type,
                experience_required,
                location,
                status,
                created_at
            FROM job_profiles
            ORDER BY id DESC
            """

        ) or []


        return rows


    except Exception as error:

        print(
            f"Job database error: {error}"
        )

        return []


# =========================================================
# DASHBOARD STATISTICS
# =========================================================

def get_dashboard_statistics():
    """
    Return real recruitment statistics.
    """

    statistics = {

        "total_candidates": 0,

        "cv_uploaded": 0,

        "screened_candidates": 0,

        "shortlisted_candidates": 0,

        "active_jobs": 0,

        "average_match": 0,

        "most_detected_skill": "No data",

        "requirements_met": 0,

        "average_processing_time": "N/A"

    }


    try:

        database = get_database()


        try:

            result = database.fetch_one(

                """
                SELECT
                    COUNT(*) AS total
                FROM candidates
                """

            )


            if result:

                statistics[
                    "total_candidates"
                ] = int(

                    result.get(
                        "total",
                        0
                    )
                    or 0

                )


        except Exception as error:

            print(
                "Total candidates error:",
                error
            )


        try:

            result = database.fetch_one(

                """
                SELECT
                    COUNT(*) AS total
                FROM cv_documents
                """

            )


            if result:

                statistics[
                    "cv_uploaded"
                ] = int(

                    result.get(
                        "total",
                        0
                    )
                    or 0

                )


        except Exception:

            statistics[
                "cv_uploaded"
            ] = statistics[
                "total_candidates"
            ]


        # -------------------------------------------------
        # GET ONLY THE LATEST SCREENING RESULT
        # FOR EACH CANDIDATE
        # -------------------------------------------------

        all_results = []


        try:

            all_results = database.fetch_all(

                """
                SELECT
                    sr.*
                FROM screening_results sr
                INNER JOIN
                (
                    SELECT
                        candidate_id,
                        MAX(id) AS latest_id
                    FROM screening_results
                    GROUP BY candidate_id
                ) latest
                    ON sr.id = latest.latest_id
                """

            ) or []


        except Exception as error:

            print(
                "Screening statistics error:",
                error
            )


        candidate_ids = set()

        scores = []

        processing_times = []


        for row in all_results:

            candidate_id = row.get(
                "candidate_id"
            )


            if candidate_id is not None:

                candidate_ids.add(
                    candidate_id
                )


            score = (

                row.get(
                    "overall_score"
                )

                if row.get(
                    "overall_score"
                ) is not None

                else row.get(
                    "match_score"
                )

            )


            if score is not None:

                try:

                    scores.append(
                        safe_score(
                            score
                        )
                    )

                except Exception:

                    pass


            processing_time = row.get(
                "processing_time"
            )


            if processing_time is not None:

                try:

                    processing_times.append(
                        float(
                            processing_time
                        )
                    )

                except Exception:

                    pass


        statistics[
            "screened_candidates"
        ] = len(
            candidate_ids
        )


        if scores:

            statistics[
                "average_match"
            ] = round(

                sum(scores)
                /
                len(scores)

            )


        if processing_times:

            average_time = (

                sum(
                    processing_times
                )
                /
                len(
                    processing_times
                )

            )


            statistics[
                "average_processing_time"
            ] = (
                f"{average_time:.2f} sec"
            )


        try:

            result = database.fetch_one(

                """
                SELECT
                    COUNT(*) AS total
                FROM candidates
                WHERE LOWER(status) = 'shortlisted'
                """

            )


            if result:

                statistics[
                    "shortlisted_candidates"
                ] = int(

                    result.get(
                        "total",
                        0
                    )
                    or 0

                )


        except Exception as error:

            print(
                "Shortlisted candidates error:",
                error
            )


        try:

            result = database.fetch_one(

                """
                SELECT
                    COUNT(*) AS total
                FROM job_profiles
                WHERE LOWER(status) = 'active'
                """

            )


            if result:

                statistics[
                    "active_jobs"
                ] = int(

                    result.get(
                        "total",
                        0
                    )
                    or 0

                )


        except Exception as error:

            print(
                "Active jobs error:",
                error
            )


        if scores:

            met = sum(

                1
                for score in scores
                if score >= 70

            )


            statistics[
                "requirements_met"
            ] = round(

                (
                    met
                    /
                    len(scores)
                )
                *
                100

            )


        try:

            skill_rows = database.fetch_all(

                """
                SELECT
                    skill_name
                FROM candidate_skills
                """

            ) or []


            skill_counts = {}


            for row in skill_rows:

                skill = row.get(
                    "skill_name"
                )


                if not skill:

                    continue


                skill_counts[
                    skill
                ] = (

                    skill_counts.get(
                        skill,
                        0
                    )
                    + 1

                )


            if skill_counts:

                statistics[
                    "most_detected_skill"
                ] = max(

                    skill_counts,
                    key=skill_counts.get

                )


        except Exception as error:

            print(
                "Most detected skill error:",
                error
            )


    except Exception as error:

        print(
            "Dashboard statistics error:",
            error
        )


    return statistics


# =========================================================
# TOP CANDIDATES
# =========================================================

def get_top_candidates():
    """
    Return top candidates using their real screening score.
    """

    try:

        candidates_data = (
            get_database_candidates()
        )


        candidates_data.sort(

            key=lambda item: float(

                item.get(
                    "match_score",
                    0
                )
                or 0

            ),

            reverse=True

        )


        return candidates_data[:5]


    except Exception as error:

        print(
            "Top candidates error:",
            error
        )

        return []


# =========================================================
# ACTIVE JOBS
# =========================================================

def get_active_jobs():
    """
    Return active jobs.
    """

    try:

        database = get_database()

        rows = database.fetch_all(

            """
            SELECT
                id,
                job_title,
                department,
                employment_type,
                experience_required,
                location,
                status
            FROM job_profiles
            WHERE LOWER(status) = 'active'
            ORDER BY id DESC
            LIMIT 6
            """

        ) or []


        return rows


    except Exception as error:

        print(
            "Active jobs error:",
            error
        )

        return []


# =========================================================
# ENSURE SCREENING TABLES
# =========================================================

def ensure_screening_tables():
    """
    Create screening support tables where necessary.
    """

    database = get_database()

    connection = get_database_connection(
        database
    )


    if connection is None:

        raise RuntimeError(
            "MySQL connection unavailable."
        )


    cursor = connection.cursor()


    try:

        # -------------------------------------------------
        # SCREENING RESULTS
        # -------------------------------------------------

        cursor.execute(

            """
            CREATE TABLE IF NOT EXISTS screening_results (

                id INT AUTO_INCREMENT PRIMARY KEY,

                candidate_id INT NOT NULL,

                overall_score DECIMAL(6,2)
                    DEFAULT 0,

                match_score DECIMAL(6,2)
                    DEFAULT 0,

                technical_skills_score DECIMAL(6,2)
                    DEFAULT 0,

                experience_score DECIMAL(6,2)
                    DEFAULT 0,

                education_score DECIMAL(6,2)
                    DEFAULT 0,

                relevance_score DECIMAL(6,2)
                    DEFAULT 0,

                recommendation VARCHAR(150)
                    DEFAULT NULL,

                compatibility_band VARCHAR(100)
                    DEFAULT NULL,

                matched_skills TEXT,

                missing_skills TEXT,

                education_summary TEXT,

                experience_years DECIMAL(5,1)
                    DEFAULT 0,

                text_similarity DECIMAL(6,2)
                    DEFAULT 0,

                processing_time DECIMAL(10,3)
                    DEFAULT 0,

                processing_time_ms INT
                    DEFAULT 0,

                created_at DATETIME
                    DEFAULT CURRENT_TIMESTAMP

            )
            """

        )


        # -------------------------------------------------
        # CANDIDATE SKILLS
        # -------------------------------------------------

        cursor.execute(

            """
            CREATE TABLE IF NOT EXISTS candidate_skills (

                id INT AUTO_INCREMENT PRIMARY KEY,

                candidate_id INT NOT NULL,

                skill_name VARCHAR(100) NOT NULL,

                created_at DATETIME
                    DEFAULT CURRENT_TIMESTAMP

            )
            """

        )


        connection.commit()


        # -------------------------------------------------
        # ADD MISSING SCREENING COLUMNS
        # -------------------------------------------------

        existing_columns = set(
            get_table_columns(
                "screening_results"
            )
        )


        required_columns = {

            "overall_score":
                "DECIMAL(6,2) DEFAULT 0",

            "match_score":
                "DECIMAL(6,2) DEFAULT 0",

            "technical_skills_score":
                "DECIMAL(6,2) DEFAULT 0",

            "experience_score":
                "DECIMAL(6,2) DEFAULT 0",

            "education_score":
                "DECIMAL(6,2) DEFAULT 0",

            "relevance_score":
                "DECIMAL(6,2) DEFAULT 0",

            "recommendation":
                "VARCHAR(150) DEFAULT NULL",

            "compatibility_band":
                "VARCHAR(100) DEFAULT NULL",

            "matched_skills":
                "TEXT",

            "missing_skills":
                "TEXT",

            "education_summary":
                "TEXT",

            "experience_years":
                "DECIMAL(5,1) DEFAULT 0",

            "text_similarity":
                "DECIMAL(6,2) DEFAULT 0",

            "processing_time":
                "DECIMAL(10,3) DEFAULT 0",

            "processing_time_ms":
                "INT DEFAULT 0"

        }


        for column, definition in (
            required_columns.items()
        ):

            if column not in existing_columns:

                try:

                    cursor.execute(

                        f"""
                        ALTER TABLE screening_results
                        ADD COLUMN `{column}`
                        {definition}
                        """

                    )

                except Exception as error:

                    print(

                        f"Could not add screening "
                        f"column {column}: {error}"

                    )


        connection.commit()


    except Exception:

        connection.rollback()

        raise


    finally:

        cursor.close()


# =========================================================
# SCREENING RECOMMENDATION
# =========================================================

def build_recommendation(
    score
):
    """
    Describe the compatibility level for recruiter review.
    """

    score = safe_score(
        score
    )


    if score >= 80:

        return (
            "High compatibility - Recruiter review"
        )


    if score >= 60:

        return (
            "Moderate compatibility - Recruiter review"
        )


    return (
        "Lower compatibility - Recruiter review"
    )


# =========================================================
# GET JOB ID FOR POSITION
# =========================================================

def get_job_id_for_position(
    position
):
    """
    Find the database job profile ID that matches
    the candidate's target position.
    """

    database = get_database()


    row = database.fetch_one(

        """
        SELECT
            id
        FROM job_profiles
        WHERE LOWER(TRIM(job_title))
              = LOWER(TRIM(%s))
          AND LOWER(status) = 'active'
        ORDER BY id DESC
        LIMIT 1
        """,

        (
            position,
        )

    )


    if row:

        return row.get(
            "id"
        )


    row = database.fetch_one(

        """
        SELECT
            id
        FROM job_profiles
        WHERE LOWER(TRIM(job_title))
              = LOWER(TRIM(%s))
        ORDER BY id DESC
        LIMIT 1
        """,

        (
            position,
        )

    )


    return (
        row.get("id")
        if row
        else None
    )


# =========================================================
# STORE SCREENING RESULT
# =========================================================

def save_screening_result(
    candidate_id,
    analysis,
    processing_time_seconds,
    position
):
    """
    Save the AI analysis into screening_results.
    """

    columns = get_table_columns(
        "screening_results"
    )


    if not columns:

        raise RuntimeError(
            "screening_results table is unavailable."
        )


    # -----------------------------------------------------
    # JOB PROFILE
    # -----------------------------------------------------

    job_id = get_job_id_for_position(
        position
    )


    if not job_id:

        raise RuntimeError(

            f"No job profile found for target position "
            f"'{position}'. "
            "Create an active job profile before screening."

        )


    # -----------------------------------------------------
    # MAIN SCORE
    # -----------------------------------------------------

    match_score = safe_score(

        analysis.get(
            "match_score",
            analysis.get(
                "overall_score",
                0
            )
        )

    )


    skill_score = safe_score(

        analysis.get(
            "skill_score",
            analysis.get(
                "technical_skills_score",
                0
            )
        )

    )


    education_score = safe_score(

        analysis.get(
            "education_score",
            0
        )

    )


    experience_score = safe_score(

        analysis.get(
            "experience_score",
            0
        )

    )


    title_score = safe_score(

        analysis.get(
            "title_score",
            0
        )

    )


    text_similarity = (
        analysis.get(
            "text_similarity",
            0
        )
    )


    try:

        text_similarity = float(
            text_similarity or 0
        )

    except Exception:

        text_similarity = 0


    # -----------------------------------------------------
    # TEXT SIMILARITY NORMALIZATION
    # -----------------------------------------------------

    if 0 <= text_similarity <= 1:

        text_similarity_score = (
            text_similarity * 100
        )

    else:

        text_similarity_score = (
            text_similarity
        )


    text_similarity_score = safe_score(
        text_similarity_score
    )


    # -----------------------------------------------------
    # RELEVANCE
    # -----------------------------------------------------

    engine_relevance = analysis.get(
        "relevance_score"
    )


    if engine_relevance is not None:

        relevance_score = safe_score(
            engine_relevance
        )

    else:

        relevance_score = safe_score(

            (
                title_score * 0.60
            )
            +
            (
                text_similarity_score * 0.40
            )

        )


    # -----------------------------------------------------
    # EDUCATION SUMMARY
    # -----------------------------------------------------

    education = analysis.get(
        "education",
        {}
    )


    if not isinstance(
        education,
        dict
    ):

        education = {}


    education_levels = education.get(
        "levels",
        []
    )


    education_disciplines = education.get(
        "disciplines",
        []
    )


    education_levels = (
        education_levels
        if isinstance(
            education_levels,
            list
        )
        else []
    )


    education_disciplines = (
        education_disciplines
        if isinstance(
            education_disciplines,
            list
        )
        else []
    )


    education_summary = ", ".join(
        str(item)
        for item in education_levels
        if item
    )


    discipline_text = ", ".join(
        str(item)
        for item in education_disciplines
        if item
    )


    if (
        education_summary
        and discipline_text
    ):

        education_summary += (
            " - "
        )


    education_summary += (
        discipline_text
    )


    # -----------------------------------------------------
    # SKILLS
    # -----------------------------------------------------

    matched_skills = analysis.get(
        "matched_skills",
        []
    )


    missing_skills = analysis.get(
        "missing_skills",
        []
    )


    if not isinstance(
        matched_skills,
        list
    ):

        matched_skills = []


    if not isinstance(
        missing_skills,
        list
    ):

        missing_skills = []


    matched_skills_text = ", ".join(

        str(skill).strip()
        for skill in matched_skills
        if str(skill).strip()

    )


    missing_skills_text = ", ".join(

        str(skill).strip()
        for skill in missing_skills
        if str(skill).strip()

    )


    experience_years = analysis.get(
        "experience_years",
        0
    )


    try:

        experience_years = float(
            experience_years or 0
        )

    except Exception:

        experience_years = 0


    recommendation = (

        analysis.get(
            "recommendation"
        )

        or

        build_recommendation(
            match_score
        )

    )


    compatibility_band = (

        analysis.get(
            "compatibility_band",
            ""
        )
        or ""

    )


    # -----------------------------------------------------
    # DATABASE VALUES
    # -----------------------------------------------------

    values_map = {

        "candidate_id":
            candidate_id,

        "job_id":
            job_id,

        "overall_score":
            match_score,

        "match_score":
            match_score,

        "technical_skills_score":
            skill_score,

        "experience_score":
            experience_score,

        "education_score":
            education_score,

        "relevance_score":
            relevance_score,

        "recommendation":
            recommendation,

        "compatibility_band":
            compatibility_band,

        "matched_skills":
            matched_skills_text,

        "missing_skills":
            missing_skills_text,

        "education_summary":
            education_summary,

        "experience_years":
            experience_years,

        "text_similarity":
            text_similarity_score,

        "processing_time":
            processing_time_seconds,

        "processing_time_ms":
            round(
                processing_time_seconds
                * 1000
            ),

        "created_at":
            datetime.now()

    }


    selected_columns = []
    selected_values = []


    for column, value in (
        values_map.items()
    ):

        if column in columns:

            selected_columns.append(
                f"`{column}`"
            )

            selected_values.append(
                value
            )


    if "candidate_id" not in columns:

        raise RuntimeError(
            "screening_results table is missing candidate_id."
        )


    if (
        "overall_score" not in columns
        and "match_score" not in columns
    ):

        raise RuntimeError(
            "screening_results table has no score column."
        )


    if (
        "job_id" in columns
        and not job_id
    ):

        raise RuntimeError(
            "screening_results requires a valid job_id."
        )


    placeholders = ", ".join(
        ["%s"] * len(
            selected_values
        )
    )


    query = f"""
        INSERT INTO screening_results
        (
            {", ".join(selected_columns)}
        )
        VALUES
        (
            {placeholders}
        )
    """


    return execute_database_write(

        query,

        tuple(
            selected_values
        )

    )


# =========================================================
# STORE DETECTED SKILLS
# =========================================================

def save_candidate_skills(
    candidate_id,
    skills
):
    """
    Replace the candidate's previous detected skills
    with the latest screening skills.
    """

    try:

        database = get_database()

        columns = get_table_columns(
            "candidate_skills"
        )


        candidate_column = find_existing_column(
            columns,
            [
                "candidate_id",
                "candidateID",
                "candidateId"
            ]
        )


        skill_column = find_existing_column(
            columns,
            [
                "skill_name",
                "skill",
                "name"
            ]
        )


        if (
            not candidate_column
            or not skill_column
        ):

            return


        connection = get_database_connection(
            database
        )


        if connection is None:

            return


        cursor = connection.cursor()


        try:

            cursor.execute(

                f"""
                DELETE FROM candidate_skills
                WHERE `{candidate_column}` = %s
                """,

                (
                    candidate_id,
                )

            )


            unique_skills = sorted(

                set(

                    str(skill).strip()
                    for skill in (
                        skills or []
                    )
                    if str(skill).strip()

                )

            )


            for skill in unique_skills:

                cursor.execute(

                    f"""
                    INSERT INTO candidate_skills
                    (
                        `{candidate_column}`,
                        `{skill_column}`
                    )
                    VALUES
                    (
                        %s,
                        %s
                    )
                    """,

                    (
                        candidate_id,
                        skill
                    )

                )


            connection.commit()


        except Exception:

            connection.rollback()

            raise


        finally:

            cursor.close()


    except Exception as error:

        print(
            "Candidate skills save error:",
            error
        )


# =========================================================
# UPDATE CANDIDATE STATUS
# =========================================================

def update_candidate_status(
    candidate_id,
    status
):
    """
    Update candidate status.
    """

    try:

        execute_database_write(

            """
            UPDATE candidates
            SET status = %s
            WHERE id = %s
            """,

            (
                status,
                candidate_id
            )

        )


    except Exception as error:

        print(
            "Candidate status update error:",
            error
        )


# =========================================================
# RUN REAL AI SCREENING
# =========================================================

def run_real_screening(
    candidate_id,
    file_path,
    position
):
    """
    Complete real CV screening workflow:

    CV
    -> Text extraction
    -> NLP processing
    -> Skill extraction
    -> Education analysis
    -> Experience analysis
    -> Job matching
    -> Score
    -> Database
    """

    if not SCREENING_ENGINE_AVAILABLE:

        raise RuntimeError(
            "AI screening engine is not available."
        )


    if extract_cv_text is None:

        raise RuntimeError(
            "CV extraction engine is unavailable."
        )


    if calculate_match_score is None:

        raise RuntimeError(
            "CV matching engine is unavailable."
        )


    if not file_path:

        raise ValueError(
            "CV file path is required."
        )


    if not os.path.exists(
        file_path
    ):

        raise FileNotFoundError(
            f"CV file not found: {file_path}"
        )


    if not position:

        raise ValueError(
            "Target position is required."
        )


    # -----------------------------------------------------
    # Ensure screening tables
    # -----------------------------------------------------

    ensure_screening_tables()


    started = datetime.now()


    # -----------------------------------------------------
    # Extract text
    # -----------------------------------------------------

    cv_text = extract_cv_text(
        file_path
    )


    if not cv_text:

        raise ValueError(
            "No text could be extracted from the CV."
        )


    cv_text = str(
        cv_text
    ).strip()


    if not cv_text:

        raise ValueError(
            "The CV contains no readable text."
        )


    # -----------------------------------------------------
    # AI matching engine
    # -----------------------------------------------------

    analysis = calculate_match_score(

        cv_text,

        position

    )


    if not isinstance(
        analysis,
        dict
    ):

        raise RuntimeError(
            "The AI engine returned an invalid result."
        )


    finished = datetime.now()


    processing_time_seconds = (

        finished - started
    ).total_seconds()


    # -----------------------------------------------------
    # Save result
    # -----------------------------------------------------

    result_id = save_screening_result(

        candidate_id,

        analysis,

        processing_time_seconds,

        position

    )


    # -----------------------------------------------------
    # Save matched skills
    # -----------------------------------------------------

    save_candidate_skills(

        candidate_id,

        analysis.get(
            "matched_skills",
            []
        )

    )


    # -----------------------------------------------------
    # Update status
    # -----------------------------------------------------

    update_candidate_status(

        candidate_id,

        "Screened"

    )


    # -----------------------------------------------------
    # Prepare return data
    # -----------------------------------------------------

    match_score = safe_score(

        analysis.get(
            "match_score",
            0
        )

    )


    return {

        "success":
            True,

        "screening_result_id":
            result_id,

        "candidate_id":
            candidate_id,

        "position":
            position,

        "match_score":
            match_score,

        "overall_score":
            match_score,

        "compatibility_band":
            analysis.get(
                "compatibility_band",
                ""
            )
            or "",

        "recommendation":
            (
                analysis.get(
                    "recommendation"
                )
                or
                build_recommendation(
                    match_score
                )
            ),

        "matched_skills":
            analysis.get(
                "matched_skills",
                []
            )
            or [],

        "missing_skills":
            analysis.get(
                "missing_skills",
                []
            )
            or [],

        "education":
            analysis.get(
                "education",
                {}
            )
            or {},

        "experience_years":
            analysis.get(
                "experience_years",
                0
            )
            or 0,

        "skill_score":
            safe_score(
                analysis.get(
                    "skill_score",
                    0
                )
            ),

        "education_score":
            safe_score(
                analysis.get(
                    "education_score",
                    0
                )
            ),

        "experience_score":
            safe_score(
                analysis.get(
                    "experience_score",
                    0
                )
            ),

        "title_score":
            safe_score(
                analysis.get(
                    "title_score",
                    0
                )
            ),

        "text_similarity":
            analysis.get(
                "text_similarity",
                0
            ),

        "processing_time":
            round(
                processing_time_seconds,
                3
            ),

        "processing_time_ms":
            round(
                processing_time_seconds
                * 1000
            ),

        "cv_text_length":
            len(
                cv_text
            )

    }


# =========================================================
# GLOBAL TEMPLATE VARIABLES
# =========================================================

@app.context_processor
def inject_global_variables():

    return {

        "app_name":
            APP_NAME,

        "app_version":
            APP_VERSION,

        "organization_name":
            ORGANIZATION_NAME,

        "current_year":
            datetime.now().year

    }


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return redirect(
        url_for(
            "login"
        )
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=[
        "GET",
        "POST"
    ]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()


        if (
            not username
            or not password
        ):

            flash(
                "Please enter your username and password.",
                "error"
            )

            return render_template(
                "login.html"
            )


        session[
            "username"
        ] = username


        return redirect(
            url_for(
                "dashboard"
            )
        )


    return render_template(
        "login.html"
    )


# =========================================================
# SIGN UP
# =========================================================

@app.route(
    "/signup",
    methods=[
        "GET",
        "POST"
    ]
)
def signup():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()


        if (
            not username
            or not password
        ):

            flash(
                "Please complete all required fields.",
                "error"
            )

            return render_template(
                "login.html"
            )


        flash(
            "Account information received successfully.",
            "success"
        )


        return redirect(
            url_for(
                "login"
            )
        )


    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for(
            "login"
        )
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@app.route("/dashboard.html")
def dashboard():

    statistics = (
        get_dashboard_statistics()
    )

    top_candidates = (
        get_top_candidates()
    )

    active_jobs = (
        get_active_jobs()
    )


    stats = {

        "total_candidates":
            statistics[
                "total_candidates"
            ],

        "cv_uploaded":
            statistics[
                "cv_uploaded"
            ],

        "screened_candidates":
            statistics[
                "screened_candidates"
            ],

        "shortlisted_candidates":
            statistics[
                "shortlisted_candidates"
            ],

        "average_match":
            statistics[
                "average_match"
            ],

        "active_jobs":
            statistics[
                "active_jobs"
            ],

        "most_detected_skill":
            statistics[
                "most_detected_skill"
            ],

        "requirements_met":
            statistics[
                "requirements_met"
            ],

        "average_processing_time":
            statistics[
                "average_processing_time"
            ]

    }


    return render_template(

        "dashboard.html",

        statistics=statistics,

        stats=stats,

        candidates=top_candidates,

        jobs=active_jobs,

        top_candidates=top_candidates,

        active_jobs=active_jobs

    )


# =========================================================
# CANDIDATES
# =========================================================

@app.route("/candidates")
@app.route("/candidates.html")
def candidates():

    candidate_data = (
        get_database_candidates()
    )


    return render_template(

        "candidates.html",

        candidates=candidate_data

    )


# =========================================================
# UPLOAD CV
# =========================================================

@app.route(
    "/upload-cv",
    methods=[
        "GET",
        "POST"
    ]
)
@app.route(
    "/upload_cv",
    methods=[
        "GET",
        "POST"
    ]
)
def upload_cv():

    if request.method == "GET":

        return render_template(
            "upload_cv.html"
        )


    cv_file = request.files.get(
        "cv_file"
    )


    candidate_name = request.form.get(
        "candidate_name",
        ""
    ).strip()


    email = request.form.get(
        "email",
        ""
    ).strip()


    position = request.form.get(
        "position",
        ""
    ).strip()


    job_profile = request.form.get(
        "job_profile",
        ""
    ).strip()


    if not candidate_name:

        return jsonify({

            "success":
                False,

            "message":
                "Candidate name is required."

        }), 400


    if not position:

        return jsonify({

            "success":
                False,

            "message":
                "Target position is required."

        }), 400


    if not cv_file:

        return jsonify({

            "success":
                False,

            "message":
                "Please select a CV file."

        }), 400


    if not cv_file.filename:

        return jsonify({

            "success":
                False,

            "message":
                "The selected file has no filename."

        }), 400


    if not allowed_file(
        cv_file.filename
    ):

        return jsonify({

            "success":
                False,

            "message":
                "Only PDF and DOCX CV files are allowed."

        }), 400


    file_size = get_file_size_mb(
        cv_file
    )


    if file_size > 10:

        return jsonify({

            "success":
                False,

            "message":
                "The CV file must not exceed 10 MB."

        }), 400


    original_filename = (
        cv_file.filename
    )


    safe_filename = secure_filename(
        original_filename
    )


    if not safe_filename:

        return jsonify({

            "success":
                False,

            "message":
                "Invalid CV filename."

        }), 400


    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )


    stored_filename = (
        f"{timestamp}_{safe_filename}"
    )


    file_path = os.path.join(

        UPLOAD_FOLDER,

        stored_filename

    )


    try:

        cv_file.save(
            file_path
        )


        candidate_id = execute_database_write(

            """
            INSERT INTO candidates
            (
                full_name,
                email,
                target_position,
                status,
                created_at
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,

            (
                candidate_name,
                email or None,
                position,
                "Pending",
                datetime.now()
            )

        )


        if not candidate_id:

            raise RuntimeError(
                "Candidate was not created in the database."
            )


        cv_record_saved = save_cv_document(

            candidate_id,

            original_filename,

            stored_filename,

            file_path

        )


        session[
            "uploaded_cv"
        ] = {

            "candidate_id":
                candidate_id,

            "candidate_name":
                candidate_name,

            "email":
                email,

            "position":
                position,

            "job_profile":
                job_profile,

            "filename":
                stored_filename,

            "original_filename":
                original_filename,

            "file_path":
                file_path

        }


        screening_data = None
        screening_error = None


        try:

            screening_data = run_real_screening(

                candidate_id,

                file_path,

                position

            )


            session[
                "uploaded_cv"
            ][
                "screening_completed"
            ] = True


        except Exception as error:

            screening_error = str(
                error
            )

            print(
                "AI screening error:",
                error
            )

            session[
                "uploaded_cv"
            ][
                "screening_completed"
            ] = False


        if screening_data:

            return jsonify({

                "success":
                    True,

                "message":
                    (
                        "CV uploaded, candidate registered, "
                        "and AI screening completed successfully."
                    ),

                "candidate_id":
                    candidate_id,

                "candidate": {

                    "id":
                        candidate_id,

                    "name":
                        candidate_name,

                    "email":
                        email,

                    "position":
                        position,

                    "status":
                        "Screened"

                },

                "cv_record_saved":
                    cv_record_saved,

                "screening_completed":
                    True,

                "screening":
                    screening_data,

                "results_url":
                    url_for(
                        "results",
                        candidate_id=candidate_id
                    )

            })


        return jsonify({

            "success":
                True,

            "message":
                (
                    "CV uploaded and candidate registered, "
                    "but AI screening could not be completed."
                ),

            "candidate_id":
                candidate_id,

            "candidate": {

                "id":
                    candidate_id,

                "name":
                    candidate_name,

                "email":
                    email,

                "position":
                    position,

                "status":
                    "Pending"

            },

            "cv_record_saved":
                cv_record_saved,

            "screening_completed":
                False,

            "screening_error":
                screening_error,

            "next_step":
                "Retry the screening using the screening API.",

            "results_url":
                url_for(
                    "results",
                    candidate_id=candidate_id
                )

        })


    except Exception as error:

        print(
            "CV upload/database error:",
            error
        )


        try:

            if os.path.exists(
                file_path
            ):

                os.remove(
                    file_path
                )

        except Exception:

            pass


        return jsonify({

            "success":
                False,

            "message":
                f"CV upload failed: {error}"

        }), 500


# =========================================================
# JOBS  (FINAL FIXED VERSION)
# =========================================================

@app.route("/jobs", methods=["GET", "POST"])
@app.route("/jobs.html", methods=["GET", "POST"])
def jobs():

    if request.method == "POST":

        job_title = request.form.get("job_title", "").strip()
        department = request.form.get("department", "").strip()
        employment_type = request.form.get("employment_type", "").strip()
        experience_required = request.form.get("experience_required", "").strip()
        job_description = request.form.get("job_description", "").strip()
        required_skills = request.form.get("required_skills", "").strip()
        minimum_education = request.form.get("minimum_education", "").strip()
        location = request.form.get("location", "").strip()

        if not all([job_title, department, employment_type, experience_required, job_description, minimum_education, location]):
            flash("Please fill all required fields.", "error")
            return redirect(url_for("jobs"))

        try:
            database = get_database()
            columns = get_table_columns("job_profiles")

            values_map = {
                "job_title": job_title,
                "department": department,
                "employment_type": employment_type,
                "experience_required": experience_required,
                "job_description": job_description,
                "required_skills": required_skills,
                "minimum_education": minimum_education,
                "location": location,
                "status": "Active",
                "created_by": 1,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }

            selected_columns = []
            selected_values = []

            for column in columns:
                if column in values_map:
                    selected_columns.append(column)
                    selected_values.append(values_map[column])

            if "job_title" not in selected_columns or "status" not in selected_columns:
                flash("Database structure error. Could not save job profile.", "error")
                return redirect(url_for("jobs"))

            placeholders = ", ".join(["%s"] * len(selected_values))

            query = f"""
                INSERT INTO job_profiles
                (
                    {", ".join(f"`{column}`" for column in selected_columns)}
                )
                VALUES
                (
                    {placeholders}
                )
            """

            execute_database_write(query, tuple(selected_values))
            flash("Job profile created successfully!", "success")

        except Exception as e:
            print("Job creation error:", e)
            flash(f"Failed to create job profile: {str(e)}", "error")

        return redirect(url_for("jobs"))

    # ====================== GET Request ======================
    job_data = get_database_jobs()
    statistics = get_dashboard_statistics()

    # Calculate extra stats for the counters
    total_jobs = len(job_data)
    full_time_jobs = sum(1 for job in job_data if str(job.get("employment_type", "")).lower() in ["full time", "full-time", "fulltime"])
    departments = len(set(job.get("department") for job in job_data if job.get("department")))

    stats = {
        "total_candidates": statistics["total_candidates"],
        "cv_uploaded": statistics["cv_uploaded"],
        "screened_candidates": statistics["screened_candidates"],
        "shortlisted_candidates": statistics["shortlisted_candidates"],
        "average_match": statistics["average_match"],
        "active_jobs": statistics["active_jobs"],
        "most_detected_skill": statistics["most_detected_skill"],
        "requirements_met": statistics["requirements_met"],
        "average_processing_time": statistics["average_processing_time"],

        # New counters
        "total_jobs": total_jobs,
        "full_time_jobs": full_time_jobs,
        "departments": departments
    }

    return render_template(
        "job_description.html",
        jobs=job_data,
        stats=stats,
        statistics=statistics
    )


# =========================================================
# JOB DESCRIPTION
# =========================================================

@app.route("/job-description", methods=["GET", "POST"])
def job_description():

    if request.method == "POST":
        return redirect(url_for("jobs"))

    job_data = get_database_jobs()
    statistics = get_dashboard_statistics()

    total_jobs = len(job_data)
    full_time_jobs = sum(1 for job in job_data if str(job.get("employment_type", "")).lower() in ["full time", "full-time", "fulltime"])
    departments = len(set(job.get("department") for job in job_data if job.get("department")))

    stats = {
        "total_candidates": statistics["total_candidates"],
        "cv_uploaded": statistics["cv_uploaded"],
        "screened_candidates": statistics["screened_candidates"],
        "shortlisted_candidates": statistics["shortlisted_candidates"],
        "average_match": statistics["average_match"],
        "active_jobs": statistics["active_jobs"],
        "most_detected_skill": statistics["most_detected_skill"],
        "requirements_met": statistics["requirements_met"],
        "average_processing_time": statistics["average_processing_time"],
        "total_jobs": total_jobs,
        "full_time_jobs": full_time_jobs,
        "departments": departments
    }

    return render_template(
        "job_description.html",
        jobs=job_data,
        stats=stats,
        statistics=statistics
    )


# =========================================================
# API - CREATE JOB PROFILE
# =========================================================

@app.route(
    "/api/jobs",
    methods=["POST"]
)
def create_job_profile():
    """
    Create a new job profile in the real job_profiles table.
    """

    try:

        data = request.get_json(silent=True) or {}

        if not data:
            data = request.form.to_dict()

        job_title = str(
            data.get("job_title", "")
            or data.get("jobTitle", "")
        ).strip()

        department = str(
            data.get("department", "")
        ).strip()

        employment_type = str(
            data.get("employment_type", "")
            or data.get("employmentType", "")
        ).strip()

        experience_required = str(
            data.get("experience_required", "")
            or data.get("experience", "")
        ).strip()

        job_description_text = str(
            data.get("job_description", "")
            or data.get("description", "")
        ).strip()

        required_skills = str(
            data.get("required_skills", "")
            or data.get("skills", "")
        ).strip()

        minimum_education = str(
            data.get("minimum_education", "")
            or data.get("education", "")
        ).strip()

        location = str(
            data.get("location", "")
        ).strip()

        if not job_title:
            return jsonify({
                "success": False,
                "message": "Job title is required."
            }), 400

        if not department:
            return jsonify({
                "success": False,
                "message": "Department is required."
            }), 400

        if not employment_type:
            return jsonify({
                "success": False,
                "message": "Employment type is required."
            }), 400

        if not experience_required:
            return jsonify({
                "success": False,
                "message": "Experience requirement is required."
            }), 400

        if not job_description_text:
            return jsonify({
                "success": False,
                "message": "Job description is required."
            }), 400

        if not minimum_education:
            return jsonify({
                "success": False,
                "message": "Minimum education is required."
            }), 400

        if not location:
            return jsonify({
                "success": False,
                "message": "Location is required."
            }), 400

        database = get_database()
        columns = get_table_columns("job_profiles")

        if not columns:
            return jsonify({
                "success": False,
                "message": "The job_profiles table could not be inspected."
            }), 500

        values_map = {
            "job_title": job_title,
            "department": department,
            "employment_type": employment_type,
            "experience_required": experience_required,
            "job_description": job_description_text,
            "required_skills": required_skills,
            "minimum_education": minimum_education,
            "location": location,
            "status": "Active",
            "created_by": 1,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        selected_columns = []
        selected_values = []

        for column in columns:
            if column in values_map:
                selected_columns.append(column)
                selected_values.append(values_map[column])

        if "job_title" not in selected_columns:
            return jsonify({
                "success": False,
                "message": "The job_profiles table is missing the job_title column."
            }), 500

        if "status" not in selected_columns:
            return jsonify({
                "success": False,
                "message": "The job_profiles table is missing the status column."
            }), 500

        placeholders = ", ".join(
            ["%s"] * len(selected_values)
        )

        query = f"""
            INSERT INTO job_profiles
            (
                {", ".join(
                    f"`{column}`"
                    for column in selected_columns
                )}
            )
            VALUES
            (
                {placeholders}
            )
        """

        job_id = execute_database_write(
            query,
            tuple(selected_values)
        )

        saved_job = database.fetch_one(
            """
            SELECT
                id,
                job_title,
                department,
                employment_type,
                experience_required,
                location,
                status,
                created_at
            FROM job_profiles
            WHERE id = %s
            LIMIT 1
            """,
            (job_id,)
        ) if job_id else None

        return jsonify({
            "success": True,
            "message": "Job profile created successfully.",
            "job_id": job_id,
            "job": saved_job
        }), 201

    except Exception as error:

        print(
            "Job profile creation error:",
            error
        )

        return jsonify({
            "success": False,
            "message": f"Job profile could not be created: {error}"
        }), 500


# =========================================================
# SCREENING PAGE
# =========================================================

@app.route("/screening")
def screening():

    uploaded = session.get(
        "uploaded_cv"
    )


    if uploaded:

        candidate_id = uploaded.get(
            "candidate_id"
        )


        if candidate_id:

            return redirect(

                url_for(

                    "results",

                    candidate_id=candidate_id

                )

            )


    return redirect(
        url_for(
            "upload_cv"
        )
    )


@app.route("/screen")
def screen():

    return redirect(
        url_for(
            "screening"
        )
    )


# =========================================================
# REAL AI SCREENING API
# =========================================================

@app.route(
    "/api/screen/<int:candidate_id>",
    methods=[
        "GET",
        "POST"
    ]
)
def api_screen_candidate(
    candidate_id
):

    try:

        candidate = get_candidate(
            candidate_id
        )


        if not candidate:

            return jsonify({

                "success":
                    False,

                "message":
                    "Candidate not found."

            }), 404


        position = (

            candidate.get(
                "target_position"
            )
            or
            request.form.get(
                "position",
                ""
            ).strip()

        )


        if not position:

            return jsonify({

                "success":
                    False,

                "message":
                    "Target position is missing."

            }), 400


        file_path = None


        uploaded = session.get(
            "uploaded_cv"
        )


        if uploaded:

            session_candidate_id = uploaded.get(
                "candidate_id"
            )


            if (
                session_candidate_id
                == candidate_id
            ):

                file_path = uploaded.get(
                    "file_path"
                )


        if not file_path:

            file_path = get_candidate_cv_path(
                candidate_id
            )


        if not file_path:

            return jsonify({

                "success":
                    False,

                "message":
                    "No stored CV file could be found for this candidate."

            }), 404


        screening_data = run_real_screening(

            candidate_id,

            file_path,

            position

        )


        session[
            "uploaded_cv"
        ] = {

            "candidate_id":
                candidate_id,

            "candidate_name":
                candidate.get(
                    "full_name",
                    ""
                ),

            "email":
                candidate.get(
                    "email",
                    ""
                ),

            "position":
                position,

            "file_path":
                file_path,

            "screening_completed":
                True

        }


        return jsonify({

            "success":
                True,

            "message":
                "AI CV screening completed successfully.",

            "screening":
                screening_data,

            "results_url":
                url_for(
                    "results",
                    candidate_id=candidate_id
                )

        })


    except Exception as error:

        print(
            "AI screening API error:",
            error
        )


        return jsonify({

            "success":
                False,

            "message":
                f"AI screening failed: {error}"

        }), 500


# =========================================================
# RESULTS
# =========================================================

@app.route("/results")
@app.route(
    "/results/<int:candidate_id>"
)
def results(
    candidate_id=None
):

    if candidate_id is None:

        uploaded = session.get(
            "uploaded_cv"
        )


        if uploaded:

            candidate_id = uploaded.get(
                "candidate_id"
            )


    screening_result = None
    candidate = None


    if candidate_id is not None:

        candidate = get_candidate(
            candidate_id
        )


        try:

            database = get_database()


            screening_result = database.fetch_one(

                """
                SELECT
                    sr.*
                FROM screening_results sr
                WHERE sr.candidate_id = %s
                ORDER BY sr.id DESC
                LIMIT 1
                """,

                (
                    candidate_id,
                )

            )


        except Exception as error:

            print(
                "Results database error:",
                error
            )


    if candidate and screening_result:

        overall_score = (

            screening_result.get(
                "overall_score"
            )

            if screening_result.get(
                "overall_score"
            ) is not None

            else screening_result.get(
                "match_score",
                0
            )

        )


        technical_score = (

            screening_result.get(
                "technical_skills_score"
            )

            if screening_result.get(
                "technical_skills_score"
            ) is not None

            else screening_result.get(
                "skill_score",
                0
            )

        )


        experience_score = screening_result.get(
            "experience_score",
            0
        )


        education_score = screening_result.get(
            "education_score",
            0
        )


        relevance_score = screening_result.get(
            "relevance_score",
            0
        )


        overall_score = safe_score(
            overall_score
        )

        technical_score = safe_score(
            technical_score
        )

        experience_score = safe_score(
            experience_score
        )

        education_score = safe_score(
            education_score
        )

        relevance_score = safe_score(
            relevance_score
        )


        matched_skills = []


        matched_text = (
            screening_result.get(
                "matched_skills"
            )
        )


        if matched_text:

            matched_skills = [

                item.strip()

                for item in str(
                    matched_text
                ).split(",")

                if item.strip()

            ]


        missing_skills = []


        missing_text = (
            screening_result.get(
                "missing_skills"
            )
        )


        if missing_text:

            missing_skills = [

                item.strip()

                for item in str(
                    missing_text
                ).split(",")

                if item.strip()

            ]


        if not matched_skills:

            try:

                database = get_database()


                skill_rows = database.fetch_all(

                    """
                    SELECT
                        skill_name
                    FROM candidate_skills
                    WHERE candidate_id = %s
                    ORDER BY skill_name
                    """,

                    (
                        candidate_id,
                    )

                ) or []


                matched_skills = [

                    row.get(
                        "skill_name"
                    )

                    for row in skill_rows

                    if row.get(
                        "skill_name"
                    )

                ]


            except Exception as error:

                print(
                    "Candidate skill results error:",
                    error
                )


        recommendation = (

            screening_result.get(
                "recommendation"
            )

            or

            build_recommendation(
                overall_score
            )

        )


        result_data = {

            "candidate": {

                "id":
                    candidate_id,

                "name":
                    candidate.get(
                        "full_name",
                        "Candidate"
                    ),

                "email":
                    (
                        candidate.get(
                            "email",
                            ""
                        )
                        or
                        "Not provided"
                    ),

                "position":
                    candidate.get(
                        "target_position",
                        "Not specified"
                    )

            },


            "overall_score":
                overall_score,


            "recommendation":
                recommendation,


            "compatibility_band":
                screening_result.get(
                    "compatibility_band",
                    ""
                )
                or "",


            "scores": {

                "technical_skills":
                    technical_score,

                "work_experience":
                    experience_score,

                "education":
                    education_score,

                "job_relevance":
                    relevance_score

            },


            "matched_skills":
                matched_skills,


            "partial_skills":
                [],


            "missing_skills":
                missing_skills,


            "experience_years":
                float(

                    screening_result.get(
                        "experience_years",
                        0
                    )
                    or 0

                ),


            "processing_time":
                screening_result.get(
                    "processing_time",
                    0
                )
                or 0,


            "processing_time_ms":
                screening_result.get(
                    "processing_time_ms",
                    0
                )
                or 0,


            "screening_id":
                screening_result.get(
                    "id"
                )

        }


    else:

        result_data = {

            "candidate": {

                "id":
                    candidate_id,

                "name":
                    (
                        candidate.get(
                            "full_name",
                            "No screening selected"
                        )
                        if candidate

                        else

                        "No screening selected"
                    ),

                "email":
                    (
                        candidate.get(
                            "email",
                            "Not available"
                        )
                        if candidate

                        else

                        "Not available"
                    )
                    or "Not available",

                "position":
                    (
                        candidate.get(
                            "target_position",
                            "Not available"
                        )
                        if candidate

                        else

                        "Not available"
                    )

            },


            "overall_score":
                0,


            "recommendation":
                "No completed screening result is available yet.",


            "compatibility_band":
                "",


            "scores": {

                "technical_skills":
                    0,

                "work_experience":
                    0,

                "education":
                    0,

                "job_relevance":
                    0

            },


            "matched_skills":
                [],

            "partial_skills":
                [],

            "missing_skills":
                [],

            "experience_years":
                0,

            "processing_time":
                0,

            "processing_time_ms":
                0,

            "screening_id":
                None

        }


    return render_template(

        "results.html",

        result=result_data,

        screening=result_data

    )


# =========================================================
# REPORTS
# =========================================================

@app.route("/reports")
def reports():

    statistics = (
        get_dashboard_statistics()
    )


    report_data = {

        "reference":
            (
                "SCR-"
                +
                datetime.now().strftime(
                    "%Y%m%d%H%M"
                )
            ),

        "generated":
            datetime.now().strftime(
                "%d %B %Y"
            ),

        "candidate":
            "All Candidates",

        "position":
            "Recruitment Screening",

        "score":
            statistics[
                "average_match"
            ],

        "recommendation":
            "Dashboard screening summary"

    }


    return render_template(

        "report.html",

        report=report_data

    )


@app.route("/report")
def report():

    return redirect(
        url_for(
            "reports"
        )
    )


# =========================================================
# SETTINGS
# =========================================================

@app.route("/settings")
def settings():

    database_status = "CONNECTED"


    try:

        database = get_database()


        connection = get_database_connection(
            database
        )


        if connection is not None:

            if hasattr(
                connection,
                "is_connected"
            ):

                if not connection.is_connected():

                    database_status = (
                        "DISCONNECTED"
                    )


    except Exception:

        database_status = (
            "DISCONNECTED"
        )


    settings_data = {

        "technical_skills_weight":
            55,

        "experience_weight":
            15,

        "education_weight":
            20,

        "relevance_weight":
            10,

        "auto_skill_extraction":
            True,

        "auto_candidate_scoring":
            True,

        "ai_recommendation":
            True,

        "system_status":
            "ONLINE",

        "ai_engine":
            (
                "READY"
                if SCREENING_ENGINE_AVAILABLE
                else "ERROR"
            ),

        "database_status":
            database_status,

        "version":
            APP_VERSION

    }


    return render_template(

        "settings.html",

        settings=settings_data

    )


# =========================================================
# API - SYSTEM STATUS
# =========================================================

@app.route("/api/status")
def api_status():

    database_status = "connected"


    try:

        database = get_database()

        connection = get_database_connection(
            database
        )


        if connection is not None:

            if hasattr(
                connection,
                "is_connected"
            ):

                if not connection.is_connected():

                    database_status = (
                        "disconnected"
                    )


    except Exception:

        database_status = (
            "disconnected"
        )


    return jsonify({

        "success":
            True,

        "application":
            APP_NAME,

        "version":
            APP_VERSION,

        "status":
            "online",

        "ai_engine":
            (
                "ready"
                if SCREENING_ENGINE_AVAILABLE
                else "error"
            ),

        "database":
            database_status,

        "timestamp":
            datetime.now().isoformat()

    })


# =========================================================
# API - CANDIDATES
# =========================================================

@app.route("/api/candidates")
def api_candidates():

    candidate_data = (
        get_database_candidates()
    )


    return jsonify({

        "success":
            True,

        "count":
            len(
                candidate_data
            ),

        "candidates":
            candidate_data

    })


# =========================================================
# API - JOBS
# =========================================================

@app.route("/api/jobs")
def api_jobs():

    job_data = (
        get_database_jobs()
    )


    return jsonify({

        "success":
            True,

        "count":
            len(
                job_data
            ),

        "jobs":
            job_data

    })


# =========================================================
# API - DASHBOARD
# =========================================================

@app.route("/api/dashboard")
def api_dashboard():

    statistics = (
        get_dashboard_statistics()
    )

    top_candidates = (
        get_top_candidates()
    )

    active_jobs = (
        get_active_jobs()
    )


    return jsonify({

        "success":
            True,

        "statistics":
            statistics,

        "top_candidates":
            top_candidates,

        "active_jobs":
            active_jobs,

        "timestamp":
            datetime.now().isoformat()

    })


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    if request.path.startswith(
        "/api"
    ):

        return jsonify({

            "success":
                False,

            "message":
                "Requested API endpoint was not found."

        }), 404


    return redirect(
        url_for(
            "dashboard"
        )
    )


@app.errorhandler(413)
def file_too_large(error):

    if request.path.startswith(
        "/api"
    ):

        return jsonify({

            "success":
                False,

            "message":
                (
                    "The uploaded file is too large. "
                    "Maximum size is 10 MB."
                )

        }), 413


    flash(
        (
            "The uploaded file is too large. "
            "Maximum size is 10 MB."
        ),
        "error"
    )


    return redirect(
        url_for(
            "upload_cv"
        )
    )


@app.errorhandler(500)
def internal_server_error(error):

    if request.path.startswith(
        "/api"
    ):

        return jsonify({

            "success":
                False,

            "message":
                "Internal server error."

        }), 500


    return """

    <!DOCTYPE html>

    <html>

    <head>

        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
        >

        <title>
            System Error
        </title>

        <style>

            body {

                margin: 0;

                min-height: 100vh;

                display: flex;

                align-items: center;

                justify-content: center;

                background: #07111f;

                color: white;

                font-family: Arial, sans-serif;

                text-align: center;

            }


            .error-box {

                width: min(90%, 520px);

                padding: 40px;

                background: #0d1b2d;

                border: 1px solid #20344d;

                border-radius: 18px;

                box-shadow:
                    0 20px 60px
                    rgba(0, 0, 0, .35);

            }


            h1 {

                margin-bottom: 12px;

                color: #38bdf8;

            }


            p {

                color: #b7c6d8;

                line-height: 1.6;

            }


            a {

                display: inline-block;

                margin-top: 20px;

                padding: 12px 22px;

                background: #2563eb;

                color: white;

                text-decoration: none;

                border-radius: 9px;

            }


            a:hover {

                background: #1d4ed8;

            }

        </style>

    </head>


    <body>

        <div class="error-box">

            <h1>
                System Error
            </h1>

            <p>
                The application encountered an unexpected error.
                Please return to the dashboard and try again.
            </p>

            <a href="/dashboard">
                Return to Dashboard
            </a>

        </div>

    </body>

    </html>

    """, 500


# =========================================================
# APPLICATION STARTUP
# =========================================================

if __name__ == "__main__":

    print()

    print(
        "=" * 60
    )

    print(
        "        INTELLIGENT CV SCREENING SYSTEM"
    )

    print(
        "=" * 60
    )

    print(
        f"Application : {APP_NAME}"
    )

    print(
        f"Version     : {APP_VERSION}"
    )

    print(
        f"Organization: {ORGANIZATION_NAME}"
    )

    print(
        "AI Engine   : "
        +
        (
            "READY"
            if SCREENING_ENGINE_AVAILABLE
            else "ERROR"
        )
    )

    print(
        "Database    : CONNECTED"
    )

    print(
        "Server      : http://127.0.0.1:5000"
    )

    print(
        "=" * 60
    )

    print()


    app.run(
        host="127.0.0.1",
        port=5000,
        debug=DEBUG
    )