import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class AugustineRetriever:
    def __init__(self, cassandra_client):
        self.cassandra_client = cassandra_client
    
    def retrieve_psalm_context(self, psalm_number: int, verse_number: Optional[int] = None, question: str = "") -> str:
        """Retrieve Augustine's commentary on specific Psalms"""
        context_parts = []
        
        # Get Psalm text
        if verse_number:
            verse_query = """
                SELECT latin_text, english_translation 
                FROM psalm_verses 
                WHERE psalm_number = %s AND verse_number = %s
            """
            verse_result = self.cassandra_client.execute_query(verse_query, (psalm_number, verse_number)).one()
            if verse_result:
                context_parts.append(f"PSALM {psalm_number}:{verse_number}")
                context_parts.append(f"Latin: {verse_result.latin_text}")
                context_parts.append(f"English: {verse_result.english_translation}")
        
        # Get Augustine's commentary
        commentary_query = """
            SELECT work_title, latin_commentary, english_translation, key_phrases
            FROM augustine_expositions 
            WHERE psalm_number = %s
        """
        params = [psalm_number]
        
        if verse_number:
            commentary_query += " AND verse_start <= %s AND verse_end >= %s"
            params.extend([verse_number, verse_number])
        
        commentary_query += " LIMIT 5"
        
        commentaries = self.cassandra_client.execute_query(commentary_query, params)
        
        for comment in commentaries:
            context_parts.append(f"\nAUGUSTINE - {comment.work_title}:")
            context_parts.append(f"Latin: {comment.latin_commentary}")
            context_parts.append(f"English: {comment.english_translation}")
            if comment.key_phrases:
                context_parts.append(f"Key Themes: {', '.join(comment.key_phrases)}")
        
        return "\n".join(context_parts) if context_parts else "No relevant Augustine commentary found."
    
    def retrieve_word_study(self, word: str, psalm_number: int, verse_number: Optional[int] = None) -> str:
        """Retrieve word-specific studies from Augustine"""
        context_parts = []
        
        # Get word studies
        word_query = """
            SELECT grammatical_form, augustine_interpretation, theological_significance
            FROM word_studies 
            WHERE word = %s AND language = 'latin' AND psalm_number = %s
        """
        params = [word, psalm_number]
        
        if verse_number:
            word_query += " AND verse_number = %s"
            params.append(verse_number)
        
        word_studies = self.cassandra_client.execute_query(word_query, params)
        
        for study in word_studies:
            context_parts.append(f"WORD: {word}")
            context_parts.append(f"Grammatical Form: {study.grammatical_form}")
            context_parts.append(f"Augustine's Interpretation: {study.augustine_interpretation}")
            context_parts.append(f"Theological Significance: {study.theological_significance}")
        
        return "\n".join(context_parts) if context_parts else f"No specific Augustine interpretation found for '{word}' in Psalm {psalm_number}."
