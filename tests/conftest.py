# tests/conftest.py
import pytest
import sys
import os

# Add the app directory to Python path so we can import app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def app():
    """Create a Flask app for testing"""
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()