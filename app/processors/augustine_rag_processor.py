# app/processors/augustine_rag_processor.py
import logging
import json
import time
from flask import jsonify, Response
from app.rag.simple_cassandra_client import SimpleCassandraClient
from app.rag.retriever import AugustineRetriever

logger = logging.getLogger(__name__)

class AugustineRAGProcessor:
    """Handles Augustine-specific RAG queries about Psalms"""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        self.cassandra_client = SimpleCassandraClient()
        self.retriever = AugustineRetriever(self.cassandra_client)
        
        self.prompt_templates = {
            "augustine_psalms": """
You are a specialized assistant for St. Augustine's expositions on the Psalms.

CONTEXT FROM AUGUSTINE'S WRITINGS:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
1. Base your answer STRICTLY on the provided Augustine context
2. Cite specific works and Psalm verses
3. Focus on Augustine's unique theological insights
4. Provide both Latin terms and English explanations
5. If context doesn't contain relevant information, say so clearly

ANSWER:
""",
            "psalm_word_study": """
Analyze the Latin word **{word_form}** in Psalm {psalm_number}:{verse_number} 
according to St. Augustine's exposition.

AUGUSTINE'S CONTEXT:
{context}

WORD ANALYSIS REQUEST: {question}

Provide:
1. Augustine's specific interpretation of this word
2. Theological significance in the Psalm context
3. Related concepts in Augustine's thought
4. Latin grammatical notes if relevant

ANSWER:
"""
        }

    def process(self, pattern_data, model, stream, original_data):
        """Process Augustine RAG patterns"""
        pattern = pattern_data['pattern']
        
        if pattern == 'augustine_psalm_query':
            return self._query_augustine_psalms(pattern_data, model, stream, original_data)
        elif pattern == 'psalm_word_study':
            return self._psalm_word_study(pattern_data, model, stream, original_data)
        else:
            return jsonify({"error": f"Unsupported Augustine RAG pattern: {pattern}"}), 400
    
    def _query_augustine_psalms(self, pattern_data, model, stream, original_data):
        """Query Augustine's expositions on specific Psalms"""
        psalm_number = pattern_data.get('psalm_number')
        verse_number = pattern_data.get('verse_number')
        question = pattern_data.get('question', '')
        
        if not psalm_number:
            return jsonify({"error": "psalm_number is required for augustine_psalm_query"}), 400
        
        # Build context from database using SimpleCassandraClient
        context = self._build_augustine_context(psalm_number, verse_number)
        
        prompt = self.prompt_templates['augustine_psalms'].format(
            context=context,
            question=question or f"Explain Augustine's interpretation of Psalm {psalm_number}" + 
                              (f":{verse_number}" if verse_number else "")
        )
        
        return self._call_ai_provider(prompt, model, stream, original_data, context)
    
    def _psalm_word_study(self, pattern_data, model, stream, original_data):
        """Study specific words in Psalms with Augustine's interpretation"""
        word_form = pattern_data.get('word_form')
        psalm_number = pattern_data.get('psalm_number')
        verse_number = pattern_data.get('verse_number')
        
        if not all([word_form, psalm_number]):
            return jsonify({"error": "word_form and psalm_number are required for psalm_word_study"}), 400
        
        # Build context using SimpleCassandraClient
        context = self._build_augustine_context(psalm_number, verse_number, word_form)
        
        question = f"Augustine's interpretation of '{word_form}' in Psalm {psalm_number}" + \
                  (f":{verse_number}" if verse_number else "")
        
        prompt = self.prompt_templates['psalm_word_study'].format(
            word_form=word_form,
            psalm_number=psalm_number,
            verse_number=verse_number or "N/A",
            context=context,
            question=question
        )
        
        return self._call_ai_provider(prompt, model, stream, original_data, context)
    
    def _build_augustine_context(self, psalm_number, verse_number=None, word_form=None):
        """Build context from Cassandra database using SimpleCassandraClient"""
        context_parts = []
        
        # Get Augustine commentaries
        augustine_comments = self.cassandra_client.get_augustine_comments(psalm_number, verse_number)
        
        if augustine_comments:
            context_parts.append("AUGUSTINE COMMENTARY:")
            for comment in augustine_comments:
                context_parts.append(f"Work: {comment.get('work_title', 'Unknown')}")
                if verse_number:
                    context_parts.append(f"Verses: {comment.get('verse_start', 'N/A')}-{comment.get('verse_end', 'N/A')}")
                context_parts.append(f"Latin: {comment.get('latin_text', '')}")
                context_parts.append(f"English: {comment.get('english_translation', '')}")
                if comment.get('key_terms'):
                    context_parts.append(f"Key Terms: {', '.join(comment.get('key_terms', []))}")
                context_parts.append("---")
        
        # Get Psalm verses if available
        if verse_number:
            verse_result = self.cassandra_client.get_psalm_verse(psalm_number, verse_number)
            if verse_result:
                context_parts.append(f"PSALM {psalm_number}:{verse_number}")
                context_parts.append(f"Latin: {verse_result.get('latin_text', '')}")
                context_parts.append(f"English: {verse_result.get('english_translation', '')}")
                if verse_result.get('grammatical_notes'):
                    context_parts.append(f"Grammar: {verse_result.get('grammatical_notes', '')}")
        
        # Filter by word if specified
        if word_form and context_parts:
            word_context = []
            for part in context_parts:
                if word_form.lower() in part.lower():
                    word_context.append(part)
            if word_context:
                return "\n".join(word_context)
        
        return "\n".join(context_parts) if context_parts else "No Augustine commentary found for the specified Psalm."
    
    def _call_ai_provider(self, prompt, model, stream, original_data, context=None):
        """Call AI provider with RAG context"""
        try:
            options = {
                "temperature": original_data.get('temperature', 0.1),
                "top_p": original_data.get('top_p', 0.9),
                "max_tokens": original_data.get('max_tokens', 4096)
            }
            
            messages = [{"role": "user", "content": prompt}]
            
            logger.info("=== AUGUSTINE RAG PROMPT ===")
            logger.info(f"Context length: {len(context) if context else 0} characters")
            logger.info(f"Prompt preview: {prompt[:200]}...")
            logger.info("=== END PROMPT ===")
            
            if stream:
                response = self.ai_provider.generate_openai_compatible(
                    messages, model, stream=True, **options
                )
                return self._format_streaming_response(response, model, context)
            else:
                response = self.ai_provider.generate_openai_compatible(
                    messages, model, stream=False, **options
                )
                return self._format_openai_response(response, model, context)
                
        except Exception as e:
            logger.error(f"Augustine RAG failed: {str(e)}")
            return jsonify({"error": f"Augustine RAG failed: {str(e)}"}), 500
    
    def _format_streaming_response(self, response, model, context):
        """Format streaming response using similar logic to psalm_rag_processor"""
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
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
    
    def _format_openai_response(self, response, model, context):
        """Format response with RAG metadata"""
        try:
            if hasattr(response, 'get') and 'choices' in response:
                content = response["choices"][0]["message"]["content"]
            elif hasattr(response, 'get') and 'response' in response:
                content = response["response"]
            else:
                content = str(response)
            
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
            if context:
                response_data["rag_metadata"] = {
                    "context_preview": context[:500] + "..." if len(context) > 500 else context,
                    "sources_used": len(context.split('\n\n')),  # Approximate chunk count
                    "source": "cassandra_augustine_commentaries"
                }
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Error formatting RAG response: {str(e)}")
            return jsonify({"error": f"Error formatting RAG response: {str(e)}"}), 500

    def health_check(self):
        """Health check for Augustine RAG processor"""
        cassandra_status = self.cassandra_client.health_check()
        return jsonify({
            "status": "healthy",
            "processor": "augustine_rag_processor",
            "supported_patterns": ["augustine_psalm_query", "psalm_word_study"],
            "cassandra": cassandra_status
        })