from flask import Flask, request, jsonify
import subprocess
import logging
import os
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def call_whitaker_cli(word: str) -> str:
    """Call the actual Whitaker CLI tool"""
    try:
        # Whitaker words command - built in this container
        whitaker_path = "/opt/whitakers-words/bin/words"
        whitaker_dir = "/opt/whitakers-words"  # Directory containing dictionary data files
        
        # Check if Whitaker is available
        if not os.path.exists(whitaker_path):
            return f"Error: Whitaker not found at {whitaker_path}"
        
        logger.info(f"Calling Whitaker for word: '{word}'")
        
        # Run from the whitaker directory so it can find dictionary data files
        result = subprocess.run(
            [whitaker_path, word],
            capture_output=True, 
            text=True, 
            timeout=30,
            cwd=whitaker_dir  # Set working directory to find dictionary files
        )
        
        if result.returncode == 0:
            logger.info(f"Whitaker analysis successful for '{word}'")
            return result.stdout
        else:
            logger.error(f"Whitaker failed for '{word}': {result.stderr}")
            return f"Error: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        logger.error(f"Whitaker timeout for '{word}'")
        return "Error: Analysis timed out"
    except Exception as e:
        logger.error(f"Unexpected error for '{word}': {e}")
        return f"Error: {str(e)}"

def parse_whitaker_output(output: str) -> dict:
    """Parse Whitaker's output into structured data"""
    if output.startswith("Error:"):
        return {"error": output}
    
    lines = [line.strip() for line in output.split('\n') if line.strip()]
    
    # Basic parsing - you can enhance this based on Whitaker's actual output format
    parsed_data = {
        "raw_output": output,
        "lines": lines,
        "word_forms": [],
        "definitions": []
    }
    
    # Simple heuristic parsing (adjust based on actual Whitaker output)
    for line in lines:
        if re.match(r'^\w+,\s+\w+', line):  # Likely a word form line
            parsed_data["word_forms"].append(line)
        elif line.startswith('(') or ';' in line:  # Likely definitions/notes
            parsed_data["definitions"].append(line)
    
    return parsed_data

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    # Test if Whitaker is accessible
    test_result = call_whitaker_cli("test")
    if "Error:" in test_result:
        return jsonify({
            "status": "unhealthy", 
            "service": "whitaker-server",
            "error": "Whitaker CLI not accessible"
        }), 503
    
    return jsonify({
        "status": "healthy", 
        "service": "whitaker-server",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    })

@app.route('/analyze', methods=['POST'])
def analyze_word():
    """Analyze a single Latin word"""
    data = request.get_json()
    
    if not data or 'word' not in data:
        return jsonify({"error": "No word provided in JSON body"}), 400
    
    word = data.get('word', '').strip()
    language = data.get('language', 'la')
    
    if not word:
        return jsonify({"error": "Empty word provided"}), 400
    
    if language != 'la':
        return jsonify({"error": "Only Latin (la) language is supported"}), 400
    
    output = call_whitaker_cli(word)
    parsed = parse_whitaker_output(output)
    
    response = {
        "word": word,
        "language": language,
        "analysis": parsed
    }
    
    logger.info(f"Processed analysis for '{word}'")
    return jsonify(response)

@app.route('/analyze/text', methods=['POST'])
def analyze_text():
    """Analyze a text passage"""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided in JSON body"}), 400
    
    text = data.get('text', '').strip()
    language = data.get('language', 'la')
    
    if not text:
        return jsonify({"error": "Empty text provided"}), 400
    
    if language != 'la':
        return jsonify({"error": "Only Latin (la) language is supported"}), 400
    
    # Extract Latin words (basic tokenization)
    latin_words = re.findall(r'\b[a-zA-Z]+\b', text)
    latin_words = [word.lower() for word in latin_words if len(word) > 1]
    
    # Analyze each unique word
    unique_words = list(set(latin_words))
    results = {}
    
    for word in unique_words:
        output = call_whitaker_cli(word)
        parsed = parse_whitaker_output(output)
        results[word] = parsed
    
    response = {
        "text": text,
        "language": language,
        "unique_words_analyzed": len(unique_words),
        "total_words": len(latin_words),
        "results": results
    }
    
    logger.info(f"Processed text analysis: {len(unique_words)} unique words")
    return jsonify(response)

@app.route('/analyze/batch', methods=['POST'])
def analyze_batch():
    """Analyze multiple words in batch"""
    data = request.get_json()
    
    if not data or 'words' not in data:
        return jsonify({"error": "No words array provided in JSON body"}), 400
    
    words = data.get('words', [])
    language = data.get('language', 'la')
    
    if not isinstance(words, list):
        return jsonify({"error": "Words must be provided as an array"}), 400
    
    if not words:
        return jsonify({"error": "Empty words array provided"}), 400
    
    if language != 'la':
        return jsonify({"error": "Only Latin (la) language is supported"}), 400
    
    results = {}
    
    for word in words:
        if isinstance(word, str) and word.strip():
            clean_word = word.strip().lower()
            output = call_whitaker_cli(clean_word)
            parsed = parse_whitaker_output(output)
            results[clean_word] = parsed
    
    response = {
        "batch_size": len(words),
        "words_processed": len(results),
        "language": language,
        "results": results
    }
    
    logger.info(f"Processed batch analysis: {len(results)} words")
    return jsonify(response)

@app.route('/dictionary/<word>', methods=['GET'])
def get_dictionary_entry(word):
    """Get dictionary entry for a word"""
    if not word or not word.strip():
        return jsonify({"error": "No word provided"}), 400
    
    clean_word = word.strip().lower()
    output = call_whitaker_cli(clean_word)
    parsed = parse_whitaker_output(output)
    
    response = {
        "word": clean_word,
        "entry": parsed
    }
    
    return jsonify(response)

@app.route('/info', methods=['GET'])
def get_info():
    """Get service information"""
    return jsonify({
        "service": "Whitaker HTTP Wrapper",
        "version": "1.0",
        "description": "HTTP API wrapper for Whitaker's Words Latin dictionary",
        "endpoints": {
            "health": {"method": "GET", "path": "/health"},
            "analyze_word": {"method": "POST", "path": "/analyze"},
            "analyze_text": {"method": "POST", "path": "/analyze/text"},
            "analyze_batch": {"method": "POST", "path": "/analyze/batch"},
            "dictionary": {"method": "GET", "path": "/dictionary/<word>"},
            "info": {"method": "GET", "path": "/info"}
        }
    })

if __name__ == '__main__':
    logger.info("Starting Whitaker HTTP Server...")
    app.run(host='0.0.0.0', port=9090, debug=False)