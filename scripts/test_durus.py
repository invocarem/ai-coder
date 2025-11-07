# scripts/test_durus.py
import sys
import os
import json
import re
import logging
from typing import Optional, Tuple

# Configure logging similar to scripts/latin-words.py so we can see what's happening
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ensure the repository root is on the import path (mirrors scripts/latin-words.py setup)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from app.rag.simple_whitaker_client import SimpleWhitakerClient
from app.utils.whitaker_output_parser import WhitakerOutputParser, EnhancedWhitakerClient

TARGET_WORD = "durus"
EXPECTED_LEMMA = "durus"
EXPECTED_DECLENSION = 1
EXPECTED_GENDER = "masculine"

def test_durus_basic():
    logger.info("=== Whitaker Basic Test for 'durus' ===")

    client = SimpleWhitakerClient(port=9090)

    logger.info("Requesting analysis for '%s'", TARGET_WORD)
    response = client.analyze_word(TARGET_WORD)
    if not response:
        logger.error("❌ Failed to retrieve analysis for '%s'", TARGET_WORD)
        return False

    analysis = response.get("analysis", {})
    logger.debug("Full analysis payload: %s", json.dumps(analysis, indent=2))

    # Test lemma extraction
    raw_output = analysis.get("raw_output", "")
    lemma_match = re.search(r"^([a-z]+),", raw_output, re.MULTILINE)
    lemma = lemma_match.group(1).lower() if lemma_match else None

    if lemma != EXPECTED_LEMMA:
        logger.error("❌ Lemma mismatch: expected '%s', got '%s'",
                     EXPECTED_LEMMA, lemma)
        return False

    logger.info("✅ Basic test passed - lemma matches expected value!")
    return True

def test_durus_structured():
    logger.info("=== Whitaker Structured Test for 'durus' ===")

    client = EnhancedWhitakerClient(port=9090)

    logger.info("Requesting structured analysis for '%s'", TARGET_WORD)
    structured_result = client.analyze_word_structured(TARGET_WORD)
    
    if not structured_result:
        logger.error("❌ Failed to generate structured analysis for '%s'", TARGET_WORD)
        return False

    logger.info("Structured analysis result:")
    logger.info(json.dumps(structured_result, indent=2, ensure_ascii=False))
    
    # Validate key fields for adjective
    expected_fields = ["lemma", "part_of_speech", "declension", "gender", "nominative", "translations"]
    missing_fields = [field for field in expected_fields if field not in structured_result]
    
    if missing_fields:
        logger.error("❌ Missing expected fields: %s", missing_fields)
        return False
    
    # Test specific values
    tests_passed = True
    
    if structured_result["lemma"] != EXPECTED_LEMMA:
        logger.error("❌ Lemma mismatch: expected '%s', got '%s'",
                     EXPECTED_LEMMA, structured_result["lemma"])
        tests_passed = False
    
    if structured_result["declension"] != EXPECTED_DECLENSION:
        logger.error("❌ Declension mismatch: expected %s, got %s",
                     EXPECTED_DECLENSION, structured_result["declension"])
        tests_passed = False
        
    if structured_result.get("gender") != EXPECTED_GENDER:
        logger.error("❌ Gender mismatch: expected '%s', got '%s'",
                     EXPECTED_GENDER, structured_result.get("gender"))
        tests_passed = False
    
    if structured_result["part_of_speech"] != "adjective":
        logger.error("❌ Part of speech mismatch: expected 'adjective', got '%s'",
                     structured_result["part_of_speech"])
        tests_passed = False

    if tests_passed:
        logger.info("✅ All structured tests passed!")
    else:
        logger.error("❌ Some structured tests failed")
        
    return tests_passed

if __name__ == "__main__":
    success_basic = test_durus_basic()
    success_structured = test_durus_structured()
    
    if not (success_basic and success_structured):
        sys.exit(1)