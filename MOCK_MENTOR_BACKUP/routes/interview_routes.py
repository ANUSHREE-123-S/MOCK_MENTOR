# routes/interview_routes.py
# Handles starting an interview, serving questions, and submitting answers

from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, jsonify)
from models.db_helper import fetch_one, fetch_all, fetch_dict, execute_query
from utils.analytics import auto_score_answer, get_weak_topics, save_recommendations
import random
from config import Config

interview_bp = Blueprint('interview', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'candidate_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

# ── Start Interview - Topic & Difficulty Selection ────────────
@interview_bp.route('/interview/start', methods=['GET', 'POST'])
@login_required
def start_interview():
    topics      = fetch_dict("SELECT topic_id, topic_name FROM topics ORDER BY topic_name")
    difficulties= fetch_dict("SELECT difficulty_id, difficulty_name FROM difficulty_levels")

    if request.method == 'POST':
        topic_id      = request.form.get('topic_id')
        difficulty_id = request.form.get('difficulty_id')

        if not topic_id or not difficulty_id:
            flash('Please select topic and difficulty.', 'danger')
            return render_template('start_interview.html', topics=topics, difficulties=difficulties,
                                   candidate_name=session.get('candidate_name', ''))

        # Check if enough questions exist
        count = fetch_one("""
            SELECT COUNT(*) FROM questions
            WHERE topic_id = %s AND difficulty_id = %s
        """, (topic_id, difficulty_id))

        if not count or count[0] < 1:
            flash('No questions available for this selection. Try a different combination.', 'warning')
            return render_template('start_interview.html', topics=topics, difficulties=difficulties,
                                   candidate_name=session.get('candidate_name', ''))

        # Create interview record
        interview_id = execute_query(
            "INSERT INTO interviews (candidate_id, topic_id) VALUES (%s, %s)",
            (session['candidate_id'], topic_id)
        )

        # Store in session
        session['current_interview_id'] = interview_id
        session['current_topic_id']     = int(topic_id)
        session['current_difficulty_id']= int(difficulty_id)
        session['interview_start_time'] = __import__('time').time()

        return redirect(url_for('interview.take_interview', interview_id=interview_id))

    return render_template('start_interview.html',
        topics=topics,
        difficulties=difficulties,
        candidate_name=session.get('candidate_name', '')
    )

# ── Take Interview - Answer Questions ─────────────────────────
@interview_bp.route('/interview/<int:interview_id>', methods=['GET', 'POST'])
@login_required
def take_interview(interview_id):
    cid = session['candidate_id']

    # Verify interview belongs to this candidate
    iv = fetch_one(
        "SELECT interview_id, topic_id FROM interviews WHERE interview_id=%s AND candidate_id=%s",
        (interview_id, cid)
    )
    if not iv:
        flash('Interview not found.', 'danger')
        return redirect(url_for('student.dashboard'))

    topic_id      = session.get('current_topic_id', iv[1])
    difficulty_id = session.get('current_difficulty_id', 1)
    n             = Config.QUESTIONS_PER_INTERVIEW

    # Get questions already answered in this interview
    answered = fetch_all(
        "SELECT question_id FROM responses WHERE interview_id = %s", (interview_id,)
    )
    answered_ids = [r[0] for r in answered]

    # Fetch available questions
    all_qs = fetch_dict("""
        SELECT question_id, question_text, sample_answer
        FROM questions
        WHERE topic_id = %s AND difficulty_id = %s
    """, (topic_id, difficulty_id))

    # Remove already answered
    remaining = [q for q in all_qs if q['question_id'] not in answered_ids]

    if not remaining:
        # All questions answered → finalize
        return redirect(url_for('interview.finish_interview', interview_id=interview_id))

    # Pick random question from remaining
    question = random.choice(remaining)
    q_number = len(answered_ids) + 1
    total_q  = min(n, len(all_qs))

    if request.method == 'POST':
        user_answer = request.form.get('answer', '').strip()
        time_taken  = int(request.form.get('time_taken', 0))
        q_id        = int(request.form.get('question_id'))

        # Fetch the correct sample answer
        q_data = fetch_one(
            "SELECT sample_answer FROM questions WHERE question_id = %s", (q_id,)
        )
        sample = q_data[0] if q_data else ''

        # Auto-score the answer
        score = auto_score_answer(user_answer, sample, max_score=10)

        # Save response
        execute_query(
            "INSERT INTO responses (interview_id, question_id, user_answer, score, time_taken) VALUES (%s,%s,%s,%s,%s)",
            (interview_id, q_id, user_answer, score, time_taken)
        )

        # Check if we've hit the question limit
        total_answered = len(answered_ids) + 1
        if total_answered >= total_q:
            return redirect(url_for('interview.finish_interview', interview_id=interview_id))

        return redirect(url_for('interview.take_interview', interview_id=interview_id))

    return render_template('take_interview.html',
        question=question,
        q_number=q_number,
        total_q=total_q,
        interview_id=interview_id,
        candidate_name=session.get('candidate_name', ''),
        time_limit=Config.INTERVIEW_TIME_LIMIT * 60
    )

# ── Finish Interview - Calculate Score & Save ─────────────────
@interview_bp.route('/interview/<int:interview_id>/finish')
@login_required
def finish_interview(interview_id):
    import time
    cid = session['candidate_id']

    # Calculate total score (sum of response scores, scaled to 100)
    score_data = fetch_one("""
        SELECT SUM(score), COUNT(score)
        FROM responses WHERE interview_id = %s
    """, (interview_id,))

    total_raw = float(score_data[0] or 0)
    count      = int(score_data[1] or 1)
    # Scale: each question is /10, total is out of 100
    total_score = round((total_raw / (count * 10)) * 100, 2) if count > 0 else 0

    # Duration
    start_time = session.pop('interview_start_time', time.time())
    duration   = int(time.time() - start_time)

    # Determine feedback text
    if total_score >= 80:
        feedback = "Excellent performance! You have a strong grasp of the topic."
    elif total_score >= 60:
        feedback = "Good job! A few areas need improvement. Review weak topics."
    elif total_score >= 40:
        feedback = "Average performance. Focus on practice and revision."
    else:
        feedback = "Needs improvement. Study the fundamentals and try again."

    # Update interview record
    execute_query("""
        UPDATE interviews SET total_score=%s, feedback=%s, interview_duration=%s
        WHERE interview_id=%s
    """, (total_score, feedback, duration, interview_id))

    # Save detailed feedback scores
    technical_score     = round(total_score * 0.6, 2)
    communication_score = round(total_score * 0.2, 2)
    confidence_score    = round(total_score * 0.2, 2)

    existing_fb = fetch_one(
        "SELECT feedback_id FROM interview_feedback WHERE interview_id=%s", (interview_id,)
    )
    if not existing_fb:
        execute_query("""
            INSERT INTO interview_feedback (interview_id, technical_score, communication_score, confidence_score, suggestions)
            VALUES (%s,%s,%s,%s,%s)
        """, (interview_id, technical_score, communication_score, confidence_score, feedback))

    # Update weak topics & recommendations
    from utils.analytics import update_leaderboard
    weak = get_weak_topics(cid)
    save_recommendations(cid, weak)
    update_leaderboard()

    # Clear interview session keys
    session.pop('current_interview_id', None)
    session.pop('current_topic_id', None)
    session.pop('current_difficulty_id', None)

    flash(f'Interview completed! Your score: {total_score:.1f}/100', 'success')
    return redirect(url_for('student.report', interview_id=interview_id))

# ── Interview History ─────────────────────────────────────────
@interview_bp.route('/interviews')
@login_required
def interview_history():
    cid = session['candidate_id']

    topic_filter      = request.args.get('topic', '')
    difficulty_filter = request.args.get('difficulty', '')

    query = """
        SELECT i.interview_id, t.topic_name, d.difficulty_name,
               i.total_score,
               DATE_FORMAT(i.interview_date, '%%d %%b %%Y %%H:%%i') AS date_str,
               i.interview_duration, i.feedback
        FROM interviews i
        JOIN topics t ON i.topic_id = t.topic_id
        LEFT JOIN questions q ON q.topic_id = i.topic_id
        LEFT JOIN difficulty_levels d ON q.difficulty_id = d.difficulty_id
        WHERE i.candidate_id = %s
    """
    params = [cid]

    if topic_filter:
        query += " AND t.topic_name = %s"
        params.append(topic_filter)

    query += " GROUP BY i.interview_id ORDER BY i.interview_date DESC"

    interviews = fetch_dict(query, tuple(params))
    topics     = fetch_dict("SELECT topic_name FROM topics ORDER BY topic_name")

    return render_template('interview_history.html',
        interviews=interviews,
        topics=topics,
        selected_topic=topic_filter,
        candidate_name=session.get('candidate_name', '')
    )
