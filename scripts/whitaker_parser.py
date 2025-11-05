# whitaker_parser.py

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Dict, List, Optional

class WhitakerParser:
    def __init__(self):
        self.base_url = "https://archives.nd.edu/cgi-bin/wordz.pl"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def query_whitaker(self, word: str) -> Optional[str]:
        """Query Whitaker's Words online for a Latin word"""
        try:
            params = {'keyword': word, 'english': 'Search'}
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"❌ Error querying Whitaker for '{word}': {e}")
            return None
    
    def parse_whitaker_output(self, html_content: str, original_word: str) -> Optional[Dict]:
        """Parse Whitaker's HTML output into structured JSON"""
        if not html_content:
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        pre_tags = soup.find_all('pre')
        
        if not pre_tags:
            return None
        
        # Get the main content from the first pre tag
        content = pre_tags[0].get_text()
        lines = content.split('\n')
        
        result = {
            "original_input": original_word,
            "lemma": "",
            "part_of_speech": "",
            "conjugation": None,
            "declension": None,
            "infinitive": "",
            "present": "",
            "future": "",
            "perfect": "",
            "supine": "",
            "forms": {},
            "translations": {"en": "", "la": ""},
            "raw_output": content[:1000]  # Keep some raw data for debugging
        }
        
        # Parse the main dictionary entry line
        for line in lines:
            line = line.strip()
            
            # Look for verb entries
            if re.search(r'V\s*\(\d', line):
                return self._parse_verb_entry(lines, result, original_word)
            
            # Look for noun entries
            elif re.search(r'N\s*\[\d', line) or re.search(r'NOUN', line):
                return self._parse_noun_entry(lines, result, original_word)
            
            # Look for adjective entries
            elif re.search(r'ADJ', line) or re.search(r'A\s*\[\d', line):
                return self._parse_adjective_entry(lines, result, original_word)
        
        return None
    
    def _parse_verb_entry(self, lines: List[str], result: Dict, original_word: str) -> Dict:
        """Parse verb-specific data"""
        result["part_of_speech"] = "verb"
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Parse main verb line like: "buccino, buccinare, buccinavi, buccinatus  V (1st)"
            verb_match = re.search(r'^(\w+),\s*(\w+),\s*(\w+),\s*(\w+)\s+V\s*\((\d)', line)
            if verb_match:
                result["lemma"] = verb_match.group(1)
                result["infinitive"] = verb_match.group(2)
                result["perfect"] = verb_match.group(3)
                result["supine"] = verb_match.group(4)
                result["conjugation"] = int(verb_match.group(5))
                result["present"] = verb_match.group(1)
                
                # Generate future tense (simplified)
                stem = result["infinitive"][:-2]  # Remove 're'
                if result["conjugation"] == 1:
                    result["future"] = stem + "bo"
                elif result["conjugation"] == 2:
                    result["future"] = stem + "bo"
                elif result["conjugation"] == 3:
                    result["future"] = stem[:-1] + "am"  # Remove last char and add 'am'
                elif result["conjugation"] == 4:
                    result["future"] = stem + "am"
                
                # Build Latin translation
                result["translations"]["la"] = f"{result['lemma']}, {result['infinitive']}, {result['perfect']}, {result['supine']}"
            
            # Parse forms
            form_match = re.match(r'^(\w+\.?\w*)\s+([A-Z]+)\s+.*', line)
            if form_match:
                form = form_match.group(1).replace('.', '')  # Remove dots
                pos_code = form_match.group(2)
                
                if 'IMPERATIVE' in line or 'IMP' in pos_code:
                    if '2 P' in line:  # 2nd person plural
                        if 'forms' not in result:
                            result['forms'] = {}
                        if 'imperative' not in result['forms']:
                            result['forms']['imperative'] = []
                        if form not in result['forms']['imperative']:
                            result['forms']['imperative'].append(form)
            
            # Parse English translation
            if ';' in line and not re.search(r'[A-Z]+\s*\[', line):
                trans = line.split(';')[0].strip()
                if trans and len(trans) > 10:  # Reasonable length for translation
                    result["translations"]["en"] = trans
        
        return result
    
    def _parse_noun_entry(self, lines: List[str], result: Dict, original_word: str) -> Dict:
        """Parse noun-specific data"""
        result["part_of_speech"] = "noun"
        
        for line in lines:
            line = line.strip()
            
            # Parse main noun line like: "rosa, rosae N (1st) F"
            noun_match = re.search(r'^(\w+),\s*(\w+)\s+[AN]\s*\[?(\d)', line)
            if noun_match:
                result["lemma"] = noun_match.group(1)
                result["genitive"] = noun_match.group(2)
                result["declension"] = int(noun_match.group(3))
                result["translations"]["la"] = f"{result['lemma']}, {result['genitive']}"
            
            # Parse gender
            if 'F' in line:
                result["gender"] = "feminine"
            elif 'M' in line:
                result["gender"] = "masculine"
            elif 'N' in line:
                result["gender"] = "neuter"
            
            # Parse English translation
            if ';' in line and not re.search(r'[A-Z]+\s*\[', line):
                trans = line.split(';')[0].strip()
                if trans and len(trans) > 5:
                    result["translations"]["en"] = trans
        
        return result
    
    def _parse_adjective_entry(self, lines: List[str], result: Dict, original_word: str) -> Dict:
        """Parse adjective-specific data"""
        result["part_of_speech"] = "adjective"
        
        for line in lines:
            line = line.strip()
            
            # Parse main adjective line
            adj_match = re.search(r'^(\w+),\s*(\w+),\s*(\w+)\s+ADJ', line)
            if adj_match:
                result["lemma"] = adj_match.group(1)
                result["masculine"] = adj_match.group(1)
                result["feminine"] = adj_match.group(2)
                result["neuter"] = adj_match.group(3)
                result["translations"]["la"] = f"{result['masculine']}, {result['feminine']}, {result['neuter']}"
            
            # Parse English translation
            if ';' in line and not re.search(r'[A-Z]+\s*\[', line):
                trans = line.split(';')[0].strip()
                if trans and len(trans) > 5:
                    result["translations"]["en"] = trans
        
        return result
    
    def get_word_info(self, word: str) -> Optional[Dict]:
        """Main method to get structured word information"""
        print(f"🔍 Querying Whitaker for: {word}")
        
        html_content = self.query_whitaker(word)
        if not html_content:
            return None
        
        parsed_data = self.parse_whitaker_output(html_content, word)
        
        # Be respectful to the server
        time.sleep(1)
        
        return parsed_data
    
    def save_to_json(self, word_data: Dict, filename: str = None):
        """Save word data to JSON file"""
        if not filename:
            filename = f"{word_data['original_input']}_{word_data['part_of_speech']}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(word_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving to JSON: {e}")

# Example usage and test
def main():
    parser = WhitakerParser()
    
    # Test with your example
    test_words = ["buccinate", "amo", "rosa", "bonus"]
    
    for word in test_words:
        print(f"\n{'='*50}")
        print(f"Processing: {word}")
        print(f"{'='*50}")
        
        word_data = parser.get_word_info(word)
        
        if word_data:
            print(json.dumps(word_data, indent=2, ensure_ascii=False))
            
            # Save to file
            parser.save_to_json(word_data, f"latin_{word}.json")
        else:
            print(f"❌ No data found for {word}")

if __name__ == "__main__":
    main()