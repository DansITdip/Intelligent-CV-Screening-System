-- ============================================================
-- INTELLIGENT CV SCREENING AND JOB MATCHING SYSTEM
-- DATABASE SCHEMA
-- ============================================================

CREATE DATABASE IF NOT EXISTS cv_screening_system
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE cv_screening_system;


-- ============================================================
-- 1. USERS
-- Stores system administrators and recruiters
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('Admin', 'Recruiter') NOT NULL DEFAULT 'Recruiter',
    status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);


-- ============================================================
-- 2. JOB PROFILES
-- Stores jobs being advertised/screened against
-- ============================================================

CREATE TABLE IF NOT EXISTS job_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_title VARCHAR(150) NOT NULL,
    department VARCHAR(100),
    employment_type VARCHAR(50),
    experience_required VARCHAR(100),
    job_description TEXT,
    minimum_education VARCHAR(150),
    location VARCHAR(150),
    status ENUM('Active', 'Inactive', 'Closed')
        NOT NULL DEFAULT 'Active',
    created_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_job_created_by
        FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE SET NULL
);


-- ============================================================
-- 3. JOB REQUIREMENTS
-- Individual requirements attached to each job
-- ============================================================

CREATE TABLE IF NOT EXISTS job_requirements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,

    requirement_type ENUM(
        'Skill',
        'Education',
        'Experience',
        'Certification',
        'Other'
    ) NOT NULL DEFAULT 'Skill',

    requirement_name VARCHAR(150) NOT NULL,

    importance ENUM(
        'Required',
        'Preferred'
    ) NOT NULL DEFAULT 'Required',

    weight DECIMAL(5,2) DEFAULT 0,

    CONSTRAINT fk_requirement_job
        FOREIGN KEY (job_id)
        REFERENCES job_profiles(id)
        ON DELETE CASCADE,

    INDEX idx_requirement_job (job_id)
);


-- ============================================================
-- 4. CANDIDATES
-- Stores candidate information
-- ============================================================

CREATE TABLE IF NOT EXISTS candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,

    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(150),
    phone VARCHAR(30),

    target_position VARCHAR(150),
    education VARCHAR(200),

    years_experience DECIMAL(4,1) DEFAULT 0,

    status ENUM(
        'New',
        'Screened',
        'Shortlisted',
        'Review',
        'Rejected'
    ) NOT NULL DEFAULT 'New',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_candidate_name (full_name),
    INDEX idx_candidate_status (status)
);


-- ============================================================
-- 5. CV DOCUMENTS
-- Stores uploaded CV information and extracted text
-- ============================================================

CREATE TABLE IF NOT EXISTS cv_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,

    candidate_id INT NOT NULL,

    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,

    file_type VARCHAR(20) NOT NULL,
    file_size INT,

    extracted_text LONGTEXT,

    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_cv_candidate
        FOREIGN KEY (candidate_id)
        REFERENCES candidates(id)
        ON DELETE CASCADE,

    INDEX idx_cv_candidate (candidate_id)
);


-- ============================================================
-- 6. CANDIDATE SKILLS
-- Skills automatically extracted from CVs
-- ============================================================

CREATE TABLE IF NOT EXISTS candidate_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,

    candidate_id INT NOT NULL,

    skill_name VARCHAR(100) NOT NULL,
    skill_category VARCHAR(100),
    proficiency VARCHAR(50),

    source VARCHAR(50) DEFAULT 'AI Extraction',

    CONSTRAINT fk_skill_candidate
        FOREIGN KEY (candidate_id)
        REFERENCES candidates(id)
        ON DELETE CASCADE,

    UNIQUE KEY unique_candidate_skill (
        candidate_id,
        skill_name
    ),

    INDEX idx_skill_name (skill_name)
);


-- ============================================================
-- 7. SCREENING RESULTS
-- Main AI screening results
-- ============================================================

CREATE TABLE IF NOT EXISTS screening_results (
    id INT AUTO_INCREMENT PRIMARY KEY,

    candidate_id INT NOT NULL,
    job_id INT NOT NULL,

    technical_skills_score DECIMAL(5,2) DEFAULT 0,
    experience_score DECIMAL(5,2) DEFAULT 0,
    education_score DECIMAL(5,2) DEFAULT 0,
    relevance_score DECIMAL(5,2) DEFAULT 0,

    overall_score DECIMAL(5,2) DEFAULT 0,

    recommendation ENUM(
        'Shortlisted',
        'Review',
        'Rejected',
        'Pending'
    ) NOT NULL DEFAULT 'Pending',

    processing_time DECIMAL(8,3),

    screened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_screening_candidate
        FOREIGN KEY (candidate_id)
        REFERENCES candidates(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_screening_job
        FOREIGN KEY (job_id)
        REFERENCES job_profiles(id)
        ON DELETE CASCADE,

    INDEX idx_screening_candidate (candidate_id),
    INDEX idx_screening_job (job_id),
    INDEX idx_screening_score (overall_score)
);


-- ============================================================
-- 8. MATCH RESULTS
-- Detailed comparison between candidate and job requirements
-- ============================================================

CREATE TABLE IF NOT EXISTS match_results (
    id INT AUTO_INCREMENT PRIMARY KEY,

    screening_id INT NOT NULL,
    requirement_id INT NULL,

    candidate_value VARCHAR(255),

    match_status ENUM(
        'Matched',
        'Partial',
        'Missing'
    ) NOT NULL,

    match_score DECIMAL(5,2) DEFAULT 0,

    explanation TEXT,

    CONSTRAINT fk_match_screening
        FOREIGN KEY (screening_id)
        REFERENCES screening_results(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_match_requirement
        FOREIGN KEY (requirement_id)
        REFERENCES job_requirements(id)
        ON DELETE SET NULL,

    INDEX idx_match_screening (screening_id)
);


-- ============================================================
-- 9. REPORTS
-- Stores generated AI screening reports
-- ============================================================

CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,

    report_reference VARCHAR(50) NOT NULL UNIQUE,

    screening_id INT NOT NULL,

    report_title VARCHAR(200) NOT NULL,

    report_content LONGTEXT,

    generated_by INT NULL,

    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_report_screening
        FOREIGN KEY (screening_id)
        REFERENCES screening_results(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_report_user
        FOREIGN KEY (generated_by)
        REFERENCES users(id)
        ON DELETE SET NULL,

    INDEX idx_report_screening (screening_id)
);


-- ============================================================
-- 10. SYSTEM SETTINGS
-- Stores configurable application settings
-- ============================================================

CREATE TABLE IF NOT EXISTS system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,

    setting_name VARCHAR(100) NOT NULL UNIQUE,

    setting_value VARCHAR(255),

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);


-- ============================================================
-- 11. AUDIT LOGS
-- Records important actions performed in the system
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NULL,

    action VARCHAR(150) NOT NULL,

    description TEXT,

    ip_address VARCHAR(45),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_audit_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL,

    INDEX idx_audit_user (user_id),
    INDEX idx_audit_date (created_at)
);


-- ============================================================
-- DEFAULT SYSTEM SETTINGS
-- ============================================================

INSERT INTO system_settings
    (setting_name, setting_value)
VALUES
    ('technical_skills_weight', '40'),
    ('work_experience_weight', '25'),
    ('education_weight', '15'),
    ('job_relevance_weight', '20'),
    ('auto_skill_extraction', '1'),
    ('auto_candidate_scoring', '1'),
    ('ai_recommendation', '1'),
    ('max_cv_upload_size_mb', '10')
ON DUPLICATE KEY UPDATE
    setting_value = VALUES(setting_value);


-- ============================================================
-- DATABASE READY
-- ============================================================