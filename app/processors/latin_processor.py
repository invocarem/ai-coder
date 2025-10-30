# app/processors/latin_processor.py
import logging
import re
from flask import jsonify, Response
import json
import time

logger = logging.getLogger(__name__)

class LatinProcessor:
    """Handles Latin word analysis with morphological parsing and lemma identification"""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        
        self.prompt_templates = {
            "latin_analysis": """
Analyze the Latin word: **{word_form}**

Please provide a COMPLETE morphological analysis following this EXACT structure:

**LEMMA:** [dictionary form]
**PART OF SPEECH:** [verb/noun/adjective/adverb/conjunction/preposition/pronoun]
**MEANING:** [primary English translation]

**GRAMMATICAL ANALYSIS:**
- **Lemma:** [prsent for verb, nominative singular for noun/adjective]
- **Case:** [nominative/genitive/dative/accusative/ablative/vocative/locative - if applicable]
- **Number:** [singular/plural - if applicable]  
- **Gender:** [masculine/feminine/neuter - if applicable]
- **Tense:** [present/imperfect/future/perfect/pluperfect/future perfect - if verb]
- **Mood:** [indicative/subjunctive/imperative/infinitive/participle/gerund/gerundive/supine - if verb]
- **Voice:** [active/passive/deponent - if verb]
- **Person:** [1st/2nd/3rd - if verb]
- **Degree:** [positive/comparative/superlative - if adjective/adverb]

**PRINCIPAL PARTS:** [only for verbs - present indicative, present infinitive, perfect indicative, supine]
**DECLENSION/CONJUGATION:** [1st/2nd/3rd/4th/mixed/irregular]

**FULL FORM PARADIGM:**
[Provide the complete conjugation or declension table]

**ETYMOLOGY:** [brief origin information if known]
**USAGE EXAMPLES:**
1. [Latin example sentence] - "[English translation]"
2. [Latin example sentence] - "[English translation]"

**RELATED WORDS:**
- [related word 1]: [meaning]
- [related word 2]: [meaning]

**NOTES:** [any special grammatical notes or irregularities]

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
            options = {
                "temperature": original_data.get('temperature', 0.1),
                "top_p": original_data.get('top_p', 0.9),
                "max_tokens": original_data.get('max_tokens', 4096)
            }
            
            messages = [{"role": "user", "content": prompt}]
            
            logger.info("=== LATIN ANALYSIS PROMPT ===")
            logger.info(prompt)
            logger.info("=== END PROMPT ===")
            
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
            logger.error(f"Latin analysis failed: {str(e)}")
            return jsonify({"error": f"Latin analysis failed: {str(e)}"}), 500
    
    def _format_streaming_response(self, response, model):
        """Format streaming response in OpenAI-compatible format"""
        def generate():
            for line in response:
                if line:
                    try:
                        if isinstance(line, bytes):
                            line = line.decode('utf-8')
                        
                        if line.startswith('data: '):
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
                        else:
                            data = json.loads(line)
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
            if hasattr(response, 'get') and 'choices' in response:
                content = response["choices"][0]["message"]["content"]
            elif hasattr(response, 'get') and 'response' in response:
                content = response["response"]
            else:
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
        """Health check for Latin processor"""
        return jsonify({
            "status": "healthy",
            "processor": "latin_processor",
            "supported_patterns": ["latin_analysis"]
        })