# app/processors/latin_rag_processor.py
import json

class LatinRAGProcessor:
    def __init__(self, ai_provider, cassandra_db):
        self.ai_provider = ai_provider
        self.db = cassandra_db
        
    def initialize_from_json(self, json_file_path):
        """Load your existing JSON data into Cassandra"""
        with open(json_file_path, 'r', encoding='utf-8') as f:
            words_data = json.load(f)
        
        for word_data in words_data:
            self.db.store_word(word_data)
            print(f"Loaded: {word_data['lemma']}")
    
    def analyze_latin_word(self, word, context_type="biblical", user_query=""):
        """Enhanced RAG analysis using your existing data + AI"""
        
        # 1. RETRIEVAL: Get from Cassandra
        db_word = self.db.get_word(word)
        usage_contexts = self.db.get_word_context(word, context_type)
        
        if not db_word:
            # Word not in database - use AI to generate and store
            return self._handle_new_word(word, context_type, user_query)
        
        # 2. AUGMENTATION: Build context from database
        context = self._build_rag_context(db_word, usage_contexts, user_query)
        
        # 3. GENERATION: Use AI to create comprehensive analysis
        return self._generate_analysis(word, context, user_query)
    
    def _build_rag_context(self, db_word, usage_contexts, user_query):
        """Build RAG context from Cassandra data"""
        context_parts = []
        
        # Basic word information
        context_parts.append(f"WORD: {db_word.lemma}")
        context_parts.append(f"Part of Speech: {db_word.part_of_speech}")
        
        if db_word.translations:
            context_parts.append("Translations:")
            for lang, trans in db_word.translations.items():
                context_parts.append(f"  {lang}: {trans}")
        
        # Verb-specific info
        if db_word.part_of_speech == 'verb':
            context_parts.append(f"Conjugation: {db_word.conjugation}")
            context_parts.extend([
                f"Present: {db_word.present}",
                f"Future: {db_word.future}", 
                f"Perfect: {db_word.perfect}",
                f"Supine: {db_word.supine}"
            ])
        
        # Noun-specific info  
        if db_word.part_of_speech == 'noun':
            context_parts.append(f"Declension: {db_word.declension}")
            context_parts.append(f"Gender: {db_word.gender}")
        
        # Usage contexts from RAG
        if usage_contexts:
            context_parts.append("\nCONTEXTUAL USAGE:")
            for usage in usage_contexts:
                context_parts.append(f"Source: {usage.source} ({usage.reference})")
                context_parts.append(f"Context: {usage.context_text}")
                if usage.usage_examples:
                    context_parts.append("Examples:")
                    for example in usage.usage_examples:
                        context_parts.append(f"  - {example}")
        
        return "\n".join(context_parts)
    
    def _generate_analysis(self, word, context, user_query):
        """Generate AI analysis using RAG context"""
        prompt = f"""
        Based on the following verified Latin data, provide a comprehensive analysis of '{word}'.
        
        VERIFIED DATA:
        {context}
        
        USER REQUEST: {user_query}
        
        Please provide:
        1. Complete grammatical analysis
        2. All possible forms and conjugations/declensions  
        3. Usage examples in context
        4. Theological/literary significance if relevant
        5. Relationship to other Latin words
        
        Format the response clearly with sections.
        """
        
        return self.ai_provider.generate_openai_compatible(
            [{"role": "user", "content": prompt}],
            model="your-model",
            stream=False
        )
    
    def _handle_new_word(self, word, context_type, user_query):
        """Handle words not in the database"""
        prompt = f"""
        Analyze the Latin word: {word}
        
        User context: {user_query}
        Requested analysis type: {context_type}
        
        Please provide comprehensive analysis including:
        - Complete grammatical information
        - All forms and conjugations/declensions
        - Translation and meanings
        - Usage examples
        
        Return the analysis in a structured format.
        """
        
        response = self.ai_provider.generate_openai_compatible(
            [{"role": "user", "content": prompt}],
            model="your-model", 
            stream=False
        )
        
        # TODO: Parse response and store in Cassandra
        # You could add logic to extract structured data and call db.store_word()
        
        return response