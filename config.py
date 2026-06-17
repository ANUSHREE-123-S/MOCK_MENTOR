# config.py  –  MockMentor Configuration (Development + Production)
# ─────────────────────────────────────────────────────────────────
# python-dotenv loads .env when present (local dev).
# Cloud platforms (Render / Railway / GCP) inject env vars directly.
# Existing routes / db_helper / utils are NOT modified.

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    _env = Path(__file__).parent / '.env'
    if _env.exists():
        load_dotenv(_env)
except ImportError:
    pass


class Config:
    """Shared base configuration."""

    # Secret key ──────────────────────────────────────────────
    SECRET_KEY = os.environ.get(
        'SECRET_KEY',
        'dev-only-insecure-key-replace-in-production'
    )

    # MySQL ───────────────────────────────────────────────────
    MYSQL_HOST     = os.environ.get('MYSQL_HOST',     'localhost')
    MYSQL_USER     = os.environ.get('MYSQL_USER',     'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB       = os.environ.get('MYSQL_DB',       'mockmentor_db')
    MYSQL_PORT     = int(os.environ.get('MYSQL_PORT', 3306))
    # Set MYSQL_SSL=1 for PlanetScale / Aiven / managed DBs
    MYSQL_SSL      = os.environ.get('MYSQL_SSL', '').lower() in ('1','true','yes')

    # Uploads ─────────────────────────────────────────────────
    UPLOAD_FOLDER      = os.environ.get('UPLOAD_FOLDER', 'static/uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024   # 5 MB
    ALLOWED_EXTENSIONS = {'pdf', 'txt'}

    # App tuning (identical to original values) ───────────────
    WEAK_TOPIC_THRESHOLD    = 40.0
    QUESTIONS_PER_INTERVIEW = 5
    INTERVIEW_TIME_LIMIT    = 30
    CODE_TIME_LIMIT         = 60

    # Skill maps (unchanged) ──────────────────────────────────
    SKILL_MAP = {
        'Programming Languages': ['python','java','c++','c','javascript','typescript','go','rust','kotlin','swift','ruby','php','scala'],
        'Web Development':       ['html','css','flask','django','react','angular','vue','nodejs','express','spring','bootstrap','jquery'],
        'Databases':             ['mysql','postgresql','mongodb','sqlite','redis','oracle','sql server','cassandra','dynamodb','firebase'],
        'Cloud & DevOps':        ['aws','azure','gcp','docker','kubernetes','jenkins','terraform','ansible','linux','git','ci/cd'],
        'Data Science & AI':     ['machine learning','deep learning','tensorflow','pytorch','pandas','numpy','scikit','nlp','computer vision','data analysis'],
        'Core CS':               ['data structures','algorithms','operating systems','computer networks','dbms','oops','system design'],
    }
    SKILL_TOPIC_MAP = {
        'python':'Python','java':'Java','javascript':'Web Development',
        'flask':'Web Development','django':'Web Development','react':'Web Development',
        'mysql':'SQL','sql':'SQL','mongodb':'DBMS','dbms':'DBMS',
        'data structures':'Data Structures','algorithms':'Algorithms',
        'operating systems':'Operating Systems','computer networks':'Computer Networks',
        'system design':'System Design','machine learning':'Algorithms',
        'aws':'System Design','docker':'System Design',
    }


class DevelopmentConfig(Config):
    DEBUG   = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG   = False
    TESTING = False

    # Raise clearly if SECRET_KEY is still the insecure default
    @classmethod
    def _validate(cls):
        if cls.SECRET_KEY.startswith('dev-only'):
            raise RuntimeError(
                "Set a real SECRET_KEY environment variable before deploying to production.\n"
                "Generate one:  python -c \"import secrets; print(secrets.token_hex(32))\""
            )

    # Containers have ephemeral filesystems – /tmp is always writable
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/mockmentor_uploads')

    # HTTPS-only cookies
    SESSION_COOKIE_SECURE   = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PREFERRED_URL_SCHEME    = 'https'


class TestingConfig(Config):
    DEBUG   = False
    TESTING = True
    MYSQL_DB = os.environ.get('MYSQL_TEST_DB', 'mockmentor_test')


# Mapping for app factory
config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'testing':     TestingConfig,
    'default':     DevelopmentConfig,
}
