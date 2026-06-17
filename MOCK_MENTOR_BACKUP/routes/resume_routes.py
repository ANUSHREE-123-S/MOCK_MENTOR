# routes/resume_routes.py
# Resume upload, text extraction, skill detection, and recommendations

import os
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, current_app)
from models.db_helper import fetch_one, fetch_dict, execute_query
from utils.resume_analyzer import analyse_resume
from werkzeug.utils import secure_filename

resume_bp = Blueprint('resume', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'candidate_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def allowed_file(filename):
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'txt'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


# ── Resume Dashboard ──────────────────────────────────────────
@resume_bp.route('/')
@login_required
def resume_home():
    cid = session['candidate_id']

    resume = fetch_dict(
        "SELECT * FROM resumes WHERE candidate_id=%s", (cid,)
    )
    resume = resume[0] if resume else None

    analysis = None
    skills   = []
    if resume:
        analysis = fetch_dict(
            "SELECT * FROM resume_analysis WHERE resume_id=%s", (resume['resume_id'],)
        )
        analysis = analysis[0] if analysis else None

        skills = fetch_dict(
            "SELECT skill_name, category FROM extracted_skills WHERE resume_id=%s ORDER BY category",
            (resume['resume_id'],)
        )

    return render_template('resume/resume_home.html',
        resume=resume,
        analysis=analysis,
        skills=skills,
        candidate_name=session.get('candidate_name', '')
    )


# ── Upload Resume ─────────────────────────────────────────────
@resume_bp.route('/upload', methods=['POST'])
@login_required
def upload_resume():
    cid = session['candidate_id']

    if 'resume' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('resume.resume_home'))

    file = request.files['resume']

    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('resume.resume_home'))

    if not allowed_file(file.filename):
        flash('Only PDF and TXT files are supported.', 'warning')
        return redirect(url_for('resume.resume_home'))

    # Save file
    upload_dir = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
    os.makedirs(upload_dir, exist_ok=True)
    filename   = secure_filename(f"resume_{cid}_{file.filename}")
    filepath   = os.path.join(upload_dir, filename)
    file.save(filepath)

    ext = filename.rsplit('.', 1)[1].lower()

    # Run analysis
    result = analyse_resume(filepath, ext)

    # Save or update resume record
    existing = fetch_one("SELECT resume_id FROM resumes WHERE candidate_id=%s", (cid,))
    if existing:
        resume_id = existing[0]
        execute_query(
            "UPDATE resumes SET filename=%s, raw_text=%s, uploaded_at=NOW() WHERE resume_id=%s",
            (filename, result['raw_text'], resume_id)
        )
        # Clear old skills and analysis
        execute_query("DELETE FROM extracted_skills WHERE resume_id=%s", (resume_id,))
        execute_query("DELETE FROM resume_analysis WHERE resume_id=%s", (resume_id,))
    else:
        resume_id = execute_query(
            "INSERT INTO resumes (candidate_id, filename, raw_text) VALUES (%s,%s,%s)",
            (cid, filename, result['raw_text'])
        )

    # Save extracted skills
    for skill in result['skills']:
        execute_query(
            "INSERT INTO extracted_skills (resume_id, skill_name, category) VALUES (%s,%s,%s)",
            (resume_id, skill['skill_name'], skill['category'])
        )

    # Save analysis
    topics_str    = ','.join(result['topics'])
    companies_str = ','.join(result['companies'])
    execute_query("""
        INSERT INTO resume_analysis
            (resume_id, match_score, recommended_topics, recommended_companies, analysis_text)
        VALUES (%s,%s,%s,%s,%s)
    """, (resume_id, result['match_score'], topics_str, companies_str, result['analysis']))

    flash(f'Resume analysed! Detected {len(result["skills"])} skills.', 'success')
    return redirect(url_for('resume.resume_home'))


# ── Delete Resume ─────────────────────────────────────────────
@resume_bp.route('/delete', methods=['POST'])
@login_required
def delete_resume():
    cid = session['candidate_id']
    resume = fetch_one("SELECT resume_id, filename FROM resumes WHERE candidate_id=%s", (cid,))
    if resume:
        # Delete file from disk
        upload_dir = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
        filepath   = os.path.join(upload_dir, resume[1] or '')
        if os.path.exists(filepath):
            os.remove(filepath)
        execute_query("DELETE FROM resumes WHERE resume_id=%s", (resume[0],))
        flash('Resume deleted.', 'info')
    return redirect(url_for('resume.resume_home'))
