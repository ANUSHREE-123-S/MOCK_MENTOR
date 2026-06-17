# routes/student_routes.py  – UPGRADED
from flask import Blueprint, render_template, redirect, url_for, session, flash, request, send_file
from models.db_helper import fetch_one, fetch_all, fetch_dict, execute_query
from utils.analytics import (get_topic_performance, get_weak_topics,
                               get_interview_trend, update_leaderboard, save_recommendations)
from utils.pdf_generator import generate_interview_pdf
from utils.recommendation_engine import generate_full_recommendations, save_recommendations_v2
import io

student_bp = Blueprint('student', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'candidate_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@student_bp.route('/dashboard')
@login_required
def dashboard():
    cid = session['candidate_id']
    stats = fetch_one("""
        SELECT COUNT(interview_id),ROUND(AVG(total_score),1),MAX(total_score)
        FROM interviews WHERE candidate_id=%s
    """, (cid,))
    total_interviews = stats[0] if stats else 0
    avg_score        = stats[1] if stats and stats[1] else 0
    best_score       = stats[2] if stats and stats[2] else 0

    coding = fetch_one("""
        SELECT COUNT(DISTINCT cq_id),
               SUM(CASE WHEN status='Accepted' THEN 1 ELSE 0 END),
               ROUND(AVG(score),1)
        FROM coding_submissions WHERE candidate_id=%s
    """, (cid,))
    coding_stats = {'attempted': (coding[0] or 0), 'solved': (coding[1] or 0),
                    'avg_score': (coding[2] or 0)} if coding else {'attempted':0,'solved':0,'avg_score':0}

    resume_row      = fetch_one("SELECT resume_id FROM resumes WHERE candidate_id=%s", (cid,))
    resume_uploaded = bool(resume_row)
    resume_analysis = None
    if resume_row:
        ra = fetch_one("SELECT match_score, recommended_topics FROM resume_analysis WHERE resume_id=%s",
                       (resume_row[0],))
        if ra:
            resume_analysis = {'match_score': ra[0], 'topics': ra[1]}

    rank_row      = fetch_one("SELECT rank_position FROM leaderboard WHERE candidate_id=%s", (cid,))
    rank_position = rank_row[0] if rank_row else 'N/A'

    recent_interviews = fetch_dict("""
        SELECT i.interview_id, t.topic_name, i.total_score,
               DATE_FORMAT(i.interview_date,'%%d %%b %%Y') AS date_str, i.interview_duration
        FROM interviews i JOIN topics t ON i.topic_id=t.topic_id
        WHERE i.candidate_id=%s ORDER BY i.interview_date DESC LIMIT 5
    """, (cid,))

    weak_topics      = get_weak_topics(cid)
    recommendations  = generate_full_recommendations(cid)
    save_recommendations_v2(cid, recommendations)

    timeline = fetch_dict("""
        (SELECT 'interview' AS type, t.topic_name AS label, i.total_score AS score,
                DATE_FORMAT(i.interview_date,'%%d %%b') AS date_str
         FROM interviews i JOIN topics t ON i.topic_id=t.topic_id
         WHERE i.candidate_id=%s)
        UNION ALL
        (SELECT 'coding', cq.title, cs.score,
                DATE_FORMAT(cs.submitted_at,'%%d %%b')
         FROM coding_submissions cs JOIN coding_questions cq ON cs.cq_id=cq.cq_id
         WHERE cs.candidate_id=%s AND cs.status='Accepted')
        ORDER BY date_str DESC LIMIT 6
    """, (cid, cid))

    company_readiness = fetch_dict("""
        SELECT co.company_name, co.logo_emoji, co.difficulty,
               ROUND(IFNULL(AVG(i.total_score),0),0) AS readiness
        FROM companies co
        LEFT JOIN company_questions cq ON cq.company_id=co.company_id
        LEFT JOIN topics t ON cq.topic_id=t.topic_id
        LEFT JOIN interviews i ON i.topic_id=t.topic_id AND i.candidate_id=%s
        GROUP BY co.company_id ORDER BY readiness DESC LIMIT 4
    """, (cid,))

    update_leaderboard()
    return render_template('dashboard.html',
        total_interviews=total_interviews, avg_score=avg_score, best_score=best_score,
        rank_position=rank_position, recent_interviews=recent_interviews,
        weak_topics=weak_topics, recommendations=recommendations,
        coding_stats=coding_stats, resume_uploaded=resume_uploaded,
        resume_analysis=resume_analysis, timeline=timeline,
        company_readiness=company_readiness,
        candidate_name=session.get('candidate_name',''))

@student_bp.route('/analytics')
@login_required
def analytics():
    cid = session['candidate_id']
    topic_performance = get_topic_performance(cid)
    weak_topics       = get_weak_topics(cid)
    interview_trend   = get_interview_trend(cid)
    accuracy_data = fetch_dict("""
        SELECT t.topic_name, ROUND(AVG(r.score)*10,1) AS accuracy_pct
        FROM responses r
        JOIN interviews i ON r.interview_id=i.interview_id
        JOIN questions  q ON r.question_id=q.question_id
        JOIN topics     t ON q.topic_id=t.topic_id
        WHERE i.candidate_id=%s GROUP BY t.topic_id,t.topic_name ORDER BY accuracy_pct DESC
    """, (cid,))
    save_recommendations(cid, weak_topics)
    return render_template('analytics.html',
        topic_performance=topic_performance, weak_topics=weak_topics,
        interview_trend=interview_trend, accuracy_data=accuracy_data,
        candidate_name=session.get('candidate_name',''))

@student_bp.route('/leaderboard')
@login_required
def leaderboard():
    update_leaderboard()
    leaders = fetch_dict("""
        SELECT l.rank_position, c.name, c.college, l.average_score,
               l.total_interviews, l.candidate_id
        FROM leaderboard l JOIN candidates c ON l.candidate_id=c.candidate_id
        ORDER BY l.rank_position ASC LIMIT 50
    """)
    my_rank = fetch_one("SELECT rank_position FROM leaderboard WHERE candidate_id=%s",
                        (session['candidate_id'],))
    return render_template('leaderboard.html',
        leaders=leaders, my_rank=my_rank[0] if my_rank else 'N/A',
        current_candidate_id=session['candidate_id'],
        candidate_name=session.get('candidate_name',''))

@student_bp.route('/report/<int:interview_id>')
@login_required
def report(interview_id):
    cid = session['candidate_id']
    interview = fetch_dict("""
        SELECT i.interview_id, i.total_score, i.interview_date,
               i.feedback, i.interview_duration, t.topic_name
        FROM interviews i JOIN topics t ON i.topic_id=t.topic_id
        WHERE i.interview_id=%s AND i.candidate_id=%s
    """, (interview_id, cid))
    if not interview:
        flash('Report not found.', 'danger')
        return redirect(url_for('student.dashboard'))
    interview = interview[0]
    responses = fetch_dict("""
        SELECT r.score, r.user_answer, r.time_taken, q.question_text, q.sample_answer
        FROM responses r JOIN questions q ON r.question_id=q.question_id
        WHERE r.interview_id=%s
    """, (interview_id,))
    fb = fetch_dict("SELECT technical_score,communication_score,confidence_score,suggestions FROM interview_feedback WHERE interview_id=%s", (interview_id,))
    feedback_detail = fb[0] if fb else None
    candidate = fetch_dict("SELECT name,email,college FROM candidates WHERE candidate_id=%s", (cid,))
    candidate = candidate[0] if candidate else {}
    return render_template('report.html',
        interview=interview, responses=responses, feedback_detail=feedback_detail,
        candidate=candidate, candidate_name=session.get('candidate_name',''))

@student_bp.route('/report/<int:interview_id>/pdf')
@login_required
def download_pdf(interview_id):
    cid = session['candidate_id']
    interview_rows = fetch_dict("""
        SELECT i.interview_id, i.total_score, i.interview_date,
               i.feedback, i.interview_duration, t.topic_name
        FROM interviews i JOIN topics t ON i.topic_id=t.topic_id
        WHERE i.interview_id=%s AND i.candidate_id=%s
    """, (interview_id, cid))
    if not interview_rows:
        flash('Report not found.', 'danger')
        return redirect(url_for('student.dashboard'))
    interview = interview_rows[0]
    responses = fetch_dict("""
        SELECT r.score, r.user_answer, r.time_taken, q.question_text, q.sample_answer
        FROM responses r JOIN questions q ON r.question_id=q.question_id WHERE r.interview_id=%s
    """, (interview_id,))
    candidate = fetch_dict("SELECT name,email,college FROM candidates WHERE candidate_id=%s", (cid,))
    candidate = candidate[0] if candidate else {}
    pdf_bytes = generate_interview_pdf(interview, responses, candidate)
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name=f'MockMentor_Report_{interview_id}.pdf')

@student_bp.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    cid = session['candidate_id']
    candidate = fetch_dict("SELECT name,email,college,skills,created_at FROM candidates WHERE candidate_id=%s", (cid,))
    candidate = candidate[0] if candidate else {}
    if request.method == 'POST':
        execute_query("UPDATE candidates SET college=%s,skills=%s WHERE candidate_id=%s",
                      (request.form.get('college','').strip(), request.form.get('skills','').strip(), cid))
        flash('Profile updated!', 'success')
        return redirect(url_for('student.profile'))
    return render_template('profile.html', candidate=candidate, candidate_name=session.get('candidate_name',''))
