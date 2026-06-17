# routes/api_routes.py
# JSON API endpoints used by Chart.js and frontend JS

from flask import Blueprint, jsonify, session
from models.db_helper import fetch_dict, fetch_one
from utils.analytics import get_topic_performance, get_interview_trend

api_bp = Blueprint('api', __name__)

def login_required_json(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'candidate_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# ── Topic performance data for bar/pie chart ──────────────────
@api_bp.route('/topic-performance')
@login_required_json
def topic_performance():
    cid  = session['candidate_id']
    data = get_topic_performance(cid)
    return jsonify({
        'labels': [d['topic_name'] for d in data],
        'scores': [float(d['avg_score']) for d in data],
    })

# ── Interview trend for line chart ────────────────────────────
@api_bp.route('/interview-trend')
@login_required_json
def interview_trend():
    cid  = session['candidate_id']
    data = get_interview_trend(cid)
    return jsonify({
        'labels': [d['date_label'] for d in data],
        'scores': [float(d['total_score']) for d in data],
        'topics': [d['topic_name']   for d in data],
    })

# ── Accuracy data for pie chart ───────────────────────────────
@api_bp.route('/accuracy')
@login_required_json
def accuracy():
    cid  = session['candidate_id']
    data = fetch_dict("""
        SELECT t.topic_name,
               ROUND(AVG(r.score) * 10, 1) AS accuracy_pct
        FROM responses r
        JOIN interviews i ON r.interview_id = i.interview_id
        JOIN questions  q ON r.question_id  = q.question_id
        JOIN topics     t ON q.topic_id     = t.topic_id
        WHERE i.candidate_id = %s
        GROUP BY t.topic_id, t.topic_name
        ORDER BY accuracy_pct DESC
    """, (cid,))
    return jsonify({
        'labels': [d['topic_name'] for d in data],
        'values': [float(d['accuracy_pct']) for d in data],
    })

# ── Admin: overall system stats ───────────────────────────────
@api_bp.route('/admin/stats')
def admin_stats():
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    topic_data = fetch_dict("""
        SELECT t.topic_name, ROUND(AVG(i.total_score),1) AS avg_score
        FROM interviews i JOIN topics t ON i.topic_id = t.topic_id
        GROUP BY t.topic_id, t.topic_name ORDER BY avg_score DESC
    """)
    return jsonify({
        'labels': [d['topic_name'] for d in topic_data],
        'scores': [float(d['avg_score']) for d in topic_data],
    })
