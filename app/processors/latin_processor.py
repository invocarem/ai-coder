# app/processors/latin_processor.py
import logging
import re
from flask import jsonify, Response
import json
import time

logger = logging.getLogger(__name__)

class LatinProcessor:
    """Handles Latin language analysis with morphological parsing and lemma lookup"""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        
        # Common Latin endings for morphological analysis
        self.verb_endings = {
            'present': ['o', 's', 't', 'mus', 'tis', 'nt', 'or', 'ris', 'tur', 'mur', 'mini', 'ntur'],
            'perfect': ['i', 'isti', 'it', 'imus', 'istis', 'erunt', 'eram', 'eras', 'erat'],
            'supine': ['um', 'u']
        }
        
        self.noun_endings = {
            '1st': ['a', 'ae', 'ae', 'am', 'a', 'a', 'ae', 'arum', 'is', 'as', 'ae', 'is'],
            '2nd': ['us', 'i', 'o', 'um', 'o', 'e', 'i', 'orum', 'is', 'os', 'i', 'is'],
            '3rd': ['', 'is', 'i', 'em', 'e', 'es', 'um', 'ibus', 'es', 'ibus']
        }

        self.prompt_templates = {
            "latin_word_analysis": """
            Analyze this Latin word form: **{word_form}**
            
            **Context:** {context}
            **Sentence:** {sentence}
            
            Please provide:
            
            **1. Lemma Identification:**
            - Most likely dictionary form (lemma)
            - Confidence level for the identification
            
            **2. Morphological Analysis:**
            - Part of speech
            - Tense, mood, voice (if verb)
            - Case, number, gender (if noun/adjective)
            - Person and number (if verb)
            
            **3. Full Grammatical Information:**
            - Conjugation/declension pattern
            - Principal parts (if verb)
            - All possible forms
            
            **4. Translation and Usage:**
            - English translation
            - Usage in the given context
            - Biblical/theological significance if relevant
            
            **5. Related Words:**
            - Derivatives and cognates
            - Related Latin words
            
            If you're uncertain about the lemma, please indicate this and provide multiple possibilities.
            """,
            
            "verse_lemma_analysis": """
            Analyze all words in this Latin verse and provide their lemmas:
            
            **Verse:** {verse}
            **Translation:** {translation}
            
            Please provide:
            
            **Complete Word-by-Word Analysis:**
            
            For each word in the verse:
            - **Word form:** [as it appears]
            - **Lemma:** [dictionary form]
            - **Part of speech:** 
            - **Morphological analysis:** (case, tense, etc.)
            - **English equivalent:**
            - **Grammatical role in sentence:**
            
            **Overall Verse Analysis:**
            - Grammatical structure
            - Key theological terms
            - Significant word choices
            - Rhetorical devices
            
            Format as a clear table for the word analysis and prose for the overall analysis.
            """,
            
            "patristic_exposition": """
            Provide St. Augustine's exposition on this biblical passage:
            
            **Passage:** {passage}
            **Translation:** {translation}
            
            Please draw from Augustine's actual writings and provide:
            
            **1. Direct Citations:**
            - Relevant quotes from Augustine's works
            - Reference to specific books/sermons
            
            **2. Theological Insights:**
            - Augustine's key interpretations
            - Doctrinal significance
            - Spiritual applications
            
            **3. Contextual Analysis:**
            - How Augustine relates this to other Scripture
            - Pastoral implications
            - Anti-heretical arguments if relevant
            
            **4. Practical Applications:**
            - How Augustine applies this to Christian life
            - Moral and spiritual lessons
            
            Focus on authentic Augustinian interpretation rather than general commentary.
            """
        }

    def process(self, pattern_data, model, stream, original_data):
        """Process Latin-related patterns"""
        pattern = pattern_data['pattern']
        
        if pattern == 'latin_analysis':
            return self._analyze_latin_word(pattern_data, model, stream, original_data)
        elif pattern == 'verse_lemmas':
            return self._analyze_verse_lemmas(pattern_data, model, stream, original_data)
        elif pattern == 'patristic_exposition':
            return self._get_patristic_exposition(pattern_data, model, stream, original_data)
        else:
            return jsonify({"error": f"Unsupported Latin pattern: {pattern}"}), 400
    
    def _analyze_latin_word(self, pattern_data, model, stream, original_data):
        """Analyze a Latin word form and find its lemma"""
        word_form = pattern_data['word_form']
        context = pattern_data.get('context', '')
        sentence = pattern_data.get('sentence', '')
        
        # First, try to identify possible lemmas
        possible_lemmas = self._suggest_lemmas(word_form)
        
        prompt = self.prompt_templates['latin_word_analysis'].format(
            word_form=word_form,
            context=context,
            sentence=sentence
        )
        
        # Add lemma suggestions to prompt if we have them
        if possible_lemmas:
            prompt += f"\n\nPossible lemmas based on form analysis: {', '.join(possible_lemmas)}"
        
        return self._call_ai_provider(prompt, model, stream, original_data)
    
    def _analyze_verse_lemmas(self, pattern_data, model, stream, original_data):
        """Analyze all words in a Latin verse and provide lemmas"""
        verse = pattern_data['verse']
        translation = pattern_data.get('translation', '')
        
        # Extract individual words from the verse
        words = self._extract_latin_words(verse)
        
        prompt = self.prompt_templates['verse_lemma_analysis'].format(
            verse=verse,
            translation=translation
        )
        
        return self._call_ai_provider(prompt, model, stream, original_data)
    
    def _get_patristic_exposition(self, pattern_data, model, stream, original_data):
        """Get St. Augustine's exposition on a biblical passage"""
        passage = pattern_data['passage']
        translation = pattern_data.get('translation', '')
        church_father = pattern_data.get('church_father', 'Augustine')
        
        prompt = self.prompt_templates['patristic_exposition'].format(
            passage=passage,
            translation=translation
        )
        
        # Customize for different Church Fathers
        if church_father != 'Augustine':
            prompt = prompt.replace("Augustine", church_father)
            prompt = prompt.replace("Augustinian", f"{church_father}'s")
        
        return self._call_ai_provider(prompt, model, stream, original_data)
    
    def _suggest_lemmas(self, word_form):
        """Suggest possible lemmas based on morphological patterns"""
        suggestions = []
        word_lower = word_form.lower()
        
        # Verb pattern matching
        if word_lower.endswith('it'):  # like "abiit"
            # Could be perfect tense of -eo verb or present of -io verb
            stem = word_lower[:-2]
            suggestions.extend([f"{stem}eo", f"{stem}io", f"{stem}o"])
        
        elif word_lower.endswith('avit') or word_lower.endswith('evit'):
            # First conjugation perfect
            stem = word_lower[:-4]
            suggestions.append(f"{stem}o")
        
        elif word_lower.endswith('iit'):
            # Contracted perfect forms
            stem = word_lower[:-3]
            suggestions.extend([f"{stem}eo", f"{stem}io"])
        
        # Noun pattern matching
        if word_lower.endswith('us'):
            suggestions.append(word_lower[:-2] + 'us')  # 2nd declension
        elif word_lower.endswith('a'):
            suggestions.append(word_lower[:-1] + 'a')   # 1st declension
        elif word_lower.endswith('um'):
            suggestions.append(word_lower[:-2] + 'um')  # 2nd declension neuter
        
        return list(set(suggestions))  # Remove duplicates
    
    def _extract_latin_words(self, verse):
        """Extract individual Latin words from a verse, handling punctuation"""
        # Remove punctuation and split
        clean_verse = re.sub(r'[.,;!?]', ' ', verse)
        words = [word.strip() for word in clean_verse.split() if word.strip()]
        return words
    
    def _call_ai_provider(self, prompt, model, stream, original_data):
        """Call AI provider and format response (same as before)"""
        try:
            options = {
                "temperature": original_data.get('temperature', 0.1),
                "top_p": original_data.get('top_p', 0.9),
                "max_tokens": original_data.get('max_tokens', 4096)
            }
            
            messages = [{"role": "user", "content": prompt}]
            
            if stream:
                response = self.ai_provider.generate_openai_compatible(
                    messages, model, stream=True, **options
                )
                return self._format_streaming_response(response, model)
            else:
                response = self.ai_provider.generate_openai_compatible(
                    messages, model, stream=False, **options
                )
                return self._format_openai_response(response, model)
                
        except Exception as e:
            return jsonify({"error": f"Latin analysis failed: {str(e)}"}), 500
    
    # ... keep the same _format_streaming_response and _format_openai_response methods ...