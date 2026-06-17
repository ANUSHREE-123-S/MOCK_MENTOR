# utils/analytics.py
# Functions for computing analytics, weak topics, leaderboard updates

from models.db_helper import fetch_all, fetch_one, fetch_dict, execute_query
from config import Config

# ── Get topic-wise performance for a candidate ────────────────
def get_topic_performance(candidate_id):
    query = """
        SELECT t.topic_name,
               ROUND(AVG(i.total_score), 2) AS avg_score,
               COUNT(i.interview_id) AS total_interviews
        FROM interviews i
        JOIN topics t ON i.topic_id = t.topic_id
        WHERE i.candidate_id = %s
        GROUP BY t.topic_id, t.topic_name
        ORDER BY avg_score DESC
    """
    return fetch_dict(query, (candidate_id,))

# ── Detect weak topics (below threshold) ─────────────────────
def get_weak_topics(candidate_id):
    threshold = Config.WEAK_TOPIC_THRESHOLD
    query = """
        SELECT t.topic_name,
               ROUND(AVG(i.total_score), 2) AS avg_score
        FROM interviews i
        JOIN topics t ON i.topic_id = t.topic_id
        WHERE i.candidate_id = %s
        GROUP BY t.topic_id, t.topic_name
        HAVING avg_score < %s
        ORDER BY avg_score ASC
    """
    return fetch_dict(query, (candidate_id, threshold))

# ── Get interview history (last 10) for line chart ────────────
def get_interview_trend(candidate_id):
    query = """
        SELECT DATE_FORMAT(i.interview_date, '%%d %%b') AS date_label,
               i.total_score,
               t.topic_name
        FROM interviews i
        JOIN topics t ON i.topic_id = t.topic_id
        WHERE i.candidate_id = %s
        ORDER BY i.interview_date DESC
        LIMIT 10
    """
    rows = fetch_dict(query, (candidate_id,))
    # Reverse so chart is chronological
    return list(reversed(rows))

# ── Compute and update leaderboard for ALL candidates ─────────
def update_leaderboard():
    query = """
        SELECT c.candidate_id,
               ROUND(AVG(i.total_score), 2) AS avg_score,
               COUNT(i.interview_id) AS total_interviews
        FROM candidates c
        LEFT JOIN interviews i ON c.candidate_id = i.candidate_id
        GROUP BY c.candidate_id
        ORDER BY avg_score DESC
    """
    rows = fetch_dict(query)

    for rank, row in enumerate(rows, start=1):
        cid   = row['candidate_id']
        avg   = row['avg_score'] or 0
        total = row['total_interviews'] or 0

        # UPSERT into leaderboard
        existing = fetch_one(
            "SELECT leaderboard_id FROM leaderboard WHERE candidate_id = %s", (cid,)
        )
        if existing:
            execute_query(
                "UPDATE leaderboard SET average_score=%s, rank_position=%s, total_interviews=%s WHERE candidate_id=%s",
                (avg, rank, total, cid)
            )
        else:
            execute_query(
                "INSERT INTO leaderboard (candidate_id, average_score, rank_position, total_interviews) VALUES (%s,%s,%s,%s)",
                (cid, avg, rank, total)
            )

# ── Auto-score an answer (keyword matching) ───────────────────
def auto_score_answer(user_answer, sample_answer, max_score=10):
    """Simple keyword-based scoring system."""
    if not user_answer or not user_answer.strip():
        return 0.0

    user_words   = set(user_answer.lower().split())
    sample_words = set(sample_answer.lower().split())

    # Remove common stop words
    stop_words = {'a','an','the','is','are','was','were','be','been',
                  'have','has','had','do','does','did','will','would',
                  'could','should','may','might','shall','can','to','of',
                  'in','on','at','by','for','with','and','or','but'}
    sample_keywords = sample_words - stop_words
    user_keywords   = user_words - stop_words

    if not sample_keywords:
        return round(max_score * 0.5, 2)  # neutral if no reference

    match_ratio = len(user_keywords & sample_keywords) / len(sample_keywords)
    score = round(min(match_ratio * max_score, max_score), 2)
    return score

# ── Generate recommendations for weak topics ──────────────────
RECOMMENDATIONS = {
    'DBMS':              'Practice SQL joins, normalization (1NF/2NF/3NF), and ACID properties.',
    'Data Structures':   'Revise arrays, linked lists, trees, and graphs with LeetCode problems.',
    'Algorithms':        'Practice sorting, searching, greedy, and dynamic programming problems.',
    'Operating Systems': 'Review process scheduling, memory management, deadlocks, and paging.',
    'Computer Networks': 'Study OSI model, TCP/IP, DNS, HTTP, and network security basics.',
    'Python':            'Practice OOP concepts, decorators, list comprehensions, and libraries.',
    'Java':              'Focus on Collections, multithreading, OOP principles, and JVM internals.',
    'Web Development':   'Practice HTML, CSS, JavaScript, REST APIs, and frameworks.',
    'System Design':     'Study scalability, load balancing, caching, databases, and microservices.',
    'SQL':               'Practice complex queries, joins, subqueries, indexes, and stored procedures.',
}

def save_recommendations(candidate_id, weak_topics):
    # Delete old recommendations for this candidate
    execute_query("DELETE FROM recommendations WHERE candidate_id = %s", (candidate_id,))

    for wt in weak_topics:
        topic_name = wt['topic_name']
        topic_row  = fetch_one("SELECT topic_id FROM topics WHERE topic_name = %s", (topic_name,))
        if not topic_row:
            continue
        topic_id = topic_row[0]
        text     = RECOMMENDATIONS.get(topic_name, f'Practice more questions on {topic_name}.')
        execute_query(
            "INSERT INTO recommendations (candidate_id, topic_id, recommendation_text) VALUES (%s,%s,%s)",
            (candidate_id, topic_id, text)
        )
