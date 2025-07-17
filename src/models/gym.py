from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Gym(db.Model):
    __tablename__ = 'gyms'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('gym_owners.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    logo_url = db.Column(db.String(255), nullable=True)
    contact_info = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = db.relationship('GymOwner', backref='gym')
    machines = db.relationship('GymMachine', backref='gym', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'name': self.name,
            'logo_url': self.logo_url,
            'contact_info': self.contact_info,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class GymOwner(db.Model):
    __tablename__ = 'gym_owners'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class GymClient(db.Model):
    __tablename__ = 'gym_clients'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    scan_history = db.relationship('ScanHistory', backref='client', cascade='all, delete-orphan')
    bookmarks = db.relationship('BookmarkedMachine', backref='client', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class GymMachine(db.Model):
    __tablename__ = 'gym_machines'
    
    id = db.Column(db.Integer, primary_key=True)
    gym_id = db.Column(db.Integer, db.ForeignKey('gyms.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    how_to_use_video_url = db.Column(db.String(255), nullable=True)
    local_video_path = db.Column(db.String(255), nullable=True) # New field for local video files
    safety_tips = db.Column(db.Text, nullable=True)
    usage_guide = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    qr_code = db.relationship('QRCode', backref='machine', uselist=False, cascade='all, delete-orphan')
    multilingual_content = db.relationship('MultilingualContent', backref='machine', cascade='all, delete-orphan')
    scan_history = db.relationship('ScanHistory', backref='machine', cascade='all, delete-orphan')
    bookmarks = db.relationship('BookmarkedMachine', backref='machine', cascade='all, delete-orphan')
    
    def to_dict(self):
        # Adjust local_video_path to remove 'static/' prefix if present
        local_video_path = self.local_video_path
        if local_video_path and local_video_path.startswith('static/'):
            local_video_path = local_video_path[len('static/'):]

        return {
            'id': self.id,
            'gym_id': self.gym_id,
            'name': self.name,
            'how_to_use_video_url': self.how_to_use_video_url,
            'local_video_path': local_video_path,
            'safety_tips': self.safety_tips,
            'usage_guide': self.usage_guide,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class QRCode(db.Model):
    __tablename__ = 'qr_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('gym_machines.id'), nullable=False)
    qr_code_data = db.Column(db.Text, nullable=False)  # Encrypted data
    token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'machine_id': self.machine_id,
            'token': self.token,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class MultilingualContent(db.Model):
    __tablename__ = 'multilingual_content'
    
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('gym_machines.id'), nullable=False)
    language_code = db.Column(db.String(10), nullable=False)  # e.g., 'en', 'es', 'fr'
    instruction_text = db.Column(db.Text, nullable=True)
    safety_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'machine_id': self.machine_id,
            'language_code': self.language_code,
            'instruction_text': self.instruction_text,
            'safety_text': self.safety_text,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ScanHistory(db.Model):
    __tablename__ = 'scan_history'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('gym_clients.id'), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey('gym_machines.id'), nullable=False)
    scan_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'machine_id': self.machine_id,
            'scan_timestamp': self.scan_timestamp.isoformat() if self.scan_timestamp else None
        }

class BookmarkedMachine(db.Model):
    __tablename__ = 'bookmarked_machines'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('gym_clients.id'), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey('gym_machines.id'), nullable=False)
    bookmark_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate bookmarks
    __table_args__ = (db.UniqueConstraint('client_id', 'machine_id', name='unique_client_machine_bookmark'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'machine_id': self.machine_id,
            'bookmark_timestamp': self.bookmark_timestamp.isoformat() if self.bookmark_timestamp else None
        }

