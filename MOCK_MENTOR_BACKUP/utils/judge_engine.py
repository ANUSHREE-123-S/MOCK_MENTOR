# utils/judge_engine.py
# ============================================================
# MockMentor Simulated Coding Judge Engine
# ============================================================
# Evaluates submitted code using keyword/pattern analysis.
# No real compiler needed — suitable for DBMS mini-project.
# Returns realistic verdicts: Accepted / Partial / Wrong Answer
# / Runtime Error, plus score, test counts, simulated timing.
# ============================================================

import re
import random
import time as _time

# ── Simulated memory/time ranges per difficulty ───────────────
PERF_PROFILE = {
    'easy':   {'time_range': (18, 95),   'mem_range': (14.2, 18.8)},
    'medium': {'time_range': (45, 280),  'mem_range': (16.4, 24.6)},
    'hard':   {'time_range': (120, 650), 'mem_range': (22.1, 38.4)},
}

# ── Master keyword rulebook ───────────────────────────────────
# Format: problem_key → {langs: {lang: [required_keywords]}, bonus: [...]}
PROBLEM_RULES = {

    # ─── ARRAYS ──────────────────────────────────────────────
    'two sum': {
        'any': ['for', 'if', 'return', ['dict', 'map', 'hashmap', '{}', 'defaultdict',
                                        'seen', 'complement', 'target']],
        'bonus': ['enumerate', 'complement', 'target - '],
        'anti': ['brute', 'o(n2)', 'o(n^2)'],   # wrong approach hints
    },
    'find maximum': {
        'any': [['max', 'maximum', 'largest', '>'], 'for', ['min', 'minimum', 'smallest', '<']],
        'bonus': ['max(', 'min(', 'sort'],
    },
    'three sum': {
        'any': ['sort', 'for', ['two pointer', 'left', 'right', 'while']],
        'bonus': ['sort', 'left', 'right', 'skip', 'duplicate'],
    },
    'product of array': {
        'any': ['for', 'result', ['prefix', 'product', 'left', 'right', 'multiply']],
        'bonus': ['prefix', 'suffix', 'left_product', 'right_product'],
    },
    'rotate matrix': {
        'any': [['transpose', 'reverse', 'zip', 'swap'], 'for'],
        'bonus': ['transpose', 'reverse', 'zip(*'],
    },
    'move zeroes': {
        'any': ['for', ['swap', 'pointer', 'insert', 'append', '== 0', '!= 0']],
        'bonus': ['two pointer', 'non_zero', 'insert_pos'],
    },
    'find missing': {
        'any': [['sum', 'xor', 'n*(n+1)', 'range']],
        'bonus': ['expected', 'actual', 'n*(n+1)/2', 'xor'],
    },
    'find duplicate': {
        'any': [['set', 'seen', 'dict', 'visited', 'floyd', 'slow', 'fast']],
        'bonus': ['seen', 'floyd', 'slow', 'fast', 'tortoise'],
    },
    'maximum product subarray': {
        'any': ['for', ['max_prod', 'min_prod', 'current', 'product']],
        'bonus': ['max_prod', 'min_prod', 'negative'],
    },
    'subarray sum': {
        'any': ['for', ['prefix', 'hashmap', 'count', 'cumsum', 'running']],
        'bonus': ['prefix_sum', 'count[', 'defaultdict'],
    },
    'jump game': {
        'any': [['reach', 'max_reach', 'greedy', 'farthest', 'can_reach']],
        'bonus': ['max_reach', 'greedy', 'farthest'],
    },
    'sort colors': {
        'any': [['low', 'mid', 'high', 'three pointer', 'dutch', 'flag']],
        'bonus': ['low', 'mid', 'high', 'swap'],
    },
    'kth largest': {
        'any': [['heap', 'sort', 'quick', 'partition', 'nth_element']],
        'bonus': ['heapq', 'nlargest', 'sort', 'partition'],
    },
    'count vowels': {
        'any': [['vowel', 'aeiou', 'in', 'count']],
        'bonus': ['aeiou', 'vowels', 'consonants'],
    },
    'sum of digits': {
        'any': [['digit', 'sum', '%', '//', 'while', 'str(']],
        'bonus': ['while', 'sum', 'digit'],
    },
    'check armstrong': {
        'any': [['len', 'power', '**', 'digit', 'sum']],
        'bonus': ['**', 'len(str', 'digit'],
    },
    'count words': {
        'any': [['split', 'count', 'len', 'words']],
        'bonus': ['split()', 'len(', 'strip'],
    },

    # ─── STRINGS ─────────────────────────────────────────────
    'reverse a string': {
        'any': [['[::-1]', 'reverse', 'reversed', 'join', 'swap']],
        'bonus': ['[::-1]', 'reversed(', 'join'],
    },
    'palindrome': {
        'any': [['[::-1]', 'reverse', 'left', 'right', 'equal', '==']],
        'bonus': ['[::-1]', 'isalnum', 'lower'],
    },
    'anagram': {
        'any': [['sort', 'count', 'counter', 'frequency', 'dict']],
        'bonus': ['sorted(', 'Counter(', 'collections'],
    },
    'longest substring': {
        'any': ['for', ['set', 'dict', 'window', 'sliding', 'left', 'right', 'max_len']],
        'bonus': ['left', 'right', 'window', 'max_len', 'seen'],
    },
    'longest common prefix': {
        'any': [['zip', 'sort', 'min', 'prefix', 'common']],
        'bonus': ['zip(*', 'sorted', 'min('],
    },
    'longest palindromic': {
        'any': ['for', ['expand', 'center', 'dp', 'palindrome', 'left', 'right']],
        'bonus': ['expand', 'center', 'palindrome'],
    },
    'group anagrams': {
        'any': [['sort', 'dict', 'defaultdict', 'tuple', 'counter']],
        'bonus': ['defaultdict', 'sorted(', 'tuple'],
    },
    'decode ways': {
        'any': ['dp', ['ways', 'decode', 'count']],
        'bonus': ['dp[', 'ways', 'valid'],
    },
    'minimum window': {
        'any': ['for', ['window', 'left', 'right', 'count', 'found', 'need']],
        'bonus': ['left', 'right', 'found', 'need', 'min_len'],
    },
    'regular expression': {
        'any': [['dp', 'match', 'star', 'dot', 'pattern']],
        'bonus': ['dp[', 'match', 'star', '*'],
    },

    # ─── MATH ────────────────────────────────────────────────
    'fizzbuzz': {
        'any': [['fizzbuzz', 'fizz', 'buzz'], ['%', 'mod', 'modulo'],
                ['3', '5', '15']],
        'bonus': ['fizzbuzz', '% 15', '% 3', '% 5'],
    },
    'fibonacci': {
        'any': [['fib', 'fibonacci', ['a,b', 'a, b', 'prev', 'curr', 'dp']]],
        'bonus': ['a, b = b', 'fib[i]', 'memoize'],
    },
    'check prime': {
        'any': [['prime', 'sqrt', '**0.5', 'divisor', 'factor']],
        'bonus': ['sqrt', '**0.5', 'range(2'],
    },
    'binary to decimal': {
        'any': [['int(', 'power', '2**', 'binary', 'bit']],
        'bonus': ['int(', ', 2)', '2**'],
    },
    'star pattern': {
        'any': [['*', 'for', 'range', 'print']],
        'bonus': ['for i in range', 'print('],
    },
    'swap two numbers': {
        'any': [['swap', 'temp', ',', 'xor', '^', 'a, b']],
        'bonus': ['a, b = b, a', '^=', 'temp'],
    },
    'sum of array': {
        'any': [['sum', 'total', '+', 'for', 'accumulate']],
        'bonus': ['sum(', 'total +=', 'reduce'],
    },
    'count occurrences': {
        'any': [['count', 'dict', 'counter', 'frequency', 'defaultdict']],
        'bonus': ['Counter(', 'defaultdict', 'get('],
    },

    # ─── DATA STRUCTURES ─────────────────────────────────────
    'reverse linked list': {
        'any': [['prev', 'next', 'current', 'head', 'node', 'pointer']],
        'bonus': ['prev = none', 'prev =  none', 'curr.next', 'prev'],
    },
    'valid parentheses': {
        'any': [['stack', 'append', 'pop', ['dict', 'map', 'matching']]],
        'bonus': ['stack', 'append', 'pop', 'empty'],
    },
    'next greater element': {
        'any': [['stack', 'monotonic', ['greater', 'larger', 'peek', 'top']]],
        'bonus': ['stack', 'monoton', 'while stack'],
    },
    'median of two': {
        'any': [['binary search', 'partition', 'half', 'left', 'right']],
        'bonus': ['binary', 'partition', 'left_half', 'half'],
    },
    'sliding window maximum': {
        'any': [['deque', 'monotonic', 'window', 'max']],
        'bonus': ['deque', 'popleft', 'monoton'],
    },
    'implement queue': {
        'any': [['stack', 's1', 's2', 'transfer', 'push', 'pop']],
        'bonus': ['s1', 's2', 'transfer', 'empty'],
    },
    'kth largest element': {
        'any': [['heap', 'sort', 'partition', 'quickselect']],
        'bonus': ['heapq', 'nlargest', 'quickselect'],
    },

    # ─── DYNAMIC PROGRAMMING ─────────────────────────────────
    'longest increasing': {
        'any': [['dp', 'lis', 'binary search', 'bisect', 'patience']],
        'bonus': ['bisect', 'dp[', 'lis'],
    },
    'coin change': {
        'any': ['dp', ['amount', 'coin', 'minimum', 'memo']],
        'bonus': ['dp[amount]', 'float("inf")', 'min('],
    },
    'decode ways': {
        'any': ['dp', ['valid', 'single', 'double', 'two_digit']],
        'bonus': ['dp[i]', 'two_digit', 'valid'],
    },
    'burst balloons': {
        'any': [['dp', 'interval', 'left', 'right', 'last']],
        'bonus': ['dp[l][r]', 'interval', 'last_balloon'],
    },
    'edit distance': {
        'any': [['dp', 'levenshtein', 'insert', 'delete', 'replace']],
        'bonus': ['dp[i][j]', 'min(', 'insert', 'delete'],
    },
    'maximum profit': {
        'any': [['dp', 'buy', 'sell', 'profit', 'transaction']],
        'bonus': ['buy', 'sell', 'dp[k]', 'transaction'],
    },
    'candy': {
        'any': ['for', ['left', 'right', 'rating', 'candy', 'neighbor']],
        'bonus': ['left_pass', 'right_pass', 'rating[i]'],
    },

    # ─── GRAPHS & TREES ──────────────────────────────────────
    'level order': {
        'any': [['queue', 'bfs', 'level', 'deque', 'append']],
        'bonus': ['deque', 'bfs', 'level'],
    },
    'validate binary search': {
        'any': [['min_val', 'max_val', 'bound', 'inorder', 'valid']],
        'bonus': ['min_val', 'max_val', 'inorder'],
    },
    'diameter of': {
        'any': [['dfs', 'depth', 'height', 'left', 'right', 'max_depth']],
        'bonus': ['left_depth', 'right_depth', 'diameter'],
    },
    'number of islands': {
        'any': [['dfs', 'bfs', 'visited', 'grid', 'count']],
        'bonus': ['dfs', 'bfs', 'visited', 'grid['],
    },
    'word ladder': {
        'any': [['bfs', 'queue', 'visited', 'neighbor', 'level']],
        'bonus': ['bfs', 'queue', 'visited', 'word'],
    },
    'longest consecutive': {
        'any': [['set', 'hash', 'start', 'streak', 'consecutive']],
        'bonus': ['set(', 'num - 1', 'streak'],
    },

    # ─── SORTING ─────────────────────────────────────────────
    'merge sort': {
        'any': [['merge', 'divide', 'mid', 'left', 'right', 'conquer']],
        'bonus': ['merge(', 'mid', 'left + right'],
    },
    'quick sort': {
        'any': [['pivot', 'partition', 'left', 'right', 'quicksort']],
        'bonus': ['pivot', 'partition', 'quicksort'],
    },
    'bubble sort': {
        'any': ['for', ['swap', 'adjacent', '>', '<', 'compare']],
        'bonus': ['swap', 'n-1-i', 'arr[j]'],
    },

    # ─── MISC ────────────────────────────────────────────────
    'spiral': {
        'any': [['top', 'bottom', 'left', 'right', 'boundary', 'shrink']],
        'bonus': ['top', 'bottom', 'left', 'right'],
    },
    'largest rectangle': {
        'any': [['stack', 'monotonic', 'height', 'width', 'area']],
        'bonus': ['stack', 'height', 'width', 'area'],
    },
    'russian doll': {
        'any': [['sort', 'lis', 'binary', 'bisect', 'dp']],
        'bonus': ['bisect', 'lis', 'sort('],
    },
    'minimum cost': {
        'any': [['prim', 'kruskal', 'mst', 'distance', 'manhattan']],
        'bonus': ['prim', 'kruskal', 'mst'],
    },
    'search in rotated': {
        'any': ['binary', ['mid', 'left', 'right', 'rotated', 'pivot']],
        'bonus': ['binary', 'mid', 'sorted_half'],
    },
    'n-queens': {
        'any': [['backtrack', 'queen', 'row', 'col', 'diagonal']],
        'bonus': ['backtrack', 'diagonal', 'col_set'],
    },
    'word break': {
        'any': [['dp', 'word', 'dict', 'prefix', 'memo']],
        'bonus': ['dp[i]', 'word_dict', 'memo'],
    },
    'generate parentheses': {
        'any': [['backtrack', 'open', 'close', 'recurse', 'dfs']],
        'bonus': ['backtrack', 'open_count', 'close_count'],
    },
    'trapping rain water': {
        'any': [['left', 'right', 'max_left', 'max_right', 'water', 'trap']],
        'bonus': ['max_left', 'max_right', 'water +='],
    },
    'permutations': {
        'any': [['backtrack', 'permut', 'swap', 'visited', 'recurse']],
        'bonus': ['backtrack', 'swap', 'permut'],
    },
    'subsets': {
        'any': [['backtrack', 'subset', 'include', 'exclude', 'power']],
        'bonus': ['backtrack', 'subset', 'include'],
    },
    'count pairs': {
        'any': [['dict', 'count', 'complement', 'target', 'hash']],
        'bonus': ['complement', 'seen', 'target -'],
    },
    'product except': {
        'any': ['prefix', ['suffix', 'left', 'right', 'result']],
        'bonus': ['prefix', 'suffix', 'result[i]'],
    },
    'detect cycle': {
        'any': [['slow', 'fast', 'floyd', 'visited', 'cycle']],
        'bonus': ['slow', 'fast', 'floyd', 'cycle'],
    },
    'floyd': {
        'any': [['slow', 'fast', 'tortoise', 'hare', 'cycle']],
        'bonus': ['slow.next', 'fast.next.next'],
    },
    'median stream': {
        'any': [['heap', 'max_heap', 'min_heap', 'balance', 'median']],
        'bonus': ['max_heap', 'min_heap', 'balance'],
    },
}


def _get_rule(title: str) -> dict:
    """Find the best matching rule for a problem title."""
    title_lw = title.lower()
    best_key = None
    best_len = 0
    for key in PROBLEM_RULES:
        if key in title_lw and len(key) > best_len:
            best_key = key
            best_len = len(key)
    return PROBLEM_RULES.get(best_key, {}) if best_key else {}


def _check_syntax_errors(code: str, language: str) -> str | None:
    """Return an error message if obvious syntax issues found."""
    code_lw = code.lower().strip()

    # Empty / trivially short
    if len(code_lw) < 15:
        return "Code is too short. Please write a complete solution."

    # Language-specific minimal checks
    if language == 'python':
        # Unmatched brackets
        opens  = code.count('(') + code.count('[') + code.count('{')
        closes = code.count(')') + code.count(']') + code.count('}')
        if abs(opens - closes) > 2:
            return "SyntaxError: Mismatched brackets detected."
        if 'def ' not in code_lw and 'for ' not in code_lw and 'print' not in code_lw:
            return "Your code doesn't seem to produce any output. Add print() statements."

    if language in ('java', 'cpp'):
        if '{' not in code and '}' not in code:
            return "Missing function body braces {}."
        if language == 'java' and 'main' not in code_lw:
            return "Java solution must have a main() method."
        if language == 'cpp' and 'int main' not in code_lw:
            return "C++ solution must have int main()."

    return None  # No error


def _score_against_rules(code: str, rule: dict) -> float:
    """
    Score code 0.0–1.0 based on keyword matching.
    'any':   list of required keyword groups (each group = OR match)
    'bonus': extra keywords that push score higher
    'anti':  keywords that indicate a wrong/suboptimal approach
    """
    if not rule:
        # No specific rule — generic scoring
        return _generic_score(code)

    code_lw = code.lower()
    groups  = rule.get('any', [])
    bonus   = rule.get('bonus', [])
    anti    = rule.get('anti', [])

    if not groups:
        return _generic_score(code)

    # Score each group
    group_scores = []
    for group in groups:
        if isinstance(group, list):
            # OR within list
            matched = any(kw.lower() in code_lw for kw in group)
        else:
            matched = group.lower() in code_lw
        group_scores.append(1.0 if matched else 0.0)

    base_score = sum(group_scores) / len(group_scores) if group_scores else 0.0

    # Bonus bump
    bonus_count = sum(1 for kw in bonus if kw.lower() in code_lw)
    bonus_ratio = bonus_count / len(bonus) if bonus else 0
    bonus_bump  = bonus_ratio * 0.25  # up to +0.25

    # Anti-pattern penalty
    anti_hits = sum(1 for kw in anti if kw.lower() in code_lw)
    anti_pen  = anti_hits * 0.15

    raw = min(1.0, base_score + bonus_bump - anti_pen)
    return max(0.0, raw)


def _generic_score(code: str) -> float:
    """Generic scoring for problems without specific rules."""
    code_lw = code.lower()
    score   = 0.0

    # Has meaningful length
    if len(code) > 50:  score += 0.2
    if len(code) > 150: score += 0.1

    # Has functions / methods
    if any(kw in code_lw for kw in ['def ', 'function ', 'void ', 'int ', 'public ']):
        score += 0.15

    # Has loops
    if any(kw in code_lw for kw in ['for ', 'while ', 'foreach']):
        score += 0.15

    # Has conditionals
    if any(kw in code_lw for kw in ['if ', 'else', 'elif', 'switch']):
        score += 0.1

    # Has return / output
    if any(kw in code_lw for kw in ['return', 'print', 'cout', 'system.out']):
        score += 0.15

    # Has data structures
    if any(kw in code_lw for kw in ['dict', 'list', 'array', 'map', 'set', 'stack', 'queue',
                                      'vector', 'arraylist', 'hashmap']):
        score += 0.15

    return min(1.0, score)


def _decide_per_testcase(code_score: float, tc_index: int, total_tc: int,
                          difficulty: str) -> bool:
    """
    Decide pass/fail for a single test case based on:
    - overall code score
    - test case index (easier ones pass first)
    - difficulty level
    """
    # Difficulty multiplier: hard problems require better code
    diff_mult = {'easy': 1.0, 'medium': 0.88, 'hard': 0.78}.get(difficulty.lower(), 0.85)

    # Position factor: earlier test cases (sample cases) easier to pass
    position_bonus = ((total_tc - tc_index) / total_tc) * 0.15

    effective_score = (code_score * diff_mult) + position_bonus

    # Thresholds
    if effective_score >= 0.85:
        return True
    if effective_score >= 0.55:
        # Probabilistic: good code passes most test cases
        threshold = effective_score
        return random.random() < threshold
    if effective_score >= 0.30:
        # Partial code passes some test cases
        threshold = effective_score * 0.7
        return random.random() < threshold
    return False


def evaluate_submission(code: str, language: str, title: str,
                         difficulty: str, testcases: list) -> dict:
    """
    Full evaluation pipeline.
    Returns:
        status       : 'Accepted' | 'Partial' | 'Wrong Answer' | 'Runtime Error'
        score        : 0–100 float
        test_passed  : int
        test_total   : int
        runtime_ms   : int  (simulated)
        memory_mb    : float (simulated)
        error_msg    : str | None
        tc_results   : list of per-test-case dicts
    """

    # ── Step 1: Syntax / obvious error check ──────────────────
    err = _check_syntax_errors(code, language)
    if err:
        return {
            'status':      'Runtime Error',
            'score':       0.0,
            'test_passed': 0,
            'test_total':  len(testcases),
            'runtime_ms':  0,
            'memory_mb':   0.0,
            'error_msg':   err,
            'tc_results':  [{'index': i+1, 'passed': False,
                              'input': tc.get('input_data',''),
                              'expected': tc.get('expected',''),
                              'got': 'Runtime Error'} for i, tc in enumerate(testcases)],
        }

    # ── Step 2: Score code quality ─────────────────────────────
    rule       = _get_rule(title)
    code_score = _score_against_rules(code, rule)

    # ── Step 3: Simulate per-test-case execution ───────────────
    total      = len(testcases)
    passed     = 0
    tc_results = []

    diff_key   = difficulty.lower() if difficulty else 'medium'
    profile    = PERF_PROFILE.get(diff_key, PERF_PROFILE['medium'])

    for i, tc in enumerate(testcases):
        tc_pass = _decide_per_testcase(code_score, i, total, diff_key)
        if tc_pass:
            passed += 1
            got = tc.get('expected', '').strip()
        else:
            # Generate a plausible-looking wrong output
            expected = tc.get('expected', '').strip()
            got = _generate_wrong_output(expected, code_score)

        tc_results.append({
            'index':    i + 1,
            'passed':   tc_pass,
            'input':    tc.get('input_data', ''),
            'expected': tc.get('expected', ''),
            'got':      got,
            'time_ms':  random.randint(*profile['time_range']),
        })

    # ── Step 4: Determine verdict ──────────────────────────────
    ratio = passed / total if total > 0 else 0.0

    if ratio == 1.0:
        status = 'Accepted'
        score  = 100.0
    elif ratio >= 0.6:
        status = 'Partial'
        score  = round(ratio * 100, 1)
    elif ratio > 0:
        status = 'Wrong Answer'
        score  = round(ratio * 100, 1)
    else:
        # If code quality is very low, Runtime Error; else Wrong Answer
        status = 'Runtime Error' if code_score < 0.2 else 'Wrong Answer'
        score  = 0.0

    # ── Step 5: Simulate execution metrics ────────────────────
    base_time = random.randint(*profile['time_range'])
    # Accepted solutions get slightly better (lower) time
    runtime_ms = base_time if status != 'Accepted' else max(10, base_time - random.randint(5, 30))
    memory_mb  = round(random.uniform(*profile['mem_range']), 1)

    return {
        'status':      status,
        'score':       score,
        'test_passed': passed,
        'test_total':  total,
        'runtime_ms':  runtime_ms,
        'memory_mb':   memory_mb,
        'error_msg':   None,
        'tc_results':  tc_results,
    }


def _generate_wrong_output(expected: str, score: float) -> str:
    """Generate a plausible-but-wrong output for failed test cases."""
    if not expected.strip():
        return 'null'

    # Try to corrupt the expected value slightly
    parts = expected.strip().split()

    if not parts:
        return '0'

    # If numeric output, shift by ±1 or ±2
    if parts[0].lstrip('-').isdigit():
        try:
            val = int(parts[0])
            offset = random.choice([-2, -1, 1, 2, val + 1])
            wrong_parts = [str(val + offset)] + parts[1:]
            return ' '.join(wrong_parts)
        except Exception:
            pass

    # If true/false
    if parts[0].lower() in ('true', 'false'):
        return 'false' if parts[0].lower() == 'true' else 'true'

    # String output — return first word only or empty
    if score < 0.2:
        return ''
    return parts[0] if len(parts) > 1 else (parts[0][:-1] if len(parts[0]) > 1 else '?')


def get_no_testcase_result(code: str, language: str,
                            title: str, difficulty: str) -> dict:
    """
    When no test cases are in DB, still evaluate code quality
    and return a reasonable result.
    """
    err = _check_syntax_errors(code, language)
    if err:
        return {'status': 'Runtime Error', 'score': 0.0,
                'test_passed': 0, 'test_total': 0,
                'runtime_ms': 0, 'memory_mb': 0.0, 'error_msg': err, 'tc_results': []}

    rule       = _get_rule(title)
    code_score = _score_against_rules(code, rule)
    diff_key   = difficulty.lower() if difficulty else 'medium'
    profile    = PERF_PROFILE.get(diff_key, PERF_PROFILE['medium'])

    if code_score >= 0.85:
        status, score = 'Accepted', 100.0
    elif code_score >= 0.55:
        status, score = 'Partial', round(code_score * 100, 1)
    elif code_score >= 0.25:
        status, score = 'Wrong Answer', round(code_score * 100, 1)
    else:
        status, score = 'Wrong Answer', 0.0

    return {
        'status':      status,
        'score':       score,
        'test_passed': 0,
        'test_total':  0,
        'runtime_ms':  random.randint(*profile['time_range']),
        'memory_mb':   round(random.uniform(*profile['mem_range']), 1),
        'error_msg':   None,
        'tc_results':  [],
    }