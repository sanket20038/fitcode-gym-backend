import os
import sys


# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.gym import db
from src.routes.auth import auth_bp
from src.routes.gym_management import gym_bp
from src.routes.qr_management import qr_bp
from src.routes.client_features import client_bp
from src.routes.analytics import analytics_bp
from src.routes.translation_proxy import translation_proxy_bp
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
# app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')


# Enable CORS for all routes
CORS(app, origins="*")

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(gym_bp, url_prefix='/api')
app.register_blueprint(qr_bp, url_prefix='/api')
app.register_blueprint(client_bp, url_prefix='/api/client')
app.register_blueprint(analytics_bp, url_prefix='/api')
app.register_blueprint(translation_proxy_bp, url_prefix='/api/translation')

# Database configuration
# app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
# Supabase PostgreSQL connection
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///database/app.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# with app.app_context():
#     db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

@app.route('/api/health', methods=['GET'])
def health_check():
    return {'status': 'healthy', 'message': 'Gym Platform API is running'}, 200

@app.route('/videos/<path:filename>')
def serve_video(filename):
    video_folder = os.path.join(app.static_folder, 'videos')
    return send_from_directory(video_folder, filename)

@app.route('/api/uploads/<path:filename>')
def serve_upload(filename):
    upload_folder = os.path.join(os.path.dirname(__file__), 'uploads')
    return send_from_directory(upload_folder, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
