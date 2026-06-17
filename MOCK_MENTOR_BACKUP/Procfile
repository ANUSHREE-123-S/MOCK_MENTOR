# Procfile – Render & Railway read this to start the app.
# Gunicorn spawns 2 worker processes, 2 threads each.
# Adjust --workers based on your plan's RAM (1 worker ≈ 100–150 MB).
web: gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120
