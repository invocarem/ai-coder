import sys
import os
import json
import logging

# Configure logging to see what's happening
logging.basicConfig(level=logging.DEBUG)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.utils.pattern_detector import PatternDetector

detector = PatternDetector()
message = """### processor: latin
### pattern: latin_analysis
### word_form: invenietur"""
result = detector.detect_pattern(message)
print(result)
