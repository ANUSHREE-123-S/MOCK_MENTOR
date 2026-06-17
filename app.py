# app.py  –  MockMentor Application Factory
# Supports FLASK_ENV=development (default) or FLASK_ENV=production

import os
from flask import Flask
from flask_mysqldb import MySQL
from config import config

mysql = MySQL()   # initialised without app so it can be reused in db_helper


def create_app(env: str | None = None) -> Flask:
    """
    Application factory.
    env defaults to FLASK_ENV environment variable, then 'development'.
    """
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')

    cfg = config.get(env, config['default'])

    # Validate production config (raises if SECRET_KEY is still default)
    if env == 'production' and hasattr(cfg, '_validate'):
        cfg._validate()

    app = Flask(__name__)
    app.config.from_object(cfg)

    # Ensure upload folder exists (local dev; /tmp always exists on cloud)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Bind MySQL
    mysql.init_app(app)

    # ── Blueprints ────────────────────────────────────────────
    from routes.auth_routes      import auth_bp
    from routes.student_routes   import student_bp
    from routes.interview_routes import interview_bp
    from routes.admin_routes     import admin_bp
    from routes.api_routes       import api_bp
    from routes.coding_routes    import coding_bp
    from routes.company_routes   import company_bp
    from routes.resume_routes    import resume_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(interview_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp,     url_prefix='/api')
    app.register_blueprint(coding_bp,  url_prefix='/coding')
    app.register_blueprint(company_bp, url_prefix='/company')
    app.register_blueprint(resume_bp,  url_prefix='/resume')

    return app


# ── Keep existing direct-run behaviour intact ─────────────────
# Running  python app.py  still works exactly as before.
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port,
            debug=app.config.get('DEBUG', True))
