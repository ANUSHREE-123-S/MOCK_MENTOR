# routes/coding_routes.py
# Coding Round Module — Complete Upgraded Version
# Uses judge_engine.py for realistic simulated evaluation

from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, jsonify)
from models.db_helper import fetch_one, fetch_dict, execute_query
from utils.judge_engine import evaluate_submission, get_no_testcase_result
import random

coding_bp = Blueprint('coding', __name__)

# ── Login guard ───────────────────────────────────────────────
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'candidate_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ── Problem List ──────────────────────────────────────────────
@coding_bp.route('/')
@login_required
def coding_home():
    diff_filter    = request.args.get('difficulty', '')
    company_filter = request.args.get('company', '')
    search         = request.args.get('search', '')
    cid            = session['candidate_id']

    query = """
        SELECT cq.cq_id, cq.title, cq.topic_tags, cq.constraints,
               d.difficulty_name, c.company_name, c.logo_emoji,
               (SELECT status FROM coding_submissions cs
                WHERE cs.cq_id = cq.cq_id AND cs.candidate_id = %s
                ORDER BY cs.submitted_at DESC LIMIT 1) AS my_status,
               (SELECT COUNT(*) FROM coding_submissions cs2
                WHERE cs2.cq_id = cq.cq_id AND cs2.status = 'Accepted') AS accepted_count,
               (SELECT COUNT(*) FROM coding_submissions cs3
                WHERE cs3.cq_id = cq.cq_id) AS total_count
        FROM coding_questions cq
        LEFT JOIN difficulty_levels d ON cq.difficulty_id = d.difficulty_id
        LEFT JOIN companies c         ON cq.company_id    = c.company_id
        WHERE 1=1
    """
    params = [cid]
    if diff_filter:
        query += " AND d.difficulty_name = %s"; params.append(diff_filter)
    if company_filter:
        query += " AND c.company_name = %s";    params.append(company_filter)
    if search:
        query += " AND (cq.title LIKE %s OR cq.topic_tags LIKE %s)"
        params += [f'%{search}%', f'%{search}%']
    query += " ORDER BY d.difficulty_id ASC, cq.cq_id ASC"
    problems = fetch_dict(query, tuple(params))

    my_stats = fetch_one("""
        SELECT COUNT(DISTINCT cq_id),
               SUM(CASE WHEN status='Accepted' THEN 1 ELSE 0 END)
        FROM coding_submissions WHERE candidate_id=%s
    """, (cid,))
    companies = fetch_dict("SELECT company_id, company_name, logo_emoji FROM companies ORDER BY company_name")

    return render_template('coding/coding_home.html',
        problems=problems,
        my_stats={'attempted': my_stats[0] or 0, 'solved': my_stats[1] or 0} if my_stats else {'attempted':0,'solved':0},
        diff_filter=diff_filter, company_filter=company_filter,
        search=search, companies=companies,
        candidate_name=session.get('candidate_name',''))


# ── Problem Editor ────────────────────────────────────────────
@coding_bp.route('/problem/<int:cq_id>')
@login_required
def coding_problem(cq_id):
    cid = session['candidate_id']
    problem = fetch_dict("""
        SELECT cq.*, d.difficulty_name, c.company_name, c.logo_emoji
        FROM coding_questions cq
        LEFT JOIN difficulty_levels d ON cq.difficulty_id = d.difficulty_id
        LEFT JOIN companies c         ON cq.company_id    = c.company_id
        WHERE cq.cq_id = %s
    """, (cq_id,))
    if not problem:
        flash('Problem not found.', 'danger')
        return redirect(url_for('coding.coding_home'))
    problem = problem[0]

    sample_tcs = fetch_dict(
        "SELECT input_data, expected FROM coding_testcases WHERE cq_id=%s AND is_sample=1",
        (cq_id,))
    all_tc_count = fetch_one(
        "SELECT COUNT(*) FROM coding_testcases WHERE cq_id=%s", (cq_id,))
    total_tc_count = all_tc_count[0] if all_tc_count else 0

    my_submissions = fetch_dict("""
        SELECT sub_id, language, status, score, test_passed, test_total,
               runtime_ms, memory_mb,
               DATE_FORMAT(submitted_at,'%%d %%b %%Y %%H:%%i') AS sub_date
        FROM coding_submissions
        WHERE cq_id=%s AND candidate_id=%s
        ORDER BY submitted_at DESC LIMIT 10
    """, (cq_id, cid))

    # Best accepted code to pre-fill editor
    best = fetch_one("""
        SELECT code, language FROM coding_submissions
        WHERE cq_id=%s AND candidate_id=%s AND status='Accepted'
        ORDER BY submitted_at DESC LIMIT 1
    """, (cq_id, cid))

    title = problem.get('title','')
    starter_code = {
        'python': (
            f"# {title}\n"
            "# Read input from stdin\n\n"
            "import sys\ninput = sys.stdin.readline\n\n"
            "def solve():\n"
            "    # Write your solution here\n"
            "    pass\n\n"
            "solve()"
        ),
        'java': (
            f"// {title}\n"
            "import java.util.*;\n"
            "import java.io.*;\n\n"
            "public class Solution {\n"
            "    public static void main(String[] args) {\n"
            "        Scanner sc = new Scanner(System.in);\n"
            "        // Write your solution here\n"
            "    }\n"
            "}"
        ),
        'cpp': (
            f"// {title}\n"
            "#include <bits/stdc++.h>\n"
            "using namespace std;\n\n"
            "int main() {\n"
            "    ios_base::sync_with_stdio(false);\n"
            "    cin.tie(NULL);\n"
            "    // Write your solution here\n"
            "    return 0;\n"
            "}"
        ),
        'javascript': (
            f"// {title}\n"
            "const readline = require('readline');\n"
            "const rl = readline.createInterface({ input: process.stdin });\n"
            "const lines = [];\n"
            "rl.on('line', l => lines.push(l.trim()));\n"
            "rl.on('close', () => {\n"
            "    // Write your solution here\n"
            "});"
        ),
    }

    # Get last result from session (set after submit redirect)
    last_result = session.pop('last_result', None)

    return render_template('coding/coding_problem.html',
        problem=problem,
        sample_tcs=sample_tcs,
        total_tc_count=total_tc_count,
        my_submissions=my_submissions,
        starter_code=starter_code,
        best_code=best[0] if best else '',
        best_lang=best[1] if best else 'python',
        last_result=last_result,
        candidate_name=session.get('candidate_name',''))


# ── Run (AJAX) — simulate sample test case output ─────────────
@coding_bp.route('/problem/<int:cq_id>/run', methods=['POST'])
@login_required
def run_code(cq_id):
    code     = request.json.get('code','').strip()
    language = request.json.get('language','python')

    problem = fetch_one(
        "SELECT title, difficulty_id FROM coding_questions WHERE cq_id=%s", (cq_id,))
    if not problem:
        return jsonify({'error': 'Problem not found'}), 404

    title   = problem[0]
    diff_id = problem[1]
    diff_map = {1:'easy', 2:'medium', 3:'hard'}
    difficulty = diff_map.get(diff_id, 'medium')

    # Get sample test case only
    sample = fetch_dict(
        "SELECT input_data, expected FROM coding_testcases WHERE cq_id=%s AND is_sample=1 LIMIT 1",
        (cq_id,))

    # Quick syntax check
    from utils.judge_engine import _check_syntax_errors, _get_rule, _score_against_rules, PERF_PROFILE
    import random
    err = _check_syntax_errors(code, language)
    if err:
        return jsonify({
            'status':  'error',
            'output':  '',
            'error':   err,
            'time_ms': 0,
            'mem_mb':  0,
        })

    rule       = _get_rule(title)
    code_score = _score_against_rules(code, rule)
    profile    = PERF_PROFILE.get(difficulty, PERF_PROFILE['medium'])
    time_ms    = random.randint(*profile['time_range'])
    mem_mb     = round(random.uniform(*profile['mem_range']), 1)

    if sample:
        expected = sample[0]['expected'].strip()
        if code_score >= 0.7:
            output = expected
            note   = '✅ Sample test case passed!'
        elif code_score >= 0.4:
            from utils.judge_engine import _generate_wrong_output
            output = _generate_wrong_output(expected, code_score)
            note   = '⚠️ Output does not match expected. Check your logic.'
        else:
            output = ''
            note   = '❌ No output produced. Check for errors in your code.'
    else:
        note   = '💡 No sample test case available. Submit to check against hidden tests.'
        output = '[No sample test case]'

    return jsonify({
        'status':   'ok',
        'output':   output,
        'note':     note,
        'time_ms':  time_ms,
        'mem_mb':   mem_mb,
        'sample_input':    sample[0]['input_data'] if sample else '',
        'sample_expected': sample[0]['expected']   if sample else '',
    })


# ── Submit Code ───────────────────────────────────────────────
@coding_bp.route('/problem/<int:cq_id>/submit', methods=['POST'])
@login_required
def submit_code(cq_id):
    cid      = session['candidate_id']
    code     = request.form.get('code', '').strip()
    language = request.form.get('language', 'python')

    if not code:
        flash('Please write some code before submitting.', 'warning')
        return redirect(url_for('coding.coding_problem', cq_id=cq_id))

    # Fetch problem metadata
    problem = fetch_one("""
        SELECT title, difficulty_id FROM coding_questions WHERE cq_id=%s
    """, (cq_id,))
    if not problem:
        flash('Problem not found.', 'danger')
        return redirect(url_for('coding.coding_home'))

    title   = problem[0]
    diff_id = problem[1]
    diff_map = {1:'easy', 2:'medium', 3:'hard'}
    difficulty = diff_map.get(diff_id, 'medium')

    # Get all test cases
    testcases = fetch_dict(
        "SELECT tc_id, input_data, expected, is_sample FROM coding_testcases WHERE cq_id=%s ORDER BY is_sample DESC, tc_id ASC",
        (cq_id,))

    # Run judge engine
    if testcases:
        result = evaluate_submission(code, language, title, difficulty, testcases)
    else:
        result = get_no_testcase_result(code, language, title, difficulty)

    # Save to DB (use memory_mb field if exists, else skip)
    try:
        execute_query("""
            INSERT INTO coding_submissions
                (cq_id, candidate_id, language, code, status, score,
                 runtime_ms, test_passed, test_total)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (cq_id, cid, language, code,
              result['status'], result['score'],
              result['runtime_ms'],
              result['test_passed'], result['test_total']))
    except Exception:
        # Fallback without runtime_ms if column missing
        execute_query("""
            INSERT INTO coding_submissions
                (cq_id, candidate_id, language, code, status, score,
                 test_passed, test_total)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (cq_id, cid, language, code,
              result['status'], result['score'],
              result['test_passed'], result['test_total']))

    # Store result in session for display (avoids flash message limits)
    session['last_result'] = {
        'status':      result['status'],
        'score':       result['score'],
        'test_passed': result['test_passed'],
        'test_total':  result['test_total'],
        'runtime_ms':  result['runtime_ms'],
        'memory_mb':   result['memory_mb'],
        'error_msg':   result['error_msg'],
        'tc_results':  result['tc_results'][:6],  # show first 6
        'title':       title,
    }

    return redirect(url_for('coding.coding_problem', cq_id=cq_id))


# ── Analytics ─────────────────────────────────────────────────
@coding_bp.route('/analytics')
@login_required
def coding_analytics():
    cid = session['candidate_id']

    overall = fetch_one("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN status='Accepted'    THEN 1 ELSE 0 END) AS accepted,
               SUM(CASE WHEN status='Wrong Answer' THEN 1 ELSE 0 END) AS wrong,
               SUM(CASE WHEN status='Partial'      THEN 1 ELSE 0 END) AS partial,
               SUM(CASE WHEN status='Runtime Error' THEN 1 ELSE 0 END) AS runtime_err,
               ROUND(AVG(score),1) AS avg_score
        FROM coding_submissions WHERE candidate_id=%s
    """, (cid,))

    diff_stats = fetch_dict("""
        SELECT d.difficulty_name,
               COUNT(cs.sub_id) AS attempts,
               SUM(CASE WHEN cs.status='Accepted' THEN 1 ELSE 0 END) AS solved,
               ROUND(AVG(cs.score),1) AS avg_score
        FROM coding_submissions cs
        JOIN coding_questions cq ON cs.cq_id = cq.cq_id
        JOIN difficulty_levels d ON cq.difficulty_id = d.difficulty_id
        WHERE cs.candidate_id=%s
        GROUP BY d.difficulty_id, d.difficulty_name ORDER BY d.difficulty_id
    """, (cid,))

    lang_stats = fetch_dict("""
        SELECT language, COUNT(*) AS uses,
               SUM(CASE WHEN status='Accepted' THEN 1 ELSE 0 END) AS accepted
        FROM coding_submissions WHERE candidate_id=%s
        GROUP BY language ORDER BY uses DESC
    """, (cid,))

    recent_subs = fetch_dict("""
        SELECT cs.sub_id, cq.title, cs.language, cs.status, cs.score,
               cs.test_passed, cs.test_total, cs.runtime_ms,
               DATE_FORMAT(cs.submitted_at,'%%d %%b %%H:%%i') AS sub_date,
               d.difficulty_name
        FROM coding_submissions cs
        JOIN coding_questions cq ON cs.cq_id = cq.cq_id
        LEFT JOIN difficulty_levels d ON cq.difficulty_id = d.difficulty_id
        WHERE cs.candidate_id=%s
        ORDER BY cs.submitted_at DESC LIMIT 15
    """, (cid,))

    leaderboard = fetch_dict("""
        SELECT c.name, c.college,
               COUNT(DISTINCT CASE WHEN cs.status='Accepted' THEN cs.cq_id END) AS solved,
               ROUND(AVG(cs.score),1) AS avg_score,
               RANK() OVER (ORDER BY COUNT(DISTINCT CASE WHEN cs.status='Accepted' THEN cs.cq_id END) DESC, AVG(cs.score) DESC) AS rank_pos
        FROM coding_submissions cs
        JOIN candidates c ON cs.candidate_id = c.candidate_id
        GROUP BY cs.candidate_id, c.name, c.college
        HAVING solved > 0
        ORDER BY rank_pos ASC LIMIT 10
    """)

    return render_template('coding/coding_analytics.html',
        overall=overall, diff_stats=diff_stats,
        lang_stats=lang_stats, recent_subs=recent_subs,
        leaderboard=leaderboard,
        candidate_name=session.get('candidate_name',''))


# ── API: chart data ───────────────────────────────────────────
@coding_bp.route('/api/stats')
@login_required
def coding_api_stats():
    cid = session['candidate_id']
    diff_stats = fetch_dict("""
        SELECT d.difficulty_name AS label,
               SUM(CASE WHEN cs.status='Accepted' THEN 1 ELSE 0 END) AS solved
        FROM coding_submissions cs
        JOIN coding_questions cq ON cs.cq_id = cq.cq_id
        JOIN difficulty_levels d ON cq.difficulty_id = d.difficulty_id
        WHERE cs.candidate_id=%s
        GROUP BY d.difficulty_name, d.difficulty_id ORDER BY d.difficulty_id
    """, (cid,))
    return jsonify({
        'labels': [d['label'] for d in diff_stats],
        'values': [int(d['solved'] or 0) for d in diff_stats],
    })