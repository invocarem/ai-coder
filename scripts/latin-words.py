# latin-words.py
import requests
import re
from bs4 import BeautifulSoup

def get_latin_word_simple(word):
    """Try the simple GET approach that works in browsers"""
    url = "https://archives.nd.edu/cgi-bin/wordz.pl"
    
    # Try GET request like a browser would
    params = {
        'keyword': word,
        'english': '1'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"🔍 Making GET request for: {word}")
        response = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"📄 Status: {response.status_code}, Length: {len(response.text)}")
        
        if response.status_code == 200 and len(response.text) > 100:
            # Save for inspection
            with open(f"get_response_{word}.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            
            return parse_response(response.text, word)
        else:
            print(f"❌ Invalid response: status {response.status_code}, length {len(response.text)}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    return None

def parse_response(html, word):
    """Parse the HTML response"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove scripts and styles
    for script in soup(["script", "style"]):
        script.decompose()
    
    text = soup.get_text()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    print(f"📖 Found {len(lines)} lines of text")
    
    # Print the first 10 lines to see what we're working with
    for i, line in enumerate(lines[:10]):
        print(f"  {i}: {line[:100]}...")
    
    # Look for the dictionary entry patterns
    full_text = "\n".join(lines)
    
    # Verb pattern
    verb_match = re.search(r'(\w+),\s*(\w+),\s*(\w+),\s*(\w+)\s+V\s*\((\d)', full_text)
    if verb_match:
        print("🎯 Found verb pattern!")
        lemma, infinitive, perfect, supine, conjugation = verb_match.groups()
        
        return {
            "lemma": lemma,
            "part_of_speech": "verb",
            "conjugation": int(conjugation),
            "infinitive": infinitive,
            "present": lemma,
            "future": generate_future(infinitive, int(conjugation)),
            "perfect": perfect,
            "supine": supine,
            "forms": {
                "imperative": generate_imperative(lemma, int(conjugation))
            },
            "translations": {
                "en": f"to {infinitive}",
                "la": f"{lemma}, {infinitive}, {perfect}, {supine}"
            }
        }
    
    # Noun pattern
    noun_match = re.search(r'(\w+),\s*(\w+)\s+N\s*\[(\d)', full_text)
    if noun_match:
        print("🎯 Found noun pattern!")
        lemma, genitive, declension = noun_match.groups()
        
        return {
            "lemma": lemma,
            "part_of_speech": "noun", 
            "declension": int(declension),
            "genitive": genitive,
            "translations": {
                "en": lemma,
                "la": f"{lemma}, {genitive}"
            }
        }
    
    print("❌ No dictionary patterns found in response")
    return None

def generate_future(infinitive, conjugation):
    stem = infinitive[:-2]
    if conjugation == 1: return stem + "bo"
    elif conjugation == 2: return stem + "bo"
    elif conjugation == 3: return stem[:-1] + "am"
    elif conjugation == 4: return stem + "am"
    return stem + "bo"

def generate_imperative(lemma, conjugation):
    if conjugation == 1:
        stem = lemma[:-1]
        return [stem + 'a', stem + 'ate']
    elif conjugation == 2:
        stem = lemma[:-2]
        return [stem + 'e', stem + 'ete']
    elif conjugation == 3:
        stem = lemma[:-1]
        return [stem + 'e', stem + 'ite']
    elif conjugation == 4:
        stem = lemma[:-1]
        return [stem + 'i', stem + 'ite']
    return []

# Test it
test_words = ["amo", "rosa"]

for word in test_words:
    print(f"\n{'='*50}")
    print(f"Testing: {word}")
    print(f"{'='*50}")
    result = get_latin_word_simple(word)
    if result:
        print("✅ SUCCESS!")
        for key, value in result.items():
            print(f"   {key}: {value}")
    else:
        print("❌ Failed to get result")