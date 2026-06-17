# wsgi.py  –  WSGI entry point for Gunicorn
#
# Gunicorn command (used by Render / Railway / Cloud Run):
#   gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --threads 2
#
# Do NOT use the Flask dev server (app.run) in production.

import os
os.environ.setdefault('FLASK_ENV', 'production')

from app import create_app
app = create_app()
