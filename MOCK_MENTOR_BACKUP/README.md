# 🎓 MockMentor – Smart Interview Preparation & Performance Analytics System

A full-stack DBMS project built with **Python Flask**, **MySQL**, and **Bootstrap 5**.

---

## 📁 Complete Project Structure

```
mockmentor/
├── app.py                    ← Flask application entry point
├── config.py                 ← Configuration (DB, secret key, settings)
├── requirements.txt          ← Python dependencies
├── database.sql              ← Complete MySQL schema + seed data
├── setup_admin.py            ← One-time admin account setup script
│
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py        ← Register, Login, Logout
│   ├── student_routes.py     ← Dashboard, Analytics, Leaderboard, Reports
│   ├── interview_routes.py   ← Start Interview, Take Interview, Submit
│   ├── admin_routes.py       ← Admin Panel, Question CRUD, Candidates
│   └── api_routes.py         ← JSON APIs for Chart.js
│
├── models/
│   ├── __init__.py
│   └── db_helper.py          ← Reusable DB query functions
│
├── utils/
│   ├── __init__.py
│   ├── analytics.py          ← Score analytics, weak topic detection
│   └── pdf_generator.py      ← PDF report generation (ReportLab)
│
├── templates/
│   ├── base.html             ← Base layout with navbar, dark mode
│   ├── index.html            ← Landing/Home page
│   ├── login.html            ← Student login
│   ├── register.html         ← Student registration
│   ├── dashboard.html        ← Student dashboard
│   ├── start_interview.html  ← Topic & difficulty selection
│   ├── take_interview.html   ← Interview with timer
│   ├── analytics.html        ← Charts & performance analytics
│   ├── leaderboard.html      ← Global rankings
│   ├── report.html           ← Interview performance report
│   ├── interview_history.html← Past interviews list
│   ├── profile.html          ← Student profile
│   ├── admin_login.html      ← Admin login
│   ├── admin_dashboard.html  ← Admin overview
│   ├── admin_questions.html  ← Question bank management
│   ├── admin_add_question.html
│   ├── admin_edit_question.html
│   └── admin_candidates.html ← Candidate management
│
└── static/
    ├── css/
    │   └── style.css         ← Complete stylesheet with dark mode
    └── js/
        └── main.js           ← Dark mode, animations, utilities
```

---

## 🛠️ STEP-BY-STEP EXECUTION GUIDE

### STEP 1 — Prerequisites

Make sure you have installed:
- **Python 3.9+**: https://www.python.org/downloads/
- **MySQL 8.0+**: https://dev.mysql.com/downloads/mysql/
- **pip** (comes with Python)

Verify:
```bash
python --version     # Should show Python 3.9+
mysql --version      # Should show MySQL 8.0+
pip --version
```

---

### STEP 2 — Download / Clone the Project

```bash
# If you have the zip file, extract it:
unzip mockmentor.zip -d mockmentor
cd mockmentor

# OR clone from git:
# git clone <repo-url>
# cd mockmentor
```

---

### STEP 3 — Create a Python Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it:
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

---

### STEP 4 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `Flask` — web framework
- `Flask-MySQLdb` — MySQL connection for Flask
- `Werkzeug` — password hashing, routing utilities
- `reportlab` — PDF generation
- `mysqlclient` — Python MySQL driver

**If mysqlclient fails to install:**

On Ubuntu/Debian:
```bash
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
pip install mysqlclient
```

On macOS (with Homebrew):
```bash
brew install mysql-client
export PKG_CONFIG_PATH="/usr/local/opt/mysql-client/lib/pkgconfig"
pip install mysqlclient
```

On Windows:
```bash
pip install mysqlclient --only-binary=:all:
# OR download wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#mysqlclient
```

---

### STEP 5 — Setup MySQL Database

**5a. Start MySQL service:**

On Windows: Open MySQL Workbench or Services → Start MySQL80
On macOS: `brew services start mysql`
On Linux: `sudo systemctl start mysql`

**5b. Login to MySQL:**
```bash
mysql -u root -p
# Enter your MySQL root password when prompted
# (press Enter if no password set)
```

**5c. Create and import the database:**
```sql
-- Inside MySQL shell:
CREATE DATABASE IF NOT EXISTS mockmentor_db;
EXIT;
```

Then import the schema from your terminal:
```bash
mysql -u root -p mockmentor_db < database.sql
```

**Verify import worked:**
```bash
mysql -u root -p mockmentor_db -e "SHOW TABLES;"
```

You should see 10 tables: candidates, admins, topics, difficulty_levels, questions, interviews, responses, interview_feedback, leaderboard, recommendations.

---

### STEP 6 — Configure the Application

Open `config.py` and update these settings:

```python
MYSQL_HOST     = 'localhost'
MYSQL_USER     = 'root'
MYSQL_PASSWORD = 'your_mysql_password'  # ← CHANGE THIS
MYSQL_DB       = 'mockmentor_db'
```

If your MySQL has no password, leave `MYSQL_PASSWORD = ''`.

---

### STEP 7 — Set Up the Admin Account

```bash
# Update MYSQL_PASSWORD in setup_admin.py first, then:
python setup_admin.py
```

Expected output:
```
✅ Admin account created successfully!
   Username: admin
   Password: admin123
```

---

### STEP 8 — Run the Flask Server

```bash
python app.py
```

Expected output:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

---

### STEP 9 — Access the Application in Browser

Open your browser and go to:

| URL | Page |
|-----|------|
| http://127.0.0.1:5000/ | Home / Landing Page |
| http://127.0.0.1:5000/register | Student Registration |
| http://127.0.0.1:5000/login | Student Login |
| http://127.0.0.1:5000/dashboard | Student Dashboard |
| http://127.0.0.1:5000/interview/start | Start Mock Interview |
| http://127.0.0.1:5000/analytics | Performance Analytics |
| http://127.0.0.1:5000/leaderboard | Leaderboard |
| http://127.0.0.1:5000/admin/login | Admin Login |
| http://127.0.0.1:5000/admin/dashboard | Admin Dashboard |
| http://127.0.0.1:5000/admin/questions | Question Management |

---

## 🔑 Default Credentials

### Admin Login
| Field | Value |
|-------|-------|
| URL | http://127.0.0.1:5000/admin/login |
| Username | `admin` |
| Password | `admin123` |

### Test Student (from seed data)
Register a new account at `/register` or use the database seed candidates (note: seed candidate passwords are demo hashes — register a fresh account for testing).

---

## 🗃️ Database Schema (ER Overview)

```
candidates ──┬──< interviews >──── topics
             │         │
             │         └──< responses >──── questions >──── topics
             │                                    │
             │                               difficulty_levels
             │
             ├──< leaderboard
             └──< recommendations >──── topics

interviews ──< interview_feedback
```

### Relationships
- **candidates** → **interviews**: One-to-Many (one student, many interviews)
- **interviews** → **responses**: One-to-Many (one interview, many answers)
- **questions** → **responses**: One-to-Many (one question, many student answers)
- **topics** → **questions**: One-to-Many (one topic, many questions)
- **difficulty_levels** → **questions**: One-to-Many
- **candidates** → **leaderboard**: One-to-One
- **candidates** → **recommendations**: One-to-Many

---

## 📊 DBMS Concepts Implemented

| Concept | Where Used |
|---------|------------|
| Primary Keys | All 10 tables (AUTO_INCREMENT) |
| Foreign Keys | interviews→candidates, responses→interviews, etc. |
| Normalization | Topics, difficulty_levels are separate normalized tables |
| 1NF | All atomic values, no repeating groups |
| 2NF | All non-key columns depend on full primary key |
| 3NF | No transitive dependencies (separate topics/difficulty tables) |
| Indexes | email on candidates, topic_id/difficulty_id on questions |
| Joins | All analytics queries use JOINs across multiple tables |
| Aggregate Functions | AVG(), COUNT(), MAX(), SUM(), ROUND() in analytics |
| GROUP BY | Topic-wise performance, leaderboard ranking |
| CRUD | Full Create/Read/Update/Delete for questions and candidates |
| Referential Integrity | ON DELETE CASCADE on all foreign keys |

---

## 🔧 Common Error Fixes

### Error: `ModuleNotFoundError: No module named 'flask_mysqldb'`
```bash
pip install Flask-MySQLdb
```

### Error: `OperationalError: (2003, "Can't connect to MySQL server")`
- Check MySQL is running: `sudo systemctl status mysql`
- Check MYSQL_PASSWORD in config.py matches your MySQL password

### Error: `OperationalError: (1045, "Access denied for user")`
- Wrong MySQL username/password in config.py
- Try: `mysql -u root -p` in terminal to verify credentials

### Error: `OperationalError: (1049, "Unknown database 'mockmentor_db'")`
- Run Step 5 again to create and import the database

### Error: `ImportError: libmysqlclient.so.21: cannot open shared object`
On Linux:
```bash
sudo apt-get install libmysqlclient-dev
```

### Error: `jinja2.exceptions.TemplateNotFound`
- Make sure you're running `python app.py` from the `mockmentor/` directory
- Not from a subdirectory

### Charts not showing
- Open browser DevTools (F12) → Console → check for errors
- Make sure you have completed at least one interview as a student

### PDF download not working
```bash
pip install reportlab
```

### Port 5000 already in use
```bash
# Change port in app.py:
app.run(debug=True, port=5001)
```

---

## 🚀 Features Checklist

- ✅ Student Registration & Login (with password hashing)
- ✅ Admin Login with separate portal
- ✅ Student Dashboard with stats, weak topics, recommendations
- ✅ Mock Interview Module (topic + difficulty selection)
- ✅ Question Timer (30 seconds per question)
- ✅ Auto-scoring (keyword matching algorithm)
- ✅ Performance Analytics (Bar, Pie, Line charts via Chart.js)
- ✅ Weak Topic Detection (threshold: 40%)
- ✅ Personalized Recommendations
- ✅ Leaderboard with podium display
- ✅ Interview History with filters
- ✅ PDF Report Download (ReportLab)
- ✅ Admin: Question CRUD (Add/Edit/Delete/Search/Filter)
- ✅ Admin: Candidate Management
- ✅ Dark Mode Toggle (persists across sessions)
- ✅ Responsive Mobile-friendly UI
- ✅ Animated stat counters & page transitions

---

## 📝 Important SQL Queries Used

```sql
-- Leaderboard ranking
SELECT c.name, l.average_score, l.rank_position
FROM leaderboard l JOIN candidates c ON l.candidate_id = c.candidate_id
ORDER BY l.rank_position LIMIT 10;

-- Weak topics for a student
SELECT t.topic_name, ROUND(AVG(i.total_score), 2) AS avg_score
FROM interviews i JOIN topics t ON i.topic_id = t.topic_id
WHERE i.candidate_id = 1
GROUP BY t.topic_name HAVING avg_score < 40;

-- Topic-wise performance
SELECT t.topic_name, ROUND(AVG(i.total_score), 2), COUNT(i.interview_id)
FROM interviews i JOIN topics t ON i.topic_id = t.topic_id
WHERE i.candidate_id = 1 GROUP BY t.topic_name;

-- Top 5 students
SELECT c.name, l.average_score FROM leaderboard l
JOIN candidates c ON l.candidate_id = c.candidate_id
ORDER BY l.average_score DESC LIMIT 5;

-- Most attempted questions
SELECT q.question_text, COUNT(r.response_id) AS attempts
FROM responses r JOIN questions q ON r.question_id = q.question_id
GROUP BY q.question_id ORDER BY attempts DESC LIMIT 10;
```

---

## 👨‍💻 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Bootstrap 5, Chart.js |
| Backend | Python 3, Flask 3.0 |
| Database | MySQL 8.0 |
| Auth | Werkzeug (PBKDF2 hashing) |
| PDF | ReportLab |
| Icons | Bootstrap Icons |
| Fonts | Plus Jakarta Sans, JetBrains Mono |

---

*MockMentor — A DBMS Project | Built with Flask & MySQL*
