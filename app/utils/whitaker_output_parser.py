# whitaker_output_parser.py
import re
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class WhitakerOutputParser:
    """
    Parser for Whitaker's word analysis output to extract structured data
    in the desired JSON format.
    """
    
    def __init__(self):
        self.raw_output = ""
        
    def parse_analysis(self, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Whitaker analysis into structured JSON format."""
        if not analysis:
            return None
            
        self.raw_output = analysis.get("raw_output", "")
        if not self.raw_output:
            logger.warning("No raw_output in analysis")
            return None
            
        logger.debug(f"Parsing Whitaker output:\n{self.raw_output}")
        
        # Determine part of speech
        pos = self._determine_part_of_speech()
        if not pos:
            logger.warning("Could not determine part of speech")
            return None
            
        result = {
            "lemma": self._extract_lemma(),
            "part_of_speech": pos,
            "translations": self._extract_translations()
        }
        
        # Parse based on part of speech
        if pos == "verb":
            verb_data = self._parse_verb_data()
            result.update(verb_data)
        elif pos == "noun":
            noun_data = self._parse_noun_data()
            result.update(noun_data)
        elif pos == "adjective":
            adj_data = self._parse_adjective_data()
            result.update(adj_data)
            
        return result
    
    def _determine_part_of_speech(self) -> Optional[str]:
        """Determine the part of speech from raw output."""
        # Updated to handle both formats: with and without parentheses
        if re.search(r"V(?:\s*\(.*\))?", self.raw_output):
            return "verb"
        elif re.search(r"N(?:\s*\(.*\))?", self.raw_output):
            return "noun"
        elif re.search(r"ADJ(?:\s*\(.*\))?", self.raw_output):
            return "adjective"
        elif re.search(r"ADV(?:\s*\(.*\))?", self.raw_output):
            return "adverb"
        elif re.search(r"PRON(?:\s*\(.*\))?", self.raw_output):
            return "pronoun"
        elif re.search(r"PREP(?:\s*\(.*\))?", self.raw_output):
            return "preposition"
        elif re.search(r"CONJ(?:\s*\(.*\))?", self.raw_output):
            return "conjunction"
        elif re.search(r"INTERJ(?:\s*\(.*\))?", self.raw_output):
            return "interjection"
        elif re.search(r"NUM(?:\s*\(.*\))?", self.raw_output):
            return "numeral"
        return None
    
    def _extract_lemma(self) -> Optional[str]:
        """Extract lemma from raw output."""
        # Look for pattern: "lemma, form1, form2, ..." in the second line
        lines = self.raw_output.strip().split('\n')
        if len(lines) >= 2:
            # Second line typically has: "durus, dura -um, ..."
            lemma_match = re.search(r"^([a-zA-Z]+),", lines[1])
            if lemma_match:
                return lemma_match.group(1).lower()
        
        # Fallback: look anywhere in the output
        lemma_match = re.search(r"^([a-zA-Z]+),", self.raw_output, re.MULTILINE)
        return lemma_match.group(1).lower() if lemma_match else None
    
    def _extract_translations(self) -> Dict[str, str]:
        """Extract translations from raw output."""
        translations = {"en": "", "la": ""}
        
        # Extract English translations (lines that don't look like Latin forms)
        en_translations = []
        lines = self.raw_output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Skip lines that are clearly Latin forms or POS tags
            if (line and 
                not re.match(r'^[a-z]+\.[a-z]+\s+[A-Z]', line) and  # Skip "dur.us ADJ" lines
                not re.match(r'^[a-zA-Z]+,\s*[a-zA-Z]', line) and   # Skip "durus, dura" lines
                not re.match(r'^\s*$', line) and                    # Skip empty lines
                not re.search(r'\[XXX[A-Z]\]', line)):              # Skip frequency codes
                en_translations.append(line)
        
        translations["en"] = "; ".join(en_translations) if en_translations else ""
        
        # Latin form info - extract from the second line
        lines = self.raw_output.strip().split('\n')
        if len(lines) >= 2:
            translations["la"] = lines[1].strip()
        else:
            lemma = self._extract_lemma()
            translations["la"] = lemma if lemma else ""
        
        return translations
    
    def _parse_verb_data(self) -> Dict[str, Any]:
        """Parse verb-specific data."""
        verb_data = {
            "conjugation": self._extract_conjugation(),
            "deponent": self._is_deponent(),
            "infinitive": self._extract_infinitive(),
            "perfect": self._extract_perfect(),
            "supine": self._extract_supine(),
            "forms": self._extract_verb_forms()
        }
        
        # Remove None values
        return {k: v for k, v in verb_data.items() if v is not None}
    
    def _parse_noun_data(self) -> Dict[str, Any]:
        """Parse noun-specific data."""
        noun_data = {
            "declension": self._extract_declension(),
            "gender": self._extract_gender(),
            "nominative": self._extract_nominative(),
            "accusative": self._extract_accusative(),
            "forms": self._extract_noun_forms()
        }
        
        # Remove None values
        return {k: v for k, v in noun_data.items() if v is not None}
    
    def _parse_adjective_data(self) -> Dict[str, Any]:
        """Parse adjective-specific data."""
        adj_data = {
            "declension": self._extract_declension(),
            "gender": self._extract_gender(),
            "nominative": self._extract_nominative(),
            "forms_plural": self._extract_adjective_plural_forms()
        }
        
        # Remove None values
        return {k: v for k, v in adj_data.items() if v is not None}
    
    def _extract_conjugation(self) -> Optional[int]:
        """Extract verb conjugation number."""
        # Try both formats: with parentheses and without
        conj_match = re.search(r"V\s*\((\d)(?:st|nd|rd|th)\)", self.raw_output)
        if conj_match:
            return int(conj_match.group(1))
        
        # Alternative format: look for conjugation in the first line
        first_line = self.raw_output.split('\n')[0] if self.raw_output else ""
        if "V" in first_line:
            # Try to extract from patterns like "V   1 1 ..."
            conj_match = re.search(r"V\s+(\d)\s+\d", first_line)
            if conj_match:
                return int(conj_match.group(1))
        
        return None
    
    def _extract_declension(self) -> Optional[int]:
        """Extract noun/adjective declension number."""
        # Try both formats: with parentheses and without
        decl_match = re.search(r"(?:N|ADJ)\s*\((\d)(?:st|nd|rd|th)\)", self.raw_output)
        if decl_match:
            return int(decl_match.group(1))
        
        # Alternative format: look for declension in the first line
        first_line = self.raw_output.split('\n')[0] if self.raw_output else ""
        if "ADJ" in first_line or "N" in first_line:
            # Try to extract from patterns like "ADJ   1 1 ..." or "N   2 1 ..."
            decl_match = re.search(r"(?:ADJ|N)\s+(\d)\s+\d", first_line)
            if decl_match:
                return int(decl_match.group(1))
        
        return None
    
    def _extract_gender(self) -> Optional[str]:
        """Extract gender information."""
        first_line = self.raw_output.split('\n')[0] if self.raw_output else ""
        
        # Check first line for gender codes
        if " M " in first_line:
            return "masculine"
        elif " F " in first_line:
            return "feminine"
        elif " N " in first_line:
            return "neuter"
        
        # Fallback to text search
        if "masc" in self.raw_output.lower():
            return "masculine"
        elif "fem" in self.raw_output.lower():
            return "feminine"
        elif "neut" in self.raw_output.lower():
            return "neuter"
        
        return None
    
    def _is_deponent(self) -> bool:
        """Check if verb is deponent."""
        return "deponent" in self.raw_output.lower()
    
    def _extract_infinitive(self) -> Optional[str]:
        """Extract infinitive form for verbs."""
        # Look for second principal part in the second line
        lines = self.raw_output.strip().split('\n')
        if len(lines) >= 2:
            parts_match = re.search(r"^[a-zA-Z]+,\s*([a-zA-Z]+)", lines[1])
            return parts_match.group(1).lower() if parts_match else None
        return None
    
    def _extract_perfect(self) -> Optional[str]:
        """Extract perfect form for verbs."""
        # Look for third principal part in the second line
        lines = self.raw_output.strip().split('\n')
        if len(lines) >= 2:
            parts_match = re.search(r"^[a-zA-Z]+,\s*[a-zA-Z]+,\s*([a-zA-Z]+)", lines[1])
            return parts_match.group(1).lower() if parts_match else None
        return None
    
    def _extract_supine(self) -> Optional[str]:
        """Extract supine form for verbs."""
        # Look for fourth principal part in the second line
        lines = self.raw_output.strip().split('\n')
        if len(lines) >= 2:
            parts_match = re.search(r"^[a-zA-Z]+,\s*[a-zA-Z]+,\s*[a-zA-Z]+,\s*([a-zA-Z]+)", lines[1])
            return parts_match.group(1).lower() if parts_match else None
        return None
    
    def _extract_nominative(self) -> Optional[str]:
        """Extract nominative form."""
        lemma = self._extract_lemma()
        return lemma.lower() if lemma else None
    
    def _extract_accusative(self) -> Optional[str]:
        """Extract accusative form for nouns."""
        # This would need more sophisticated parsing based on declension patterns
        # For now, return None and rely on forms extraction
        return None
    
    def _extract_verb_forms(self) -> Dict[str, List[str]]:
        """Extract various verb forms."""
        forms = {}
        
        # Extract present tense forms
        present_forms = self._extract_forms_by_tense("present")
        if present_forms:
            forms["present"] = present_forms
        
        # Extract imperative forms
        imperative_forms = self._extract_forms_by_mood("imperative")
        if imperative_forms:
            forms["imperative"] = imperative_forms
            
        # Extract subjunctive forms
        subjunctive_forms = self._extract_forms_by_mood("subjunctive")
        if subjunctive_forms:
            forms["subjunctive"] = subjunctive_forms
            
        # Extract perfect forms
        perfect_forms = self._extract_forms_by_tense("perfect")
        if perfect_forms:
            forms["perfect"] = perfect_forms
            
        return forms
    
    def _extract_noun_forms(self) -> Dict[str, List[str]]:
        """Extract noun forms."""
        forms = {}
        
        # Extract ablative forms
        ablative_match = re.findall(r"\b(\w+)\s*\(Abl\)", self.raw_output)
        if ablative_match:
            forms["ablative"] = [form.lower() for form in ablative_match]
            
        return forms
    
    def _extract_adjective_plural_forms(self) -> Dict[str, List[str]]:
        """Extract adjective plural forms."""
        plural_forms = {}
        
        # This would need more sophisticated parsing
        # For now, return empty dict
        return plural_forms
    
    def _extract_forms_by_tense(self, tense: str) -> List[str]:
        """Extract forms by tense (simplified implementation)."""
        # This is a simplified implementation - you'd need to expand this
        # based on the actual Whitaker output format
        forms = []
        tense_patterns = {
            "present": r"Pres\s+([a-zA-Z]+)",
            "perfect": r"Perf\s+([a-zA-Z]+)"
        }
        
        if tense in tense_patterns:
            matches = re.findall(tense_patterns[tense], self.raw_output)
            forms = [match.lower() for match in matches]
            
        return forms
    
    def _extract_forms_by_mood(self, mood: str) -> List[str]:
        """Extract forms by mood (simplified implementation)."""
        # This is a simplified implementation - you'd need to expand this
        forms = []
        mood_patterns = {
            "imperative": r"Imper\s+([a-zA-Z]+)",
            "subjunctive": r"Subj\s+([a-zA-Z]+)"
        }
        
        if mood in mood_patterns:
            matches = re.findall(mood_patterns[mood], self.raw_output)
            forms = [match.lower() for match in matches]
            
        return forms

from app.rag.simple_whitaker_client import SimpleWhitakerClient

# Enhanced SimpleWhitakerClient with parsing capability
class EnhancedWhitakerClient(SimpleWhitakerClient):
    """
    Enhanced Whitaker client that includes output parsing.
    """
    
    def __init__(self, host: str = "localhost", port: int = 9090, base_url: str = None):
        super().__init__(host, port, base_url)
        self.parser = WhitakerOutputParser()
    
    def analyze_word_structured(self, word: str, language: str = "la") -> Optional[Dict[str, Any]]:
        """
        Analyze a word and return structured JSON format.
        """
        response = self.analyze_word(word, language)
        if not response:
            return None
            
        analysis = response.get("analysis", {})
        structured_result = self.parser.parse_analysis(analysis)
        
        if structured_result:
            logger.info(f"✅ Generated structured analysis for: {word}")
        else:
            logger.warning(f"⚠️ Could not generate structured analysis for: {word}")
            
        return structured_result