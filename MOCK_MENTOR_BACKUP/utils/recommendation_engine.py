# utils/recommendation_engine.py
# AI-style intelligent recommendation engine.
# Analyses interview scores, coding performance, and resume skills
# to generate personalised study recommendations.

from models.db_helper import fetch_dict, fetch_one, execute_query

# ─────────────────────────────────────────────────────────────
# Recommendation templates keyed by topic / area
# ─────────────────────────────────────────────────────────────
TOPIC_TIPS = {
    'DBMS': {
        'tip': 'Practice SQL joins (INNER, LEFT, RIGHT), normalization (1NF-3NF), ACID properties, and indexing.',
        'resources': ['LeetCode SQL problems', 'Mode Analytics SQL Tutorial', 'W3Schools SQL'],
        'priority': 1,
    },
    'Data Structures': {
        'tip': 'Revise arrays, linked lists, stacks, queues, trees, graphs and hash maps. Solve 2 LeetCode problems daily.',
        'resources': ['NeetCode 150', 'Striver SDE Sheet', 'GeeksForGeeks DSA'],
        'priority': 1,
    },
    'Algorithms': {
        'tip': 'Focus on sorting (merge/quick/heap), searching, dynamic programming, greedy, and graph algorithms.',
        'resources': ['CLRS Book', 'Abdul Bari Algorithms (YouTube)', 'LeetCode Top 100'],
        'priority': 1,
    },
    'Operating Systems': {
        'tip': 'Review process scheduling (FCFS, SJF, Round Robin), memory management, deadlocks, semaphores, and file systems.',
        'resources': ['Galvin OS Book', 'Gate Smashers OS (YouTube)', 'GeeksForGeeks OS'],
        'priority': 2,
    },
    'Computer Networks': {
        'tip': 'Study OSI model, TCP/IP stack, DNS, HTTP/HTTPS, TCP vs UDP, routing protocols, and network security.',
        'resources': ['Tanenbaum Computer Networks', 'Gate Smashers CN (YouTube)', 'Kurose & Ross'],
        'priority': 2,
    },
    'Python': {
        'tip': 'Practice OOP in Python, decorators, generators, list comprehensions, lambda, and standard libraries.',
        'resources': ['Real Python', 'Python Cookbook', 'HackerRank Python track'],
        'priority': 2,
    },
    'Java': {
        'tip': 'Master Collections framework, multithreading, JVM internals, OOP principles, and Spring basics.',
        'resources': ['Head First Java', 'Baeldung.com', 'Java Brains (YouTube)'],
        'priority': 2,
    },
    'Web Development': {
        'tip': 'Strengthen REST API design, HTTP methods, authentication (JWT/OAuth), and a frontend framework.',
        'resources': ['MDN Web Docs', 'The Odin Project', 'freeCodeCamp'],
        'priority': 2,
    },
    'System Design': {
        'tip': 'Study scalability, load balancing, caching (Redis), CDN, microservices, CAP theorem, and databases at scale.',
        'resources': ['System Design Primer (GitHub)', 'Grokking System Design', 'ByteByteGo (YouTube)'],
        'priority': 1,
    },
    'SQL': {
        'tip': 'Practice complex JOINs, subqueries, window functions (ROW_NUMBER, RANK), GROUP BY, and query optimisation.',
        'resources': ['LeetCode SQL 50', 'Mode SQL Tutorial', 'SQLZoo'],
        'priority': 1,
    },
    'coding': {
        'tip': 'Start with easy two-pointer and sliding window problems. Then move to medium DP and graph problems.',
        'resources': ['NeetCode.io', 'LeetCode Explore Cards', 'Codeforces Div-3 contests'],
        'priority': 1,
    },
}

COMPANY_TIPS = {
    'Amazon': 'Focus on Leadership Principles (14 LPs), OOP design, and medium-hard DSA. STAR format for HR answers.',
    'Google': 'Practice hard graph/DP problems on LeetCode. System design for senior roles. Focus on clean code.',
    'Microsoft': 'Strong OOP, system design, and behavioral rounds. Practice medium DSA. Study Azure basics.',
    'TCS':       'Aptitude, basic coding (easy level), verbal, and fundamental CS concepts are key for TCS NQT.',
    'Infosys':   'Focus on aptitude, pseudocode, verbal ability, and basic Python/Java coding for InfyTQ.',
    'Wipro':     'AMCAT pattern: aptitude, English, logical reasoning, and easy coding problems.',
}


def generate_full_recommendations(candidate_id: int) -> list:
    """
    Master recommendation generator.
    Combines interview performance, coding stats, and resume data.
    Returns a sorted list of recommendation dicts.
    """
    recs = []

    # ── 1. Interview weak topics ──────────────────────────────
    from utils.analytics import get_weak_topics
    weak = get_weak_topics(candidate_id)
    for wt in weak:
        topic = wt['topic_name']
        info  = TOPIC_TIPS.get(topic, {})
        recs.append({
            'icon':     '📚',
            'source':   'interview',
            'category': topic,
            'title':    f'Improve your {topic} score ({wt["avg_score"]}%)',
            'text':     info.get('tip', f'Practice more {topic} questions.'),
            'resources':info.get('resources', []),
            'priority': info.get('priority', 2),
            'badge':    'Weak Topic',
            'badge_cls':'danger',
        })

    # ── 2. Coding performance ─────────────────────────────────
    coding_stats = fetch_one("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN status='Accepted' THEN 1 ELSE 0 END) AS accepted
        FROM coding_submissions WHERE candidate_id = %s
    """, (candidate_id,))
    if coding_stats:
        total    = coding_stats[0] or 0
        accepted = coding_stats[1] or 0
        acc_rate = (accepted / total * 100) if total > 0 else 0
        if total == 0:
            recs.append({
                'icon': '💻', 'source': 'coding', 'category': 'Coding',
                'title': 'Start Coding Practice',
                'text': TOPIC_TIPS['coding']['tip'],
                'resources': TOPIC_TIPS['coding']['resources'],
                'priority': 1, 'badge': 'Not Started', 'badge_cls': 'warning',
            })
        elif acc_rate < 50:
            recs.append({
                'icon': '💻', 'source': 'coding', 'category': 'Coding',
                'title': f'Boost coding acceptance rate ({acc_rate:.0f}%)',
                'text': TOPIC_TIPS['coding']['tip'],
                'resources': TOPIC_TIPS['coding']['resources'],
                'priority': 1, 'badge': 'Needs Work', 'badge_cls': 'danger',
            })

    # ── 3. Resume-based recommendations ──────────────────────
    resume_row = fetch_one(
        "SELECT resume_id FROM resumes WHERE candidate_id = %s", (candidate_id,)
    )
    if not resume_row:
        recs.append({
            'icon': '📄', 'source': 'resume', 'category': 'Resume',
            'title': 'Upload Your Resume for Personalised Prep',
            'text': 'Upload your resume and we will analyse your skills, detect gaps, and recommend targeted preparation topics.',
            'resources': [],
            'priority': 2, 'badge': 'Action Needed', 'badge_cls': 'info',
        })
    else:
        analysis = fetch_one(
            "SELECT recommended_topics, analysis_text FROM resume_analysis WHERE resume_id = %s",
            (resume_row[0],)
        )
        if analysis and analysis[0]:
            for topic in (analysis[0] or '').split(','):
                topic = topic.strip()
                if topic and topic in TOPIC_TIPS:
                    info = TOPIC_TIPS[topic]
                    recs.append({
                        'icon': '📄', 'source': 'resume', 'category': topic,
                        'title': f'Strengthen {topic} (from Resume Analysis)',
                        'text': info['tip'],
                        'resources': info['resources'],
                        'priority': info['priority'],
                        'badge': 'Resume Match', 'badge_cls': 'primary',
                    })

    # ── 4. No interviews yet ──────────────────────────────────
    total_interviews = fetch_one(
        "SELECT COUNT(*) FROM interviews WHERE candidate_id = %s", (candidate_id,)
    )[0]
    if total_interviews == 0:
        recs.append({
            'icon': '🎯', 'source': 'system', 'category': 'Getting Started',
            'title': 'Take Your First Mock Interview',
            'text': 'Start with an Easy DBMS or Python interview to establish your baseline score.',
            'resources': [],
            'priority': 1, 'badge': 'Start Here', 'badge_cls': 'success',
        })

    # ── Sort by priority then source ─────────────────────────
    recs.sort(key=lambda r: (r['priority'], r['source']))
    return recs[:8]   # top 8 recommendations


def save_recommendations_v2(candidate_id: int, recs: list):
    """Persist generated recommendations to DB."""
    from models.db_helper import execute_query
    execute_query("DELETE FROM recommendations WHERE candidate_id = %s", (candidate_id,))
    for rec in recs:
        topic_row = fetch_one(
            "SELECT topic_id FROM topics WHERE topic_name = %s", (rec['category'],)
        )
        topic_id = topic_row[0] if topic_row else None
        if topic_id:
            execute_query("""
                INSERT INTO recommendations
                    (candidate_id, topic_id, recommendation_text, source, priority)
                VALUES (%s, %s, %s, %s, %s)
            """, (candidate_id, topic_id, rec['text'], rec.get('source','system'), rec.get('priority',2)))
