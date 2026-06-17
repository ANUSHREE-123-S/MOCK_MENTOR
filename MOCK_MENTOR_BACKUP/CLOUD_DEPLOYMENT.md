# MockMentor – Cloud Deployment Guide
# Smart Placement Preparation & Interview Intelligence Platform
# ============================================================
# Covers: Render · Railway · GCP Cloud Run
# Pre-requisite: project already works locally with XAMPP + Flask
# ============================================================


## FILES ADDED IN THIS UPGRADE

```
mockmentor/
├── config.py          ← UPDATED  (Dev/Prod/Test config classes, env vars)
├── app.py             ← UPDATED  (app factory, reads FLASK_ENV)
├── models/db_helper.py← UPDATED  (lazy mysql import, factory-compatible)
├── wsgi.py            ← NEW      (Gunicorn WSGI entry point)
├── Procfile           ← NEW      (Render + Railway start command)
├── Dockerfile         ← NEW      (GCP Cloud Run container)
├── render.yaml        ← NEW      (Render Infrastructure-as-Code)
├── railway.toml       ← NEW      (Railway config-as-code)
├── requirements.txt   ← UPDATED  (adds gunicorn, python-dotenv)
├── .env.example       ← NEW      (copy to .env for local dev)
├── .gitignore         ← NEW      (excludes .env, uploads, pycache)
└── .dockerignore      ← NEW      (keeps Docker image small)
```

Nothing in routes/, templates/, static/, utils/ or any SQL file was changed.

---

## STEP 0 — LOCAL SETUP (do this first, works exactly as before)

```bash
# 1. Install new dependencies
pip install -r requirements.txt

# 2. Copy example env file
cp .env.example .env

# 3. Edit .env – fill in MYSQL_PASSWORD if your root has one
#    FLASK_ENV=development   (leave as-is for local)
#    SECRET_KEY=any-string   (for local dev any value is fine)

# 4. Run as always
python app.py
# → http://127.0.0.1:5000
```

Local dev is identical to before. The only visible change:
- `config.py` now reads from `.env` automatically via python-dotenv.
- `app.py` still runs with `python app.py` and still listens on port 5000.

---

## STEP 1 — PREPARE A CLOUD MYSQL DATABASE

All three platforms require an **external** MySQL database because their
containers have no local MySQL service. Choose one:

### Option A: PlanetScale (free tier, recommended)
1. Sign up at https://planetscale.com
2. Create a database named `mockmentor_db`
3. Go to **Connect** → choose **General** → copy host, user, password
4. Enable "Allow public connections"
5. In your `.env` (and the platform's env vars):
   ```
   MYSQL_HOST=aws.connect.psdb.cloud
   MYSQL_USER=your-planetscale-username
   MYSQL_PASSWORD=your-planetscale-password
   MYSQL_DB=mockmentor_db
   MYSQL_PORT=3306
   MYSQL_SSL=1
   ```
6. Import schema from your local machine:
   ```bash
   # Export from local XAMPP
   mysqldump -u root mockmentor_db > mockmentor_backup.sql

   # Import to PlanetScale via their CLI
   pscale shell mockmentor_db main < mockmentor_backup.sql
   ```

### Option B: Aiven (free tier, 1-month trial)
1. Sign up at https://aiven.io → Create MySQL service
2. Copy connection details (host, port, user, password)
3. Download the CA certificate → save as `ca.pem`
4. Set `MYSQL_SSL=1`

### Option C: Railway MySQL (add-on inside Railway)
- In Railway dashboard → Add Plugin → MySQL
- Railway automatically sets `MYSQL_URL` environment variable
- Use the connection details shown in the plugin dashboard

### Option D: FreeSQLDatabase.com (simplest free option)
1. Register at https://www.freesqldatabase.com
2. Get host/user/password/db credentials
3. Connect via phpMyAdmin link they provide → import your SQL files

---

## STEP 2 — GENERATE A SECURE SECRET KEY

```bash
python -c "import secrets; print(secrets.token_hex(32))"
# Example output: 4f2a8c1e9d3b7f6a2c5e8b1d4a7f0c3e...
# Copy this value → set as SECRET_KEY in your platform's env vars
```

---

## PLATFORM A — RENDER (easiest, free tier available)
## =====================================================

### What Render does
- Reads `Procfile` to start: `gunicorn wsgi:app ...`
- Reads `requirements.txt` to install packages
- Free tier: 512 MB RAM, sleeps after 15 min inactivity, spins up in ~30s

### Deployment Steps

**Step 1 — Push to GitHub**
```bash
git init
git add .
git commit -m "Add cloud deployment support"
git branch -M main
git remote add origin https://github.com/your-username/mockmentor.git
git push -u origin main
```
> Make sure `.env` is in `.gitignore` — never push secrets to GitHub.

**Step 2 — Create Web Service on Render**
1. Go to https://dashboard.render.com → **New** → **Web Service**
2. Connect your GitHub account → select the `mockmentor` repo
3. Fill in:
   - **Name:** mockmentor
   - **Region:** Singapore (closest for India)
   - **Branch:** main
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120`
   - **Plan:** Free

**Step 3 — Add Environment Variables**

In Render dashboard → your service → **Environment** tab, add:

| Key              | Value                                    |
|------------------|------------------------------------------|
| FLASK_ENV        | production                               |
| SECRET_KEY       | (paste the 64-char hex you generated)    |
| MYSQL_HOST       | (your PlanetScale / Aiven host)          |
| MYSQL_USER       | (your db username)                       |
| MYSQL_PASSWORD   | (your db password)                       |
| MYSQL_DB         | mockmentor_db                            |
| MYSQL_PORT       | 3306                                     |
| MYSQL_SSL        | 1                                        |
| UPLOAD_FOLDER    | /tmp/mockmentor_uploads                  |

**Step 4 — Deploy**
- Click **Create Web Service**
- Watch the build logs — takes 3–5 minutes
- Your app is live at: `https://mockmentor.onrender.com`

**Step 5 — Verify**
```bash
curl https://mockmentor.onrender.com/
# Should return the landing page HTML
```

### Render Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: MySQLdb` | mysqlclient not installed | Check build logs; ensure requirements.txt has `mysqlclient==2.2.4` |
| `RuntimeError: SECRET_KEY not set` | Missing env var | Add SECRET_KEY in Render dashboard → Environment |
| `OperationalError: Can't connect to MySQL` | Wrong MYSQL_HOST | Double-check host/user/password; enable SSL if using PlanetScale |
| App sleeps (free tier) | Render free tier spins down | Upgrade to Starter ($7/mo) or use UptimeRobot to ping every 14 min |
| `gunicorn: command not found` | gunicorn missing | Confirm `gunicorn==22.0.0` is in requirements.txt |

---

## PLATFORM B — RAILWAY (simplest deployment, $5 free credits/month)
## ==================================================================

### What Railway does
- Detects Python from your repo → reads `railway.toml`
- Reads `requirements.txt` automatically via Nixpacks
- Starts with command in `railway.toml`
- Free: $5 credit per month (enough for ~500 hours on Hobby plan)

### Deployment Steps

**Step 1 — Install Railway CLI**
```bash
npm install -g @railway/cli
# OR on macOS:
brew install railway
```

**Step 2 — Login and Init**
```bash
railway login
# Browser opens → authenticate with GitHub
```

**Step 3 — Create Project and Deploy**
```bash
cd mockmentor/

# Create a new Railway project
railway init
# → Select: Create New Project
# → Name: mockmentor

# Deploy from current directory
railway up
# Railway detects Python, installs requirements, runs gunicorn from railway.toml
```

**Step 4 — Add Environment Variables**

Option A — Railway CLI:
```bash
railway variables set FLASK_ENV=production
railway variables set SECRET_KEY=your-64-char-hex-key
railway variables set MYSQL_HOST=your-db-host
railway variables set MYSQL_USER=your-db-user
railway variables set MYSQL_PASSWORD=your-db-password
railway variables set MYSQL_DB=mockmentor_db
railway variables set MYSQL_PORT=3306
railway variables set MYSQL_SSL=1
railway variables set UPLOAD_FOLDER=/tmp/mockmentor_uploads
```

Option B — Railway Dashboard:
1. Go to https://railway.app → your project
2. Click your service → **Variables** tab
3. Add each key-value pair from the table above

**Step 5 — Add MySQL Plugin (optional — instead of external DB)**
```bash
# Inside Railway dashboard:
# + New → Database → MySQL
# Railway auto-injects MYSQL_URL, MYSQLHOST, MYSQLUSER, MYSQLPASSWORD, MYSQLDATABASE
# Copy those values → set in your service's env vars using the MYSQL_* names
```

**Step 6 — Get Your URL**
```bash
railway status
# Shows: https://mockmentor-production.up.railway.app
```

**Step 7 — Open in Browser**
```bash
railway open
```

### Railway Troubleshooting

| Error | Fix |
|-------|-----|
| `No start command found` | Ensure `railway.toml` exists and `startCommand` is set |
| `ModuleNotFoundError: dotenv` | `python-dotenv==1.0.1` must be in requirements.txt |
| `Connection refused` on MySQL | Check MYSQL_HOST / MYSQL_PASSWORD; set MYSQL_SSL=1 |
| Build fails on mysqlclient | Railway's Nixpacks includes libmysqlclient; should auto-resolve |
| `$PORT not bound` | Railway sets PORT automatically; gunicorn bind uses it via `$PORT` |

---

## PLATFORM C — GCP CLOUD RUN (enterprise-grade, always-on free tier)
## ====================================================================

### Why Cloud Run
- Serverless containers — pay only when requests arrive
- Always-on free tier: 2 million requests/month, 360,000 GB-seconds
- Auto-scales to zero, scales up instantly
- Uses the `Dockerfile` included in this upgrade

### Prerequisites
```bash
# Install Google Cloud SDK
# macOS:
brew install google-cloud-sdk
# Windows/Linux:
# https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login
gcloud auth configure-docker

# Set your project
gcloud config set project YOUR_GCP_PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com
```

### MySQL on GCP — Cloud SQL

**Create a Cloud SQL MySQL instance:**
```bash
gcloud sql instances create mockmentor-db \
  --database-version=MYSQL_8_0 \
  --tier=db-f1-micro \
  --region=asia-south1 \
  --root-password=your-root-password
```

**Create the database:**
```bash
gcloud sql databases create mockmentor_db \
  --instance=mockmentor-db
```

**Import your schema:**
```bash
# Export from local XAMPP first
mysqldump -u root mockmentor_db > mockmentor_backup.sql

# Upload to GCS bucket
gsutil cp mockmentor_backup.sql gs://your-bucket/mockmentor_backup.sql

# Import to Cloud SQL
gcloud sql import sql mockmentor-db \
  gs://your-bucket/mockmentor_backup.sql \
  --database=mockmentor_db
```

**Get the Cloud SQL connection name:**
```bash
gcloud sql instances describe mockmentor-db \
  --format="value(connectionName)"
# Output: your-project:asia-south1:mockmentor-db
# Save this — you need it below
```

### Deploy to Cloud Run

**Step 1 — Build and push the Docker image:**
```bash
# Using Cloud Build (no local Docker needed)
gcloud builds submit \
  --tag asia.gcr.io/YOUR_PROJECT_ID/mockmentor \
  --timeout=10m

# OR build locally and push:
docker build -t asia.gcr.io/YOUR_PROJECT_ID/mockmentor .
docker push asia.gcr.io/YOUR_PROJECT_ID/mockmentor
```

**Step 2 — Create a Secret for SECRET_KEY:**
```bash
# Generate key
python -c "import secrets; print(secrets.token_hex(32))" > /tmp/secret_key.txt

# Store in Secret Manager
gcloud secrets create mockmentor-secret-key \
  --data-file=/tmp/secret_key.txt

# Store DB password
echo -n "your-db-password" | \
  gcloud secrets create mockmentor-db-password --data-file=-

rm /tmp/secret_key.txt
```

**Step 3 — Deploy to Cloud Run:**
```bash
gcloud run deploy mockmentor \
  --image asia.gcr.io/YOUR_PROJECT_ID/mockmentor \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --add-cloudsql-instances YOUR_PROJECT:asia-south1:mockmentor-db \
  --set-env-vars "FLASK_ENV=production" \
  --set-env-vars "MYSQL_HOST=127.0.0.1" \
  --set-env-vars "MYSQL_USER=root" \
  --set-env-vars "MYSQL_DB=mockmentor_db" \
  --set-env-vars "MYSQL_PORT=3306" \
  --set-env-vars "UPLOAD_FOLDER=/tmp/mockmentor_uploads" \
  --set-secrets "SECRET_KEY=mockmentor-secret-key:latest" \
  --set-secrets "MYSQL_PASSWORD=mockmentor-db-password:latest"
```

**Step 4 — Get the URL:**
```bash
gcloud run services describe mockmentor \
  --region asia-south1 \
  --format="value(status.url)"
# Output: https://mockmentor-abc123-as.a.run.app
```

**Step 5 — Verify:**
```bash
curl $(gcloud run services describe mockmentor \
       --region asia-south1 \
       --format="value(status.url)")
```

### GCP Cloud Run Troubleshooting

| Error | Fix |
|-------|-----|
| `Container failed to start` | Check logs: `gcloud run services logs read mockmentor` |
| `Port 8080 not listening` | Ensure Dockerfile CMD uses `--bind 0.0.0.0:${PORT}` |
| MySQL connection refused | Cloud SQL proxy connection — verify `--add-cloudsql-instances` flag |
| `Permission denied` on /tmp | Already handled — Dockerfile sets UPLOAD_FOLDER=/tmp/mockmentor_uploads |
| Image push fails | Run `gcloud auth configure-docker` first |
| Slow cold start | Set `--min-instances 1` (costs ~$10/month but eliminates cold start) |

---

## ENVIRONMENT VARIABLES REFERENCE

| Variable          | Required | Default (local)              | Description                              |
|-------------------|----------|------------------------------|------------------------------------------|
| `FLASK_ENV`       | Yes      | development                  | `development` or `production`            |
| `SECRET_KEY`      | Yes      | insecure dev key             | Random 64-char hex string                |
| `MYSQL_HOST`      | Yes      | localhost                    | Database server hostname                 |
| `MYSQL_USER`      | Yes      | root                         | Database username                        |
| `MYSQL_PASSWORD`  | Yes      | (empty)                      | Database password                        |
| `MYSQL_DB`        | Yes      | mockmentor_db                | Database name                            |
| `MYSQL_PORT`      | No       | 3306                         | Database port                            |
| `MYSQL_SSL`       | No       | (unset)                      | Set to `1` for managed cloud databases   |
| `UPLOAD_FOLDER`   | No       | static/uploads (dev) /tmp (prod) | Resume upload directory             |
| `PORT`            | No       | 5000                         | HTTP port (set automatically by platform)|

---

## SECURITY CHECKLIST FOR PRODUCTION

- [ ] `SECRET_KEY` is a random 64-char hex string (not the dev default)
- [ ] `.env` file is in `.gitignore` and NOT pushed to GitHub
- [ ] `FLASK_ENV=production` is set (disables debug mode, enables secure cookies)
- [ ] `MYSQL_SSL=1` is set for managed cloud databases
- [ ] `UPLOAD_FOLDER=/tmp/...` (ephemeral container storage, not the repo)
- [ ] `DEBUG=False` in production (confirmed by `ProductionConfig`)
- [ ] `SESSION_COOKIE_SECURE=True` (cookies only sent over HTTPS)
- [ ] Database password is stored as a platform secret (not in source code)
- [ ] `.dockerignore` excludes `.env`, `.git`, and `static/uploads/`

---

## RESUME UPLOADS IN PRODUCTION

Container filesystems are **ephemeral** — files in `/tmp` are lost when the
container restarts. For persistent resume storage in production:

### Option 1: AWS S3 (any platform)
```bash
pip install boto3
```
```python
# In resume_routes.py, replace file.save(filepath) with:
import boto3, os
s3 = boto3.client('s3',
    aws_access_key_id=os.environ['AWS_KEY'],
    aws_secret_access_key=os.environ['AWS_SECRET'])
s3.upload_fileobj(file, 'your-bucket', filename)
```

### Option 2: GCP Cloud Storage (on Cloud Run)
```bash
pip install google-cloud-storage
```
```python
from google.cloud import storage
client = storage.Client()
bucket = client.bucket('your-bucket')
blob   = bucket.blob(filename)
blob.upload_from_file(file)
```

### Option 3: Accept ephemeral uploads (simplest)
- For a demo/academic platform, losing uploads on container restart is acceptable.
- `UPLOAD_FOLDER=/tmp/mockmentor_uploads` (already set in ProductionConfig).
- Resume text is stored in MySQL (`resumes.raw_text`) so analysis persists.
- Only the PDF file itself is lost — all skill extraction results survive in DB.

---

## QUICK REFERENCE — DEPLOY COMMANDS

```bash
# ── Render ────────────────────────────────────────────────────
git push origin main          # Auto-deploys via GitHub integration

# ── Railway ───────────────────────────────────────────────────
railway up                    # Deploy from current directory

# ── GCP Cloud Run ─────────────────────────────────────────────
gcloud builds submit --tag asia.gcr.io/PROJECT/mockmentor
gcloud run deploy mockmentor --image asia.gcr.io/PROJECT/mockmentor \
  --region asia-south1 --allow-unauthenticated
```

---

## PLATFORM COMPARISON

| Feature              | Render (Free)       | Railway ($5/mo)    | GCP Cloud Run        |
|----------------------|---------------------|--------------------|----------------------|
| Free tier            | Yes (sleeps 15 min) | $5 credit/month    | 2M req/month free    |
| Cold start           | ~30 seconds         | ~5 seconds         | ~2 seconds           |
| MySQL included       | No (external)       | Yes (add-on)       | Yes (Cloud SQL)      |
| Custom domain        | Yes (free SSL)      | Yes (free SSL)     | Yes (free SSL)       |
| Auto-deploy from Git | Yes                 | Yes                | Via Cloud Build      |
| Best for             | Academic demo       | Small production   | Scalable production  |
| India region         | Singapore           | US-West            | asia-south1 (Mumbai) |

**Recommendation for academic demo:** Render (free, easiest setup)
**Recommendation for live platform:** Railway or GCP Cloud Run

---

## KEEP LOCAL DEVELOPMENT WORKING

After this upgrade, local development is unchanged:

```bash
# Same as always
python app.py
# → http://127.0.0.1:5000  (reads .env automatically)
```

The only difference: `config.py` now loads `.env` via python-dotenv, so
you no longer need to hardcode credentials directly in the Python file.
