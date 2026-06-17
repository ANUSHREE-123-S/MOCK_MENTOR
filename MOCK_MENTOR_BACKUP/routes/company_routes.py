# routes/company_routes.py
# Company-wise interview preparation: questions, rounds, experiences, analytics

from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, jsonify)
from models.db_helper import fetch_one, fetch_dict, execute_query

company_bp = Blueprint('company', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'candidate_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ── Company List / Selection Page ─────────────────────────────
@company_bp.route('/')
@login_required
def company_list():
    companies = fetch_dict("""
        SELECT c.company_id, c.company_name, c.logo_emoji, c.description,
               c.avg_package, c.difficulty,
               COUNT(DISTINCT cq.cq_id)  AS question_count,
               COUNT(DISTINCT cr.round_id) AS round_count,
               COUNT(DISTINCT ce.exp_id)   AS experience_count
        FROM companies c
        LEFT JOIN company_questions cq ON cq.company_id = c.company_id
        LEFT JOIN company_rounds cr    ON cr.company_id = c.company_id
        LEFT JOIN company_experiences ce ON ce.company_id = c.company_id
        GROUP BY c.company_id
        ORDER BY
            CASE c.difficulty WHEN 'Easy' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END,
            c.company_name
    """)
    return render_template('company/company_list.html',
        companies=companies,
        candidate_name=session.get('candidate_name', '')
    )


# ── Company Detail / Prep Dashboard ──────────────────────────
@company_bp.route('/<int:company_id>')
@login_required
def company_detail(company_id):
    cid = session['candidate_id']

    company = fetch_dict(
        "SELECT * FROM companies WHERE company_id=%s", (company_id,)
    )
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.company_list'))
    company = company[0]

    # Interview rounds
    rounds = fetch_dict(
        "SELECT * FROM company_rounds WHERE company_id=%s ORDER BY round_order",
        (company_id,)
    )

    # Questions (with filters)
    topic_filter = request.args.get('topic', '')
    diff_filter  = request.args.get('difficulty', '')

    q_query = """
        SELECT cq.cq_id, cq.question_text, cq.sample_answer, cq.frequency,
               t.topic_name, d.difficulty_name, cr.round_name
        FROM company_questions cq
        LEFT JOIN topics t            ON cq.topic_id      = t.topic_id
        LEFT JOIN difficulty_levels d ON cq.difficulty_id = d.difficulty_id
        LEFT JOIN company_rounds cr   ON cq.round_id      = cr.round_id
        WHERE cq.company_id = %s
    """
    q_params = [company_id]
    if topic_filter:
        q_query += " AND t.topic_name = %s"; q_params.append(topic_filter)
    if diff_filter:
        q_query += " AND d.difficulty_name = %s"; q_params.append(diff_filter)
    q_query += " ORDER BY cq.frequency DESC, d.difficulty_id ASC"

    questions = fetch_dict(q_query, tuple(q_params))
    topics    = fetch_dict("SELECT DISTINCT topic_name FROM topics ORDER BY topic_name")
    diffs     = fetch_dict("SELECT difficulty_name FROM difficulty_levels")

    # Interview experiences
    experiences = fetch_dict("""
        SELECT ce.exp_id, ce.title, ce.experience, ce.result, ce.difficulty,
               DATE_FORMAT(ce.created_at,'%%d %%b %%Y') AS posted_on,
               c.name AS author
        FROM company_experiences ce
        JOIN candidates c ON ce.candidate_id = c.candidate_id
        WHERE ce.company_id = %s
        ORDER BY ce.created_at DESC LIMIT 5
    """, (company_id,))

    # Topic strength for this company's questions
    topic_strength = fetch_dict("""
        SELECT t.topic_name, COUNT(cq.cq_id) AS q_count,
               ROUND(AVG(CASE d.difficulty_name
                   WHEN 'Easy' THEN 30 WHEN 'Medium' THEN 60 ELSE 90 END), 0) AS avg_difficulty
        FROM company_questions cq
        JOIN topics t ON cq.topic_id = t.topic_id
        JOIN difficulty_levels d ON cq.difficulty_id = d.difficulty_id
        WHERE cq.company_id = %s
        GROUP BY t.topic_id, t.topic_name ORDER BY q_count DESC
    """, (company_id,))

    return render_template('company/company_detail.html',
        company=company,
        rounds=rounds,
        questions=questions,
        topics=topics,
        diffs=diffs,
        experiences=experiences,
        topic_strength=topic_strength,
        topic_filter=topic_filter,
        diff_filter=diff_filter,
        candidate_name=session.get('candidate_name', '')
    )


# ── Submit Interview Experience ───────────────────────────────
@company_bp.route('/<int:company_id>/experience/add', methods=['GET', 'POST'])
@login_required
def add_experience(company_id):
    cid = session['candidate_id']

    company = fetch_dict("SELECT * FROM companies WHERE company_id=%s", (company_id,))
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.company_list'))
    company = company[0]

    if request.method == 'POST':
        title      = request.form.get('title', '').strip()
        experience = request.form.get('experience', '').strip()
        result     = request.form.get('result', 'Pending')
        difficulty = request.form.get('difficulty', 'Medium')

        if not title or not experience:
            flash('Title and experience are required.', 'danger')
        elif len(experience) < 50:
            flash('Please write at least 50 characters describing your experience.', 'warning')
        else:
            execute_query("""
                INSERT INTO company_experiences
                    (company_id, candidate_id, title, experience, result, difficulty)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (company_id, cid, title, experience, result, difficulty))
            flash('Experience shared! Thank you for helping the community.', 'success')
            return redirect(url_for('company.company_detail', company_id=company_id))

    return render_template('company/add_experience.html',
        company=company,
        candidate_name=session.get('candidate_name', '')
    )


# ── All Experiences for a Company ────────────────────────────
@company_bp.route('/<int:company_id>/experiences')
@login_required
def all_experiences(company_id):
    company = fetch_dict("SELECT * FROM companies WHERE company_id=%s", (company_id,))
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.company_list'))
    company = company[0]

    result_filter = request.args.get('result', '')
    query = """
        SELECT ce.exp_id, ce.title, ce.experience, ce.result, ce.difficulty,
               DATE_FORMAT(ce.created_at,'%%d %%b %%Y') AS posted_on,
               c.name AS author
        FROM company_experiences ce
        JOIN candidates c ON ce.candidate_id = c.candidate_id
        WHERE ce.company_id = %s
    """
    params = [company_id]
    if result_filter:
        query += " AND ce.result = %s"; params.append(result_filter)
    query += " ORDER BY ce.created_at DESC"

    experiences = fetch_dict(query, tuple(params))

    return render_template('company/all_experiences.html',
        company=company,
        experiences=experiences,
        result_filter=result_filter,
        candidate_name=session.get('candidate_name', '')
    )


# ── Company Analytics Dashboard ───────────────────────────────
@company_bp.route('/analytics')
@login_required
def company_analytics():
    # Overall company question counts
    company_stats = fetch_dict("""
        SELECT c.company_name, c.logo_emoji, c.difficulty, c.avg_package,
               COUNT(DISTINCT cq.cq_id) AS q_count,
               COUNT(DISTINCT ce.exp_id) AS exp_count
        FROM companies c
        LEFT JOIN company_questions cq ON cq.company_id = c.company_id
        LEFT JOIN company_experiences ce ON ce.company_id = c.company_id
        GROUP BY c.company_id ORDER BY q_count DESC
    """)

    # Most asked topics across all companies
    top_topics = fetch_dict("""
        SELECT t.topic_name, COUNT(cq.cq_id) AS freq
        FROM company_questions cq
        JOIN topics t ON cq.topic_id = t.topic_id
        GROUP BY t.topic_id, t.topic_name
        ORDER BY freq DESC LIMIT 8
    """)

    # Most asked across FAANG specifically
    faang = ['Amazon', 'Google', 'Microsoft']
    faang_topics = fetch_dict("""
        SELECT t.topic_name, COUNT(cq.cq_id) AS freq
        FROM company_questions cq
        JOIN topics t ON cq.topic_id = t.topic_id
        JOIN companies co ON cq.company_id = co.company_id
        WHERE co.company_name IN ('Amazon','Google','Microsoft')
        GROUP BY t.topic_id, t.topic_name
        ORDER BY freq DESC LIMIT 6
    """)

    return render_template('company/company_analytics.html',
        company_stats=company_stats,
        top_topics=top_topics,
        faang_topics=faang_topics,
        candidate_name=session.get('candidate_name', '')
    )
