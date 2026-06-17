# utils/resume_analyzer.py
# Parses uploaded resume PDFs, extracts skills using keyword matching,
# and generates topic/company recommendations.

import re
import os
from config import Config

# ─────────────────────────────────────────────────────────────
# All known skills to detect (lowercase for matching)
# ─────────────────────────────────────────────────────────────
ALL_SKILLS = []
CATEGORY_MAP = {}   # skill → category
for cat, skills in Config.SKILL_MAP.items():
    for s in skills:
        ALL_SKILLS.append(s)
        CATEGORY_MAP[s] = cat

# Company matching: if these skills found → recommend company
COMPANY_SKILL_MATCH = {
    'Amazon':    ['python','java','aws','dynamodb','system design','algorithms'],
    'Google':    ['python','algorithms','system design','golang','data structures'],
    'Microsoft': ['c#','azure','java','.net','algorithms','system design'],
    'TCS':       ['python','java','sql','c++','manual testing','communication'],
    'Infosys':   ['python','java','sql','testing','communication'],
    'Wipro':     ['python','java','sql','communication','networking'],
}


def extract_text_from_pdf(filepath: str) -> str:
    """Extract raw text from a PDF file using PyPDF2."""
    text = ''
    try:
        import PyPDF2
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + '\n'
    except ImportError:
        # Fallback: read as binary and decode printable chars
        try:
            with open(filepath, 'rb') as f:
                raw = f.read()
            text = raw.decode('latin-1', errors='ignore')
            # Remove PDF binary noise
            text = re.sub(r'[^\x20-\x7E\n]', ' ', text)
        except Exception:
            pass
    except Exception:
        pass
    return text.strip()


def extract_text_from_txt(filepath: str) -> str:
    """Read plain text from a .txt file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ''


def extract_skills(text: str) -> list:
    """
    Scan raw resume text for known skills.
    Returns list of dicts: {skill_name, category}
    """
    text_lower = text.lower()
    found = []
    seen  = set()
    for skill in ALL_SKILLS:
        # Use word boundary matching so 'c' doesn't match inside 'css'
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower) and skill not in seen:
            seen.add(skill)
            found.append({'skill_name': skill, 'category': CATEGORY_MAP.get(skill, 'Other')})
    return found


def recommend_topics(skills: list) -> list:
    """Map extracted skills → interview topics to prepare for."""
    topic_set = set()
    skill_map  = Config.SKILL_TOPIC_MAP
    for s in skills:
        name = s['skill_name'].lower()
        if name in skill_map:
            topic_set.add(skill_map[name])
    # Always recommend core topics if weak
    if not topic_set:
        topic_set = {'Data Structures', 'Algorithms', 'DBMS'}
    return sorted(topic_set)


def recommend_companies(skills: list) -> list:
    """Return companies whose skill requirements overlap with resume."""
    skill_names = {s['skill_name'].lower() for s in skills}
    matches = []
    for company, req_skills in COMPANY_SKILL_MATCH.items():
        overlap = len(skill_names & set(req_skills))
        if overlap >= 2:
            matches.append((company, overlap))
    matches.sort(key=lambda x: -x[1])
    return [m[0] for m in matches[:4]]


def generate_analysis_text(skills: list, topics: list, companies: list, raw_text: str) -> str:
    """Build a human-readable analysis summary."""
    skill_names = [s['skill_name'] for s in skills]
    categories  = {}
    for s in skills:
        categories.setdefault(s['category'], []).append(s['skill_name'])

    lines = [
        f"✅ Detected {len(skill_names)} skills from your resume.",
        "",
    ]
    for cat, sklist in categories.items():
        lines.append(f"• {cat}: {', '.join(sklist)}")

    lines += [
        "",
        f"📚 Recommended interview topics based on your skills:",
    ]
    for t in topics:
        lines.append(f"  → {t}")

    if companies:
        lines += ["", "🏢 Companies that match your profile:"]
        for c in companies:
            lines.append(f"  → {c}")

    # Simple resume length indicator
    words = len(raw_text.split())
    if words < 200:
        lines += ["", "⚠️ Your resume appears short. Consider adding more project details."]
    elif words > 1000:
        lines += ["", "💡 Tip: Keep your resume concise — ideally 1 page for freshers."]

    return '\n'.join(lines)


def analyse_resume(filepath: str, file_ext: str) -> dict:
    """
    Full pipeline: extract text → detect skills → recommend topics/companies.
    Returns dict with all analysis data.
    """
    # Extract text
    if file_ext == 'pdf':
        raw_text = extract_text_from_pdf(filepath)
    else:
        raw_text = extract_text_from_txt(filepath)

    if not raw_text or len(raw_text) < 50:
        return {
            'raw_text': raw_text,
            'skills':   [],
            'topics':   ['Data Structures', 'Algorithms', 'DBMS'],
            'companies':[],
            'analysis': '⚠️ Could not extract sufficient text from the file. Try uploading a text-based PDF.',
            'match_score': 0,
        }

    skills    = extract_skills(raw_text)
    topics    = recommend_topics(skills)
    companies = recommend_companies(skills)
    analysis  = generate_analysis_text(skills, topics, companies, raw_text)

    # Basic match score: percentage of core skills found
    core_skills = ['python','java','c++','sql','data structures','algorithms','system design','dbms']
    found_core  = sum(1 for s in skills if s['skill_name'] in core_skills)
    match_score = round((found_core / len(core_skills)) * 100, 1)

    return {
        'raw_text':   raw_text,
        'skills':     skills,
        'topics':     topics,
        'companies':  companies,
        'analysis':   analysis,
        'match_score':match_score,
    }
