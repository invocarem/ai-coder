# app/utils/__init__.py

# Make utils a package
from .pattern_detector import PatternDetector
from .ai_provider import AIProviderFactory
from .psalm_number_converter import PsalmNumberConverter

# This allows: from app.utils import PatternDetector, AIProviderFactory