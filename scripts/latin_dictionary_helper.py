# latin_dictionary_helper.py

import requests
import re
import json
import time
from typing import Dict, Optional
from bs4 import BeautifulSoup

class LatinDictionaryHelper:
    def __init__(self):
        self.whitaker_url = "https://archives.nd.edu/cgi-bin/wordz.pl"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_word_info(self, word: str) -> Optional[Dict]:
        """Get complete word information in structured JSON format"""
        print(f"🔍 Querying Whitaker for: '{word}'")
        
        raw_html = self._query_whitaker(word)
        if not raw_html:
            print("❌ No response from Whitaker's Words")
            return None
        
        # Parse the HTML content
        return self._parse_whitaker_data(raw_html, word)
    
    def _query_whitaker(self, word: str) -> Optional[str]:
        """Query Whitaker's Words website"""
        try:
            params = {'keyword': word, 'english': 'Search'}
            response = self.session.get(self.whitaker_url, params=params, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"❌ Network error: {e}")
            return None
    
    def _parse_whitaker_data(self, html_content: str, original_word: str) -> Optional[Dict]:
        """Parse the HTML response from Whitaker's Words"""
        soup = BeautifulSoup(html_content, 'html.parser')
        pre_tags = soup.find_all('pre')
        
        if not pre_tags:
            print("❌ No dictionary data found in response")
            return None
        
        content = pre_tags[0].get_text()
        print(f"📄 Raw response preview: {content[:200]}...")
        
        # Try to parse as verb first
        verb_data = self._parse_verb_entry(content, original_word)
        if verb_data:
            return verb_data
        
        # Try other parts of speech if verb parsing fails
        noun_data = self._parse_noun_entry(content, original_word)
        if noun_data:
            return noun_data
        
        print("❌ Could not parse any grammatical data from response")
        return None
    
    def _parse_verb_entry(self, content: str, original_word: str) -> Optional[Dict]:
        """Parse verb data from Whitaker's output"""
        
        # Look for the main verb entry pattern: "lemma, infinitive, perfect, supine"
        verb_match = re.search(r'(\w+),\s*(\w+),\s*(\w+),\s*(\w+)\s+V\s*\((\d)', content)
        if not verb_match:
            print("❌ No verb pattern found")
            return None
        
        lemma, infinitive, perfect, supine, conjugation = verb_match.groups()
        conjugation = int(conjugation)
        
        print(f"✅ Found verb: {lemma} (conjugation {conjugation})")
        
        # Extract English translation
        english_trans = self._extract_english_translation(content)
        
        # Extract forms
        imperative_forms = self._extract_imperative_forms(content, lemma, conjugation)
        
        # Build the structured result
        result = {
            "lemma": lemma,
            "part_of_speech": "verb",
            "conjugation": conjugation,
            "infinitive": infinitive,
            "present": lemma,  # First person singular present
            "future": self._generate_future_tense(infinitive, conjugation),
            "perfect": perfect,
            "supine": supine,
            "forms": {
                "imperative": imperative_forms
            },
            "translations": {
                "en": english_trans,
                "la": f"{lemma}, {infinitive}, {perfect}, {supine}"
            },
            "original_input": original_word,
            "identified_lemma": lemma
        }
        
        return result
    
    def _parse_noun_entry(self, content: str, original_word: str) -> Optional[Dict]:
        """Parse noun data from Whitaker's output"""
        noun_match = re.search(r'(\w+),\s*(\w+)\s+[AN]\s*\[?(\d)[\s\*]*([MFN])?', content)
        if not noun_match:
            return None
        
        lemma, genitive, declension, gender = noun_match.groups()
        declension = int(declension)
        
        print(f"✅ Found noun: {lemma} (declension {declension})")
        
        english_trans = self._extract_english_translation(content)
        
        return {
            "lemma": lemma,
            "part_of_speech": "noun",
            "declension": declension,
            "gender": gender.lower() if gender else "unknown",
            "genitive": genitive,
            "translations": {
                "en": english_trans,
                "la": f"{lemma}, {genitive}"
            },
            "original_input": original_word,
            "identified_lemma": lemma
        }
    
    def _extract_english_translation(self, content: str) -> str:
        """Extract English translation from the content"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            # Look for lines with translations (usually contain meaningful text and semicolons)
            if ';' in line and len(line) > 20 and not re.search(r'[A-Z]+\s*\[[XW]', line):
                # Take the part before the first semicolon
                translation = line.split(';')[0].strip()
                if translation and not translation.startswith('http'):
                    return translation
        return "Translation not found"
    
    def _extract_imperative_forms(self, content: str, lemma: str, conjugation: int) -> list:
        """Extract imperative forms from the content"""
        forms = []
        
        # Look for imperative patterns in the content
        imperative_patterns = [
            r'(\w+)\s+V\s.*?IMPERATIVE',
            r'(\w+)\s+V\s.*?IMP\s.*?2 P',
            r'(\w+)\s+VPAR.*?IMPERATIVE',
        ]
        
        for pattern in imperative_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                clean_form = match.replace('.', '')
                if clean_form not in forms:
                    forms.append(clean_form)
        
        # If no forms found, generate common imperative forms based on conjugation
        if not forms:
            forms = self._generate_imperative_forms(lemma, conjugation)
        
        return forms
    
    def _generate_imperative_forms(self, lemma: str, conjugation: int) -> list:
        """Generate common imperative forms based on conjugation rules"""
        stem = lemma[:-1]  # Remove the -o ending
        
        if conjugation == 1:
            return [stem + "a", stem + "ate"]  # e.g., ama, amate
        elif conjugation == 2:
            return [stem + "e", stem + "ete"]  # e.g., mone, monete
        elif conjugation == 3:
            return [stem + "e", stem + "ite"]  # e.g., mitte, mittite
        elif conjugation == 4:
            return [stem + "i", stem + "ite"]  # e.g., audī, audīte
        else:
            return []
    
    def _generate_future_tense(self, infinitive: str, conjugation: int) -> str:
        """Generate future tense form based on conjugation"""
        stem = infinitive[:-2]  # Remove 're'
        
        if conjugation == 1:
            return stem + "bo"      # amabo
        elif conjugation == 2:
            return stem + "bo"      # monebo
        elif conjugation == 3:
            return stem[:-1] + "am"  # mittam (remove last consonant)
        elif conjugation == 4:
            return stem + "am"      # audiam
        else:
            return stem + "bo"      # fallback

# Test function
def test_parser():
    """Test the parser with various words"""
    parser = LatinDictionaryHelper()
    
    test_words = [
        "buccinate",  # Your example - imperative plural
        "amo",        # Basic verb
        "laudo",      # First conjugation
        "moneo",      # Second conjugation  
        "lego",       # Third conjugation
        "audio",      # Fourth conjugation
        "rosa",       # Noun
    ]
    
    for word in test_words:
        print(f"\n{'='*60}")
        print(f"Testing: '{word}'")
        print(f"{'='*60}")
        
        result = parser.get_word_info(word)
        
        if result:
            print("✅ SUCCESS - Found data:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Save to file
            filename = f"latin_{word}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved to {filename}")
        else:
            print("❌ FAILED - No data found")
        
        # Be nice to the server
        time.sleep(2)

if __name__ == "__main__":
    test_parser()