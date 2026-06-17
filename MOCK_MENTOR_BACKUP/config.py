# config.py - MockMentor Configuration
# All settings for Flask, MySQL, and application behavior

import os

class Config:
    # ── Flask Secret Key (change in production!) ──────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mockmentor_secret_key_2024_change_in_production')

    # ── MySQL Database Configuration ──────────────────────────
    MYSQL_HOST     = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER     = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')  # Set your MySQL password here
    MYSQL_DB       = os.environ.get('MYSQL_DB', 'mockmentor_db')
    MYSQL_PORT     = int(os.environ.get('MYSQL_PORT', 3306))

    # ── Application Settings ───────────────────────────────────
    DEBUG = True
    WEAK_TOPIC_THRESHOLD     = 40.0  # Score below this % = weak topic
    QUESTIONS_PER_INTERVIEW  = 5     # Number of questions per interview
    INTERVIEW_TIME_LIMIT     = 30    # Minutes per interview

    # ── Upload / Resume settings ───────────────────────────────
    UPLOAD_FOLDER     = 'static/uploads'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024   # 5 MB max upload
    ALLOWED_EXTENSIONS = {'pdf', 'txt'}

    # ── Coding module settings ─────────────────────────────────
    CODE_TIME_LIMIT   = 60   # seconds per coding problem (UI timer)

    # ── Skill categories for resume analysis ──────────────────
    SKILL_MAP = {
        'Programming Languages': ['python','java','c++','c','javascript','typescript','go','rust','kotlin','swift','ruby','php','scala'],
        'Web Development':       ['html','css','flask','django','react','angular','vue','nodejs','express','spring','bootstrap','jquery'],
        'Databases':             ['mysql','postgresql','mongodb','sqlite','redis','oracle','sql server','cassandra','dynamodb','firebase'],
        'Cloud & DevOps':        ['aws','azure','gcp','docker','kubernetes','jenkins','terraform','ansible','linux','git','ci/cd'],
        'Data Science & AI':     ['machine learning','deep learning','tensorflow','pytorch','pandas','numpy','scikit','nlp','computer vision','data analysis'],
        'Core CS':               ['data structures','algorithms','operating systems','computer networks','dbms','oops','system design'],
    }

    # Topic recommendations based on detected skills
    SKILL_TOPIC_MAP = {
        'python':           'Python',
        'java':             'Java',
        'javascript':       'Web Development',
        'flask':            'Web Development',
        'django':           'Web Development',
        'react':            'Web Development',
        'mysql':            'SQL',
        'sql':              'SQL',
        'mongodb':          'DBMS',
        'dbms':             'DBMS',
        'data structures':  'Data Structures',
        'algorithms':       'Algorithms',
        'operating systems':'Operating Systems',
        'computer networks':'Computer Networks',
        'system design':    'System Design',
        'machine learning': 'Algorithms',
        'aws':              'System Design',
        'docker':           'System Design',
    }
