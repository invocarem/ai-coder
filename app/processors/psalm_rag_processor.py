# app/processors/psalm_rag_processor.py
import logging
import json
import time
from flask import jsonify, Response
from app.rag.simple_cassandra_client import SimpleCassandraClient

logger = logging.getLogger(__name__)

class PsalmRAGProcessor:
    """RAG processor for Psalms and Augustine commentaries"""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        self.db = SimpleCassandraClient()
        
        self.prompt_templates = {
            "psalm_query": """
You are a theological research assistant specializing in St. Augustine's expositions on the Psalms.

CONTEXT FROM BIBLE AND AUGUSTINE'S WRITINGS:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
1. Base your answer STRICTLY on the provided context
2. Cite specific Augustine works and Psalm verses when possible
3. Focus on Augustine's unique interpretations
4. Provide both Latin terms and English explanations when available
5. If the context doesn't contain relevant information, say so clearly

ANSWER:
""",
            "word_analysis": """
Analyze the Latin word **{word_form}** in the context of Psalm {psalm_number}.

CONTEXT:
{context}

WORD ANALYSIS REQUEST: {question}

Provide:
1. Grammatical analysis of the word
2. Augustine's interpretation if available
3. Theological significance in the Psalm context
4. Related concepts in Augustine's thought

ANSWER:
"""
        }

    def process(self, pattern_data, model, stream, original_data):
        """Process Psalm RAG patterns"""
        pattern = pattern_data['pattern']
        
        if pattern == 'psalm_query':
            return self._query_psalms(pattern_data, model, stream, original_data)
        elif pattern == 'psalm_word_analysis':
            return self._analyze_psalm_word(pattern_data, model, stream, original_data)
        else:
            return jsonify({"error": f"Unsupported Psalm RAG pattern: {pattern}"}), 400
    
    def _query_psalms(self, pattern_data, model, stream, original_data):
        """Query Psalms with Augustine commentary"""
        psalm_number = pattern_data.get('psalm_number')
        verse_number = pattern_data.get('verse_number')
        question = pattern_data.get('question', '')
        
        if not psalm_number:
            return jsonify({"error": "psalm_number is required for psalm_query pattern"}), 400
        
        # Build context from database
        context = self._build_psalm_context(psalm_number, verse_number)
        
        # Build the question if not provided
        if not question:
            if verse_number:
                question = f"Explain Psalm {psalm_number}:{verse_number} and Augustine's interpretation"
            else:
                question = f"Explain Psalm {psalm_number} and Augustine's interpretation"
        
        prompt = self.prompt_templates['psalm_query'].format(
            context=context,
            question=question
        )
        
        return self._call_ai_provider(prompt, model, stream, original_data, context)
    
    def _analyze_psalm_word(self, pattern_data, model, stream, original_data):
        """Analyze specific words in Psalms with Augustine's interpretation"""
        word_form = pattern_data.get('word_form')
        psalm_number = pattern_data.get('psalm_number')
        verse_number = pattern_data.get('verse_number')
        question = pattern_data.get('question', '')
        
        if not all([word_form, psalm_number]):
            return jsonify({"error": "word_form and psalm_number are required for psalm_word_analysis pattern"}), 400
        
        # Build context
        context = self._build_psalm_context(psalm_number, verse_number)
        
        # Build question if not provided
        if not question:
            location = f"Psalm {psalm_number}" + (f":{verse_number}" if verse_number else "")
            question = f"Analyze the word '{word_form}' in {location}"
        
        prompt = self.prompt_templates['word_analysis'].format(
            word_form=word_form,
            psalm_number=psalm_number,
            context=context,
            question=question
        )
        
        return self._call_ai_provider(prompt, model, stream, original_data, context)
    
    def _build_psalm_context(self, psalm_number, verse_number=None):
        """Build context from Cassandra database"""
        context_parts = []
        
        # Get Psalm verses
        if verse_number:
            # Get specific verse
            verse_result = self.db.get_psalm_verse(psalm_number, verse_number)
            if verse_result:
                context_parts.append(f"PSALM {psalm_number}:{verse_number}")
                context_parts.append(self._format_verse_output(verse_result))
        else:
            # Get all verses for this Psalm (you might want to limit this)
            for v in [1, 2]:  # Just get first 2 verses for now
                verse_result = self.db.get_psalm_verse(psalm_number, v)
                if verse_result:
                    context_parts.append(f"PSALM {psalm_number}:{v}")
                    context_parts.append(self._format_verse_output(verse_result))
        
        # Get Augustine commentaries
        augustine_comments = self.db.get_augustine_comments(psalm_number, verse_number)
        if augustine_comments:
            context_parts.append("\nAUGUSTINE COMMENTARY:")
            context_parts.append(augustine_comments)
        
        return "\n".join(context_parts) if context_parts else "No data found for the specified Psalm."
    
    def _format_verse_output(self, verse_output):
        """Format the verse output from cqlsh"""
        if not verse_output:
            return "No verse data"
        
        # Simple formatting - you can enhance this based on actual cqlsh output format
        lines = verse_output.strip().split('\n')
        if len(lines) > 2:  # If we have data rows
            return "\n".join(lines[-3:])  # Get the last few lines which usually contain the data
        return verse_output
    
    def _call_ai_provider(self, prompt, model, stream, original_data, context):
        """Call AI provider and format response"""
        try:
            options = {
                "temperature": original_data.get('temperature', 0.1),
                "top_p": original_data.get('top_p', 0.9),
                "max_tokens": original_data.get('max_tokens', 2000)
            }
            
            messages = [{"role": "user", "content": prompt}]
            
            logger.info("=== PSALM RAG PROMPT ===")
            logger.info(f"Context length: {len(context)} characters")
            logger.info(f"Prompt preview: {prompt[:200]}...")
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
                return self._format_response(response, model, context)
                
        except Exception as e:
            logger.error(f"Psalm RAG query failed: {str(e)}")
            return jsonify({"error": f"Psalm RAG query failed: {str(e)}"}), 500

                
    def _format_streaming_response(self, response, model):
        """Format streaming response"""
        def generate():
            try:
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
                                        # Fix: Use proper dictionary for multi-line
                                        chunk_data = {
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
                                        yield f"data: {json.dumps(chunk_data)}\n\n"
                            else:
                                # Handle other response formats
                                data = json.loads(line)
                                content = data.get('response', '')
                                if content:
                                    chunk_data = {
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
                                    yield f"data: {json.dumps(chunk_data)}\n\n"
                        except (json.JSONDecodeError, Exception) as e:
                            logger.debug(f"Error processing stream line: {e}")
                            continue
                
                # Send final done chunk - FIX THIS PART
                done_chunk = {
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
                yield f"data: {json.dumps(done_chunk)}\n\n"
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                error_chunk = {
                    'error': str(e)
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
    
    
    
    def _format_response(self, response, model, context):
        """Format non-streaming response"""
        try:
            if hasattr(response, 'get') and 'choices' in response:
                content = response["choices"][0]["message"]["content"]
            elif hasattr(response, 'get') and 'response' in response:
                content = response["response"]
            else:
                content = str(response)
            
            logger.info("=== PSALM RAG RESPONSE ===")
            logger.info(content[:500] + "..." if len(content) > 500 else content)
            logger.info("=== END RESPONSE ===")
            
            response_data = {
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
            }
            
            # Add RAG metadata
            response_data["rag_metadata"] = {
                "context_preview": context[:300] + "..." if len(context) > 300 else context,
                "source": "cassandra_psalms_db"
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            return jsonify({"error": f"Error formatting response: {str(e)}"}), 500

    def health_check(self):
        """Health check for Psalm RAG processor"""
        db_status = self.db.health_check()
        return jsonify({
            "status": "healthy",
            "processor": "psalm_rag_processor",
            "supported_patterns": ["psalm_query", "psalm_word_analysis"],
            "database": db_status
        })