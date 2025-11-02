# app/rag/retriever.py
import logging
import re
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

class AugustineRetriever:
    """Intelligent retriever for Psalms and Augustine commentaries"""
    
    def __init__(self, cassandra_client):
        self.cassandra_client = cassandra_client
        from app.utils.psalm_number_converter import PsalmNumberConverter
        self.converter = PsalmNumberConverter()

    def retrieve_relevant_context(self, question: str, psalm_number = None, verse_number = None) -> str:
        """
        Intelligent retrieval with proper type handling
        REMOVE the type hints to allow any type, then convert internally
        """
        logger.info(f"🔍 Retrieving context for: '{question}', Psalm {psalm_number}:{verse_number}")
        
        # DEBUG: Log what we're receiving
        logger.info(f"🔍 DEBUG retriever received - psalm_number: {psalm_number} (type: {type(psalm_number)}), verse_number: {verse_number} (type: {type(verse_number)})")
        
        # Convert parameters to integers if they're strings
        try:
            if psalm_number is not None:
                if isinstance(psalm_number, str):
                    psalm_number = int(psalm_number)
                    logger.info(f"🔍 DEBUG Converted psalm_number from string to int: {psalm_number}")
                # Also handle if it's already an int but from different source
                psalm_number = int(psalm_number)
            if verse_number is not None:
                if isinstance(verse_number, str):
                    verse_number = int(verse_number) 
                    logger.info(f"🔍 DEBUG Converted verse_number from string to int: {verse_number}")
                verse_number = int(verse_number)
        except (ValueError, TypeError) as e:
            logger.warning(f"Type conversion issue: {e}. Using None for database queries.")
            # If conversion fails, use None to avoid Cassandra errors
            psalm_number = None
            verse_number = None
        
        logger.info(f"🔍 DEBUG After conversion - psalm_number: {psalm_number} (type: {type(psalm_number)}), verse_number: {verse_number} (type: {type(verse_number)})")
        
        # Rest of the method remains the same...
        context_parts = []
        
        # Analyze the question to understand what user needs
        question_analysis = self._analyze_question(question)
        latin_words = question_analysis['latin_words']
        needs_augustine = question_analysis['needs_augustine']
        needs_psalm_text = question_analysis['needs_psalm_text']
        is_word_analysis = question_analysis['is_word_analysis']
        
        logger.info(f"Question analysis: {question_analysis}")
        
        # 1. Get Psalm text if needed
        if needs_psalm_text and psalm_number is not None:
            psalm_context = self._get_psalm_context(psalm_number, verse_number, latin_words)
            if psalm_context:
                context_parts.append(psalm_context)
        
        # 2. Get Augustine commentary if needed
        if needs_augustine and psalm_number is not None:
            # Convert Vulgate → Protestant for Augustine queries
            protestant_psalm = self.converter.to_protestant(psalm_number)
            logger.info(f"🔄 Augustine query conversion: Vulgate {psalm_number} → Protestant {protestant_psalm}")
            augustine_context = self._get_augustine_context(protestant_psalm, verse_number, latin_words, question)
            if augustine_context:
                context_parts.append(augustine_context)
        
        # 3. If we have Latin words but no specific context found, do broader search
        if latin_words and not context_parts and psalm_number is not None:
            broader_context = self._search_by_latin_words(latin_words, psalm_number)
            if broader_context:
                context_parts.append(broader_context)
        
        final_context = "\n\n".join(context_parts) if context_parts else "No relevant data found for the query."
        
        logger.info(f"📚 Retrieved context length: {len(final_context)} characters")
        return final_context
    
    def _analyze_question(self, question: str) -> Dict[str, Any]:
        """Analyze the question to understand user intent"""
        question_lower = question.lower()
        
        return {
            'latin_words': self._extract_latin_words(question),
            'needs_augustine': any(keyword in question_lower for keyword in [
                'augustine', 'exposition', 'commentary', 'interpretation', 'explain', 
                'analysis', 'st.', 'saint', 'church father'
            ]),
            'needs_psalm_text': not any(keyword in question_lower for keyword in [
                'method', 'approach', 'style', 'about augustine'
            ]),
            'is_word_analysis': any(keyword in question_lower for keyword in [
                'word', 'analyze', 'meaning', 'definition', 'grammar'
            ])
        }
    
    def _extract_latin_words(self, text: str) -> List[str]:
        """Extract potential Latin words from text"""
        # Common Latin patterns: words with typical Latin endings
        latin_patterns = [
            r'\b[a-zA-Z]+(?:us|um|a|ae|is|it|at|et|nt|tur|ur|bit|vit|sit)\b',
            r'\b(?:abiit|stetit|sedit|meditabitur|lege|domini|beatus|vir|consilio)\b'
        ]
        
        words = []
        for pattern in latin_patterns:
            words.extend(re.findall(pattern, text, re.IGNORECASE))
        
        # Remove duplicates and return lowercase
        return list(set([w.lower() for w in words]))
    
    def _get_psalm_context(self, psalm_number: int, verse_number: Optional[int], 
                          latin_words: List[str]) -> Optional[str]:
        """Get relevant Psalm verses"""
        context_parts = []
        
        if verse_number:
            # Get specific verse
            verses_to_check = [verse_number]
        else:
            # Get first few verses for context
            verses_to_check = [1, 2, 3]
        
        for v in verses_to_check:
            verse = self.cassandra_client.get_psalm_verse(psalm_number, "", v)
            if verse:
                verse_text = f"PSALM {psalm_number}:{v}\n"
                verse_text += f"Latin: {verse['latin_text']}\n"
                verse_text += f"English: {verse['english_translation']}\n"
                if verse['grammatical_notes']:
                    verse_text += f"Grammar: {verse['grammatical_notes']}\n"
                
                # Highlight if this verse contains the Latin words we're looking for
                if latin_words and any(word in verse['latin_text'].lower() for word in latin_words):
                    verse_text += "🔍 **Contains relevant Latin words**\n"
                
                context_parts.append(verse_text)
        
        return "\n".join(context_parts) if context_parts else None
    
    def _get_augustine_context(self, psalm_number: int, verse_number: Optional[int],
                             latin_words: List[str], question: str) -> Optional[str]:
        """Get relevant Augustine commentary"""
        context_parts = []
        
        comments = self.cassandra_client.get_augustine_comments(psalm_number, verse_number)
        
        for comment in comments:
            commentary_text = f"AUGUSTINE - {comment['work_title']}\n"
            
            # Add verse range if available
            if comment['verse_start'] and comment['verse_end']:
                commentary_text += f"Verses: {comment['verse_start']}-{comment['verse_end']}\n"
            
            commentary_text += f"Latin: {comment['latin_text']}\n"
            commentary_text += f"English: {comment['english_translation']}\n"
            
            if comment['key_terms']:
                commentary_text += f"Key Terms: {', '.join(comment['key_terms'])}\n"
            
            # Highlight if this commentary contains the Latin words we're looking for
            if latin_words:
                contains_words = []
                for word in latin_words:
                    if (word in comment['latin_text'].lower() or 
                        any(word in term.lower() for term in comment.get('key_terms', []))):
                        contains_words.append(word)
                
                if contains_words:
                    commentary_text += f"🔍 **Discusses: {', '.join(contains_words)}**\n"
            
            context_parts.append(commentary_text)
        
        return "\n---\n".join(context_parts) if context_parts else None
    
    def _search_by_latin_words(self, latin_words: List[str], psalm_number: Optional[int]) -> Optional[str]:
        """Broader search when we have Latin words but no specific context"""
        context_parts = []
        
        # Search in Psalms
        if psalm_number:
            for v in [1, 2]:  # Check first few verses
                verse = self.cassandra_client.get_psalm_verse(psalm_number, "", v)
                if verse and any(word in verse['latin_text'].lower() for word in latin_words):
                    context_parts.append(f"PSALM {psalm_number}:{v} contains relevant words")
                    context_parts.append(f"Latin: {verse['latin_text']}")
        
        # Search in Augustine commentaries
        if psalm_number:
            protestant_psalm = self.converter.to_protestant(psalm_number)
            comments = self.cassandra_client.get_augustine_comments(protestant_psalm, None)
            for comment in comments:
                if any(word in comment['latin_text'].lower() for word in latin_words):
                    context_parts.append(f"AUGUSTINE discusses these words in {comment['work_title']}")
                    context_parts.append(f"Excerpt: {comment['latin_text'][:100]}...")
        
        return "\n".join(context_parts) if context_parts else Nonet