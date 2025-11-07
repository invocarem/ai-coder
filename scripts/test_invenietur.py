# app/processors/test_invenietur.py
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

TARGET_WORD = "invenietur"
EXPECTED_LEMMA = "INVENIO"
EXPECTED_CONJUGATION = "4"


def extract_lemma_and_conjugation(analysis: dict) -> Tuple[Optional[str], Optional[str]]:
    """Attempt to extract lemma and conjugation data from Whitaker analysis output."""
    raw_output = analysis.get("raw_output", "") if analysis else ""
    if not raw_output:
        logger.warning("No raw_output present in analysis payload")
        return None, None

    # Lemma line is usually the first line with principal parts: LEMMA, -re, -vi, -tus
    lemma_match = re.search(r"^([A-Z][A-Z\-]+),", raw_output, re.MULTILINE)
    lemma = lemma_match.group(1) if lemma_match else None

    # Conjugation information tends to appear on a line starting with 'V <number>'
    conj_match = re.search(r"^V\s+(\d)", raw_output, re.MULTILINE)
    conjugation = conj_match.group(1) if conj_match else None

    return lemma, conjugation


def test_invenietur():
    logger.info("=== Whitaker Lemma/Conjugation Test ===")

    client = SimpleWhitakerClient(port=9090)

    logger.info("Requesting analysis for '%s'", TARGET_WORD)
    response = client.analyze_word(TARGET_WORD)
    if not response:
        logger.error("❌ Failed to retrieve analysis for '%s'", TARGET_WORD)
        return False

    analysis = response.get("analysis", {})
    logger.debug("Full analysis payload: %s", json.dumps(analysis, indent=2))

    lemma, conjugation = extract_lemma_and_conjugation(analysis)
    logger.info("Extracted lemma: %s", lemma)
    logger.info("Extracted conjugation: %s", conjugation)

    if lemma != EXPECTED_LEMMA:
        logger.error("❌ Lemma mismatch: expected '%s', got '%s'", EXPECTED_LEMMA, lemma)
        return False

    if conjugation != EXPECTED_CONJUGATION:
        logger.error(
            "❌ Conjugation mismatch: expected '%s', got '%s'",
            EXPECTED_CONJUGATION,
            conjugation,
        )
        return False

    logger.info("✅ Lemma and conjugation match expected values!")
    return True


if __name__ == "__main__":
    success = test_invenietur()
    if not success:
        sys.exit(1)
