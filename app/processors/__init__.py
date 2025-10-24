# app/processors/__init__.py

# This makes the processors directory a Python package
# You can leave it empty, or add imports for convenience

# Optional: Make specific classes easily importable
from .code_processor import CodeProcessor

# This allows: from app.processors import CodeProcessor
# Instead of: from app.processors.code_processor import CodeProcessor