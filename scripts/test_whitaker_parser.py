import sys
import os
import json
import re
import logging

from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)
 
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from app.rag.simple_whitaker_client import SimpleWhitakerClient
from app.utils.whitaker_output_parser import WhitakerOutputParser, EnhancedWhitakerClient



# Update your test to use the enhanced client
def test_invenietur_structured():
    """Test the structured output for 'invenietur'."""
    logger.info("=== Whitaker Structured Output Test ===")

    client = EnhancedWhitakerClient(port=9090)

    logger.info("Requesting structured analysis for '%s'", TARGET_WORD)
    structured_result = client.analyze_word_structured(TARGET_WORD)
    
    if not structured_result:
        logger.error("❌ Failed to generate structured analysis for '%s'", TARGET_WORD)
        return False

    logger.info("Structured analysis result:")
    logger.info(json.dumps(structured_result, indent=2, ensure_ascii=False))
    
    # Validate key fields
    expected_fields = ["lemma", "part_of_speech", "conjugation", "infinitive", "perfect", "supine", "translations"]
    for field in expected_fields:
        if field not in structured_result:
            logger.error("❌ Missing expected field: %s", field)
            return False
    
    if structured_result["lemma"] != EXPECTED_LEMMA:
        logger.error("❌ Lemma mismatch in structured output")
        return False
        
    if structured_result["conjugation"] != int(EXPECTED_CONJUGATION):
        logger.error("❌ Conjugation mismatch in structured output")
        return False

    logger.info("✅ Structured analysis generated successfully!")
    return True


if __name__ == "__main__":
    # Test the enhanced client
    logging.basicConfig(level=logging.INFO)
    
    client = EnhancedWhitakerClient(port=9090)
    
    # Test with various words
    test_words = ["invenietur", "adeps", "durus", "prolongo", "concipio", "concido"]
    
    for word in test_words:
        print(f"\n=== Testing '{word}' ===")
        result = client.analyze_word_structured(word)
        if result:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Failed to analyze '{word}'")