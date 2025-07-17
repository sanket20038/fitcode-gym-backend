# api/index.py

import os
import sys

# Add the root directory to sys.path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import your Flask app from main.py
from src.main import app

# Vercel-compatible WSGI handler
def handler(environ, start_response):
    return app.wsgi_app(environ, start_response)
