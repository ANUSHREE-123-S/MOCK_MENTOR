# app.py - MockMentor Main Application
# Smart Placement Preparation & Interview Intelligence Platform

import os
from flask import Flask
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize MySQL properly
from models.db_helper import init_mysql
init_mysql(app)

# Ensure upload folder exists
os.makedirs(app.config.get('UPLOAD_FOLDER', 'static/uploads'), exist_ok=True)

# Original blueprints
from routes.auth_routes import auth_bp
from routes.student_routes import student_bp
from routes.interview_routes import interview_bp
from routes.admin_routes import admin_bp
from routes.api_routes import api_bp

# New upgrade blueprints
from routes.coding_routes import coding_bp
from routes.company_routes import company_bp
from routes.resume_routes import resume_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(student_bp)
app.register_blueprint(interview_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(coding_bp, url_prefix='/coding')
app.register_blueprint(company_bp, url_prefix='/company')
app.register_blueprint(resume_bp, url_prefix='/resume')

# Run server
if __name__ == '__main__':
    app.run(debug=True, port=5000)