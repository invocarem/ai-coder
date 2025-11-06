# app/processors/latin_processor.py
import logging
from flask import jsonify, Response
import json
import time
import requests
from app.config import load_config

logger = logging.getLogger(__name__)

class LatinProcessor:
    """Handles Latin word analysis with morphological parsing and lemma identification"""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        self.config = load_config()
        self.default_model = self.config["DEFAULT_MODEL"]

        self.prompt_templates = {
    "latin_analysis": """
Analyze the Latin word: **{word_form}**

Please provide a COMPLETE morphological analysis and return ONLY a JSON object following this EXACT structure:

For VERBS:
{{
  "lemma": "first_person_present_form",
  "part_of_speech": "verb",
  "conjugation": 1|2|3|4|mixed|irregular,
  "infinitive": "present_infinitive",
  "present": "first_person_present",
  "future": "first_person_future",
  "perfect": "first_person_perfect",
  "supine": "supine_form",
  "translations": {{
    "en": "primary_english_meaning",
    "la": "latin_principal_parts"
  }},
  "forms": {{
    "present_active_subjunctive": ["list", "of", "forms"],
    "other_paradigms": ["list", "of", "forms"]
  }}
}}

For NOUNS:
{{
  "lemma": "nominative_singular",
  "part_of_speech": "noun", 
  "declension": 1|2|3|4|5|irregular,
  "gender": "masculine|feminine|neuter",
  "nominative": "nominative_singular",
  "genitive": "genitive_singular",
  "translations": {{
    "en": "primary_english_meaning",
    "la": "latin_dictionary_form"
  }}
}}

For ADJECTIVES:
{{
  "lemma": "masculine_nominative_singular",
  "part_of_speech": "adjective",
  "declension": 1|2|3|irregular,
  "gender": "masculine",
  "nominative": "masculine_nominative_singular", 
  "genitive": "masculine_genitive_singular",
  "translations": {{
    "en": "primary_english_meaning",
    "la": "latin_dictionary_form"
  }},
  "forms": {{
    "nominative_f": ["feminine_nominative"],
    "nominative_n": ["neuter_nominative"],
    "genitive_f": ["feminine_genitive"],
    "genitive_n": ["neuter_genitive"],
    "other_forms": ["list", "of", "forms"]
  }}
}}

IMPORTANT RULES:
- For verbs: lemma is first person singular present indicative
- For nouns/adjectives: lemma is nominative singular
- Include principal parts for verbs: present, infinitive, perfect, supine
- Include key forms for nouns: nominative, genitive
- For adjectives, include masculine forms in main fields and feminine/neuter in "forms" object
- Use numerical values for declension/conjugation (1, 2, 3, 4, 5)
- For irregular verbs/nouns, use "irregular" as value
- Return ONLY the JSON object, no additional text or explanations

Word to analyze: {word_form}
"""
}
         

    def process(self, pattern_data, model, stream, original_data):
        """Process Latin analysis patterns"""
        pattern = pattern_data['pattern']
        
        if pattern == 'latin_analysis':
            return self._analyze_latin_word(pattern_data, model, stream, original_data)
        else:
            return jsonify({"error": f"Unsupported Latin pattern: {pattern}"}), 400
    
    def _analyze_latin_word(self, pattern_data, model, stream, original_data):
        """Analyze a Latin word form and provide complete morphological analysis"""
        word_form = pattern_data.get('word_form', '')
        
        if not word_form:
            return jsonify({"error": "word_form is required for latin_analysis pattern"}), 400
        
        # Clean the word form
        word_form = word_form.strip()
        
        prompt = self.prompt_templates['latin_analysis'].format(
            word_form=word_form
        )
        
        return self._call_ai_provider(prompt, model, stream, original_data)
    
    def _call_ai_provider(self, prompt, model, stream, original_data):
        """Call AI provider and format response"""
        try:
            logger.info(f"AI Provider type: {type(self.ai_provider)}")
            logger.info(f"AI Provider methods: {dir(self.ai_provider)}")

            options = {
                "temperature": original_data.get('temperature', 0.1),
                "top_p": original_data.get('top_p', 0.9),
                "max_tokens": original_data.get('max_tokens', 4096)
            }
            
            messages = [{"role": "user", "content": prompt}]
            
            logger.info("=== LATIN ANALYSIS PROMPT ===")
            logger.info(prompt)
            logger.info("=== END PROMPT ===")
            
            # Use the AI provider's OpenAI-compatible interface
            response = self.ai_provider.generate_openai_compatible(
                messages, model, stream=stream, **options
            )
            
            logger.info(f"Stream mode: {stream}, AI Provider response type: {type(response)}")
            if not stream:
                logger.info(f"AI Provider response content (first 500 chars): {str(response)[:500]}")
            else:
                logger.info(f"Streaming response received, will process line by line")
            
            if stream:
                logger.info("Formatting streaming response...")
                result = self._format_streaming_response(response, model)
                logger.info("Streaming response formatted successfully")
                return result
            else:
                logger.info("Formatting non-streaming response...")
                result = self._format_openai_response(response, model)
                logger.info("Non-streaming response formatted successfully")
                return result
                
        except Exception as e:
            logger.error(f"Latin analysis failed: {str(e)}", exc_info=True)
            return jsonify({"error": f"Latin analysis failed: {str(e)}"}), 500
    
    def _format_streaming_response(self, response, model):
        """Format streaming response in OpenAI-compatible format"""
        def generate():
            for line in response:
                if line:
                    try:
                        if isinstance(line, bytes):
                            line = line.decode('utf-8')
                        
                        # Skip empty lines
                        if not line.strip():
                            continue
                        
                        # Parse JSON line (Ollama /api/chat returns raw JSON lines)
                        try:
                            data = json.loads(line)
                            
                            # Ollama /api/chat format: {"message": {"content": "...", "role": "assistant"}, "done": false}
                            if 'message' in data:
                                content = data['message'].get('content', '')
                                done = data.get('done', False)
                                if content:
                                    chunk = {
                                        'id': f'chatcmpl-{int(time.time())}',
                                        'object': 'chat.completion.chunk',
                                        'created': int(time.time()),
                                        'model': model,
                                        'choices': [{
                                            'index': 0,
                                            'delta': {'content': content},
                                            'finish_reason': 'stop' if done else None
                                        }]
                                    }
                                    yield f"data: {json.dumps(chunk)}\n\n"
                                if done:
                                    break
                            # OpenAI format: {"choices": [...]}
                            elif 'choices' in data and data['choices']:
                                content = data['choices'][0].get('delta', {}).get('content', '')
                                if content:
                                    chunk = {
                                        'id': f'chatcmpl-{int(time.time())}',
                                        'object': 'chat.completion.chunk',
                                        'created': int(time.time()),
                                        'model': model,
                                        'choices': [{
                                            'index': 0,
                                            'delta': {'content': content},
                                            'finish_reason': None
                                        }]
                                    }
                                    yield f"data: {json.dumps(chunk)}\n\n"
                            # Ollama /api/generate format (backward compatibility): {"response": "..."}
                            elif 'response' in data:
                                content = data.get('response', '')
                                if content:
                                    chunk = {
                                        'id': f'chatcmpl-{int(time.time())}',
                                        'object': 'chat.completion.chunk',
                                        'created': int(time.time()),
                                        'model': model,
                                        'choices': [{
                                            'index': 0,
                                            'delta': {'content': content},
                                            'finish_reason': None
                                        }]
                                    }
                                    yield f"data: {json.dumps(chunk)}\n\n"
                        except json.JSONDecodeError:
                            # Try SSE format (data: {...})
                            if line.startswith('data: '):
                                try:
                                    data = json.loads(line[6:])
                                    if 'choices' in data and data['choices']:
                                        content = data['choices'][0].get('delta', {}).get('content', '')
                                        if content:
                                            chunk = {
                                                'id': f'chatcmpl-{int(time.time())}',
                                                'object': 'chat.completion.chunk',
                                                'created': int(time.time()),
                                                'model': model,
                                                'choices': [{
                                                    'index': 0,
                                                    'delta': {'content': content},
                                                    'finish_reason': None
                                                }]
                                            }
                                            yield f"data: {json.dumps(chunk)}\n\n"
                                except json.JSONDecodeError:
                                    continue

                    except (json.JSONDecodeError, Exception) as e:
                        logger.debug(f"Error processing stream line: {e}")
                        continue
            
            # Send final done chunk
            final_chunk = {
                'id': f'chatcmpl-{int(time.time())}',
                'object': 'chat.completion.chunk',
                'created': int(time.time()),
                'model': model,
                'choices': [{
                    'index': 0,
                    'delta': {},
                    'finish_reason': 'stop'
                }]
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
    
    def _format_openai_response(self, response, model):
        """Format non-streaming response in OpenAI-compatible format"""
        try:
            # Log the raw response for debugging
            logger.info(f"Raw response type: {type(response)}, hasattr get: {hasattr(response, 'get')}")
            if hasattr(response, 'get'):
                logger.info(f"Response keys: {list(response.keys()) if isinstance(response, dict) else 'not a dict'}")
            
            # Handle different response formats
            content = None
            
            # OpenAI format: {"choices": [{"message": {"content": "..."}}]}
            if isinstance(response, dict) and 'choices' in response:
                content = response["choices"][0]["message"]["content"]
            # Ollama /api/chat format: {"message": {"content": "...", "role": "assistant"}}
            elif isinstance(response, dict) and 'message' in response:
                message = response["message"]
                if isinstance(message, dict):
                    content = message.get("content", "")
                else:
                    content = str(message)
            # Ollama /api/generate format (backward compatibility): {"response": "..."}
            elif isinstance(response, dict) and 'response' in response:
                content = response["response"]
            else:
                # Try to extract content from any format
                logger.warning(f"Unexpected response format: {type(response)} - {response}")
                content = str(response)
            
            logger.info("=== LATIN ANALYSIS RESPONSE ===")
            logger.info(content[:500] + "..." if len(content) > 500 else content)
            logger.info("=== END RESPONSE ===")
            
            return jsonify({
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant", 
                        "content": content
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            })
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            return jsonify({"error": f"Error formatting response: {str(e)}"}), 500

    def health_check(self):
        """
        Health check endpoint implementation
        Matches the CodeProcessor pattern
        """
        try:
            # For now, just check if we can create a provider
            # You might want to add actual health checks per provider later
            provider_type = self.config.get("AI_PROVIDER", "ollama")
            
            return jsonify({
                "status": "healthy",
                "ai_provider": provider_type,
                "default_model": self.default_model,
                "provider_connected": True,  # Basic check for now
                "processor": "latin_processor",
                "supported_patterns": ["latin_analysis"]
            })
            
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "ai_provider": self.config.get("AI_PROVIDER", "unknown"),
                "error": str(e),
                "processor": "latin_processor"
            }), 500

    def get_processor_info(self):
        """
        Get information about the latin processor
        Matches the CodeProcessor pattern
        """
        return {
            "name": "AI Latin Processor",
            "version": "1.0.0",
            "default_model": self.default_model,
            "supported_patterns": ["latin_analysis"],
            "ai_provider": self.config.get("AI_PROVIDER", "ollama"),
            "max_tokens": 4096,
            "default_temperature": 0.1
        }