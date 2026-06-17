# UPGRADE GUIDE — MockMentor v2
# Smart Placement Preparation & Interview Intelligence Platform
# ============================================================

## What was added in this upgrade

| Module              | What it does                                              |
|---------------------|-----------------------------------------------------------|
| Coding Round        | Problem list, code editor, test case scoring, analytics   |
| Company Prep        | 8 companies, rounds, questions, interview experiences     |
| AI Recommendations  | Intelligent suggestions based on scores, coding, resume   |
| Resume Analyzer     | Upload PDF/TXT, extract skills, recommend topics/companies|
| Upgraded Dashboard  | 6 stat cards, timeline, company readiness, charts         |

---

## STEP-BY-STEP UPGRADE INSTRUCTIONS

### Step 1 — Install new Python dependency

```bash
# Activate your virtualenv first (if using one)
source venv/bin/activate          # macOS/Linux
venv\Scripts\activate             # Windows

pip install PyPDF2==3.0.1
```

### Step 2 — Import the upgrade SQL

In phpMyAdmin (XAMPP):
1. Open phpMyAdmin → select `mockmentor_db`
2. Click **Import** tab
3. Choose `database_upgrade.sql`
4. Click **Go**

OR from terminal:
```bash
mysql -u root -p mockmentor_db < database_upgrade.sql
```

Verify new tables:
```sql
USE mockmentor_db;
SHOW TABLES;
-- Should now show: companies, company_rounds, company_questions,
-- company_experiences, coding_questions, coding_testcases,
-- coding_submissions, resumes, extracted_skills, resume_analysis
```

### Step 3 — Create uploads folder

```bash
mkdir -p static/uploads
```

Or on Windows:
```
mkdir static\uploads
```

### Step 4 — Restart Flask

```bash
python app.py
```

### Step 5 — Access new features

| Feature              | URL                                    |
|----------------------|----------------------------------------|
| Upgraded Dashboard   | http://localhost:5000/dashboard        |
| Coding Problems      | http://localhost:5000/coding/          |
| Coding Analytics     | http://localhost:5000/coding/analytics |
| Company List         | http://localhost:5000/company/         |
| Company Analytics    | http://localhost:5000/company/analytics|
| Resume Analyzer      | http://localhost:5000/resume/          |

---

## COMMON ERRORS & FIXES

### Error: `No module named 'PyPDF2'`
```bash
pip install PyPDF2==3.0.1
```

### Error: `Table 'coding_questions' doesn't exist`
```bash
mysql -u root -p mockmentor_db < database_upgrade.sql
```

### Error: `FileNotFoundError: static/uploads`
```bash
mkdir -p static/uploads
```

### Error: `AttributeError: 'NoneType' coding_stats`
The coding_stats variable now defaults to `{'attempted':0,'solved':0,'avg_score':0}` safely.
Make sure you are using the upgraded `student_routes.py`.

### Error: `jinja2.exceptions.TemplateNotFound: coding/coding_home.html`
Make sure the folders exist:
```bash
ls templates/coding/
ls templates/company/
ls templates/resume/
```

### Charts not loading on dashboard
Open browser DevTools → Console. If you see 404 on `/coding/api/stats`,
ensure the coding blueprint is registered in `app.py`.

---

## NEW SQL QUERIES REFERENCE

```sql
-- Most asked coding problems
SELECT cq.title, COUNT(cs.sub_id) AS attempts,
       SUM(CASE WHEN cs.status='Accepted' THEN 1 ELSE 0 END) AS accepted
FROM coding_submissions cs
JOIN coding_questions cq ON cs.cq_id = cq.cq_id
GROUP BY cq.cq_id ORDER BY attempts DESC LIMIT 10;

-- Company question frequency analysis
SELECT co.company_name, t.topic_name, COUNT(*) AS q_count
FROM company_questions cq
JOIN companies co ON cq.company_id = co.company_id
JOIN topics t ON cq.topic_id = t.topic_id
GROUP BY co.company_id, t.topic_id ORDER BY q_count DESC;

-- Coding leaderboard
SELECT c.name, COUNT(DISTINCT cs.cq_id) AS problems_solved,
       ROUND(AVG(cs.score),1) AS avg_score
FROM coding_submissions cs
JOIN candidates c ON cs.candidate_id = c.candidate_id
WHERE cs.status = 'Accepted'
GROUP BY cs.candidate_id ORDER BY problems_solved DESC;

-- Resume skill distribution
SELECT category, COUNT(*) AS skill_count
FROM extracted_skills GROUP BY category ORDER BY skill_count DESC;

-- Students who uploaded resume
SELECT c.name, ra.match_score, ra.recommended_topics
FROM resume_analysis ra
JOIN resumes r ON ra.resume_id = r.resume_id
JOIN candidates c ON r.candidate_id = c.candidate_id
ORDER BY ra.match_score DESC;
```

---

## FILE CHANGES SUMMARY

### New files added:
- `database_upgrade.sql`            ← Run this to add new tables
- `routes/coding_routes.py`         ← Coding module blueprint
- `routes/company_routes.py`        ← Company prep blueprint
- `routes/resume_routes.py`         ← Resume analyzer blueprint
- `utils/recommendation_engine.py`  ← AI recommendation logic
- `utils/resume_analyzer.py`        ← PDF skill extraction
- `templates/coding/coding_home.html`
- `templates/coding/coding_problem.html`
- `templates/coding/coding_analytics.html`
- `templates/company/company_list.html`
- `templates/company/company_detail.html`
- `templates/company/add_experience.html`
- `templates/company/all_experiences.html`
- `templates/company/company_analytics.html`
- `templates/resume/resume_home.html`

### Modified files:
- `app.py`                          ← Registers 3 new blueprints
- `config.py`                       ← Added upload, skill, coding settings
- `requirements.txt`                ← Added PyPDF2
- `routes/student_routes.py`        ← Enhanced dashboard with new stats
- `templates/dashboard.html`        ← Full v2 upgrade
- `templates/base.html`             ← New nav links
- `static/css/style.css`            ← ~230 new lines appended
- `static/js/main.js`               ← ~50 new lines appended
