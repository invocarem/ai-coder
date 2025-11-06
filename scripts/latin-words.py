# scripts/latin-words.py
import sys
import os
import json
import logging

# Configure logging to see what's happening
logging.basicConfig(level=logging.DEBUG)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.simple_whitaker_client import SimpleWhitakerClient

def test_latin_words():
    client = SimpleWhitakerClient(port=9090)
    
    # 1. Health check
    print("=== Health Check ===")
    health = client.health_check()
    print(health)
    print()
    
    # 2. Service info
    print("=== Service Info ===")
    info = client.get_service_info()
    print(json.dumps(info, indent=2))
    print()
    
    # 3. Test simple dictionary lookup
    print("=== Dictionary Lookup ===")
    dict_result = client.get_dictionary_entry("rosa")
    if dict_result:
        print(f"Dictionary result: {json.dumps(dict_result, indent=2)}")
    else:
        print("❌ Dictionary lookup failed")
    print()
    
    # 4. Test single word analysis
    print("=== Single Word Analysis ===")
    word_result = client.analyze_word("dominus")
    if word_result:
        print(f"Word analysis result keys: {list(word_result.keys())}")
        # Print just a preview to avoid huge output
        analysis = word_result.get('analysis', {})
        print(f"Raw output length: {len(analysis.get('raw_output', ''))}")
        print(f"Lines found: {len(analysis.get('lines', []))}")
    else:
        print("❌ Word analysis failed")
    print()
    
    # 5. Test text analysis
    print("=== Text Analysis ===")
    text_result = client.analyze_text("In principio erat Verbum")
    if text_result:
        print(f"Text analysis - unique words: {text_result.get('unique_words_analyzed', 0)}")
        print(f"Results keys: {list(text_result.get('results', {}).keys())}")
    else:
        print("❌ Text analysis failed")
    print()
    
    # 6. Test batch analysis
    print("=== Batch Analysis ===")
    words = ["amor", "deus", "homo", "verbum"]
    batch_result = client.batch_analyze(words)
    if batch_result:
        print(f"Batch processed: {batch_result.get('words_processed', 0)} words")
        print(f"Results: {list(batch_result.get('results', {}).keys())}")
    else:
        print("❌ Batch analysis failed")

if __name__ == "__main__":
    test_latin_words()