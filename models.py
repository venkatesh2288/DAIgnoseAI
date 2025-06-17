from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to uploaded files
    uploaded_files = db.relationship('UploadedFile', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    analysis_complete = db.Column(db.Boolean, default=False)
    
    # Analysis results
    summary = db.Column(db.Text)
    risk_assessment = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    chart_data = db.Column(JSON)
    
    def __repr__(self):
        return f'<UploadedFile {self.original_filename}>'






