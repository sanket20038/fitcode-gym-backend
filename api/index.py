import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.main import app
if __name__ == '__main__':
    # Run the Flask app
    app.run()