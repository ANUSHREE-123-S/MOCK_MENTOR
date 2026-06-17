# routes/admin_routes.py
# Admin panel: dashboard, question CRUD, candidate management

from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash)
from models.db_helper import fetch_one, fetch_dict, execute_query
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated

# ── Admin Dashboard ───────────────────────────────────────────
@admin_bp.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # Summary stats
    total_students   = fetch_one("SELECT COUNT(*) FROM candidates")[0]
    total_questions  = fetch_one("SELECT COUNT(*) FROM questions")[0]
    total_interviews = fetch_one("SELECT COUNT(*) FROM interviews")[0]
    avg_score_all    = fetch_one("SELECT ROUND(AVG(total_score),1) FROM interviews")[0] or 0

    # Top 5 performers
    top_students = fetch_dict("""
        SELECT c.name, c.college, l.average_score, l.total_interviews, l.rank_position
        FROM leaderboard l JOIN candidates c ON l.candidate_id = c.candidate_id
        ORDER BY l.rank_position ASC LIMIT 5
    """)

    # Topic-wise question count
    topic_stats = fetch_dict("""
        SELECT t.topic_name, COUNT(q.question_id) AS q_count
        FROM topics t LEFT JOIN questions q ON t.topic_id = q.topic_id
        GROUP BY t.topic_id, t.topic_name ORDER BY q_count DESC
    """)

    # Recent interviews
    recent_ivs = fetch_dict("""
        SELECT c.name, t.topic_name, i.total_score,
               DATE_FORMAT(i.interview_date,'%%d %%b %%Y') AS date_str
        FROM interviews i
        JOIN candidates c ON i.candidate_id = c.candidate_id
        JOIN topics t ON i.topic_id = t.topic_id
        ORDER BY i.interview_date DESC LIMIT 10
    """)

    return render_template('admin_dashboard.html',
        total_students=total_students,
        total_questions=total_questions,
        total_interviews=total_interviews,
        avg_score_all=avg_score_all,
        top_students=top_students,
        topic_stats=topic_stats,
        recent_ivs=recent_ivs,
        admin_name=session.get('admin_name', 'Admin')
    )

# ── Question List ─────────────────────────────────────────────
@admin_bp.route('/admin/questions')
@admin_required
def manage_questions():
    topic_filter = request.args.get('topic', '')
    diff_filter  = request.args.get('difficulty', '')
    search       = request.args.get('search', '')

    query = """
        SELECT q.question_id, t.topic_name, d.difficulty_name,
               q.question_text, q.sample_answer
        FROM questions q
        JOIN topics t ON q.topic_id = t.topic_id
        JOIN difficulty_levels d ON q.difficulty_id = d.difficulty_id
        WHERE 1=1
    """
    params = []
    if topic_filter:
        query += " AND t.topic_name = %s"; params.append(topic_filter)
    if diff_filter:
        query += " AND d.difficulty_name = %s"; params.append(diff_filter)
    if search:
        query += " AND q.question_text LIKE %s"; params.append(f'%{search}%')

    query += " ORDER BY t.topic_name, d.difficulty_name"
    questions    = fetch_dict(query, tuple(params))
    topics       = fetch_dict("SELECT topic_id, topic_name FROM topics ORDER BY topic_name")
    difficulties = fetch_dict("SELECT difficulty_id, difficulty_name FROM difficulty_levels")

    return render_template('admin_questions.html',
        questions=questions,
        topics=topics,
        difficulties=difficulties,
        topic_filter=topic_filter,
        diff_filter=diff_filter,
        search=search,
        admin_name=session.get('admin_name', 'Admin')
    )

# ── Add Question ──────────────────────────────────────────────
@admin_bp.route('/admin/questions/add', methods=['GET', 'POST'])
@admin_required
def add_question():
    topics       = fetch_dict("SELECT topic_id, topic_name FROM topics ORDER BY topic_name")
    difficulties = fetch_dict("SELECT difficulty_id, difficulty_name FROM difficulty_levels")

    if request.method == 'POST':
        topic_id       = request.form.get('topic_id')
        difficulty_id  = request.form.get('difficulty_id')
        question_text  = request.form.get('question_text', '').strip()
        sample_answer  = request.form.get('sample_answer', '').strip()

        if not all([topic_id, difficulty_id, question_text]):
            flash('Topic, difficulty, and question text are required.', 'danger')
        else:
            execute_query(
                "INSERT INTO questions (topic_id, difficulty_id, question_text, sample_answer) VALUES (%s,%s,%s,%s)",
                (topic_id, difficulty_id, question_text, sample_answer)
            )
            flash('Question added successfully!', 'success')
            return redirect(url_for('admin.manage_questions'))

    return render_template('admin_add_question.html',
        topics=topics, difficulties=difficulties,
        admin_name=session.get('admin_name', 'Admin')
    )

# ── Edit Question ─────────────────────────────────────────────
@admin_bp.route('/admin/questions/edit/<int:qid>', methods=['GET', 'POST'])
@admin_required
def edit_question(qid):
    question     = fetch_dict("SELECT * FROM questions WHERE question_id=%s", (qid,))
    topics       = fetch_dict("SELECT topic_id, topic_name FROM topics ORDER BY topic_name")
    difficulties = fetch_dict("SELECT difficulty_id, difficulty_name FROM difficulty_levels")

    if not question:
        flash('Question not found.', 'danger')
        return redirect(url_for('admin.manage_questions'))

    question = question[0]

    if request.method == 'POST':
        topic_id      = request.form.get('topic_id')
        difficulty_id = request.form.get('difficulty_id')
        question_text = request.form.get('question_text', '').strip()
        sample_answer = request.form.get('sample_answer', '').strip()

        execute_query("""
            UPDATE questions SET topic_id=%s, difficulty_id=%s,
            question_text=%s, sample_answer=%s WHERE question_id=%s
        """, (topic_id, difficulty_id, question_text, sample_answer, qid))
        flash('Question updated!', 'success')
        return redirect(url_for('admin.manage_questions'))

    return render_template('admin_edit_question.html',
        question=question, topics=topics, difficulties=difficulties,
        admin_name=session.get('admin_name', 'Admin')
    )

# ── Delete Question ───────────────────────────────────────────
@admin_bp.route('/admin/questions/delete/<int:qid>', methods=['POST'])
@admin_required
def delete_question(qid):
    execute_query("DELETE FROM questions WHERE question_id=%s", (qid,))
    flash('Question deleted.', 'info')
    return redirect(url_for('admin.manage_questions'))

# ── Candidate Management ──────────────────────────────────────
@admin_bp.route('/admin/candidates')
@admin_required
def manage_candidates():
    search = request.args.get('search', '')
    query  = """
        SELECT c.candidate_id, c.name, c.email, c.college, c.created_at,
               COUNT(i.interview_id) AS total_interviews,
               ROUND(AVG(i.total_score),1) AS avg_score
        FROM candidates c
        LEFT JOIN interviews i ON c.candidate_id = i.candidate_id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND (c.name LIKE %s OR c.email LIKE %s OR c.college LIKE %s)"
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    query += " GROUP BY c.candidate_id ORDER BY c.created_at DESC"
    candidates = fetch_dict(query, tuple(params))

    return render_template('admin_candidates.html',
        candidates=candidates, search=search,
        admin_name=session.get('admin_name', 'Admin')
    )

# ── Delete Candidate ──────────────────────────────────────────
@admin_bp.route('/admin/candidates/delete/<int:cid>', methods=['POST'])
@admin_required
def delete_candidate(cid):
    execute_query("DELETE FROM candidates WHERE candidate_id=%s", (cid,))
    flash('Candidate removed.', 'info')
    return redirect(url_for('admin.manage_candidates'))

# ── Add Topic ─────────────────────────────────────────────────
@admin_bp.route('/admin/topics/add', methods=['POST'])
@admin_required
def add_topic():
    name = request.form.get('topic_name', '').strip()
    if name:
        try:
            execute_query("INSERT INTO topics (topic_name) VALUES (%s)", (name,))
            flash(f'Topic "{name}" added.', 'success')
        except Exception:
            flash('Topic already exists.', 'warning')
    return redirect(url_for('admin.admin_dashboard'))
