# app/processors/psalm_rag_processor.py
import logging
import json
import time
from app.core.config import load_config
from app.rag.simple_cassandra_client import SimpleCassandraClient
from app.rag.retriever import AugustineRetriever  # Updated!

logger = logging.getLogger(__name__)

class PsalmRAGProcessor:
    """Single RAG processor using intelligent retriever"""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        self.config = load_config()
        cassandra_host = self.config.get("CASSANDRA_HOSTS", "127.0.0.1")
        cassandra_port = self.config.get("CASSANDRA_PORT", 9042)
        self.cassandra_client = SimpleCassandraClient(host=cassandra_host, port=cassandra_port)
        self.retriever = AugustineRetriever(self.cassandra_client)  # Use enhanced retriever!
        
        self.prompt_templates = {
            "augustine_psalm_query": """
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
        """Process all Psalm RAG patterns using intelligent retriever"""
        try:
            pattern = pattern_data['pattern']
            
            logger.info(f"🔍 DEBUG Processing pattern: {pattern}")
            logger.info(f"🔍 DEBUG Available patterns: {list(self.prompt_templates.keys())}")

            if pattern in ['psalm_query', 'augustine_psalm_query']:
                logger.info(f"🔍 DEBUG Routing to _query_psalms with pattern: {pattern}")
                return self._query_psalms(pattern_data, model, stream, original_data)
            elif pattern == 'psalm_word_analysis':
                logger.info(f"🔍 DEBUG Routing to _analyze_psalm_word with pattern: {pattern}")
                return self._analyze_psalm_word(pattern_data, model, stream, original_data)
            else:
                logger.error(f"❌ Unsupported pattern: {pattern}")
                return {"error": f"Unsupported pattern: {pattern}"}, 400
        except Exception as e:
            logger.error(f"❌ Processor failed in process method: {str(e)}")
            logger.error(f"❌ Pattern data: {pattern_data}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return {"error": f"Processor error: {str(e)}"}, 500
    

    def _query_psalms(self, pattern_data, model, stream, original_data):
        """Query using intelligent retriever"""
        try:
            psalm_number = pattern_data.get('psalm_number')
            verse_number = pattern_data.get('verse_number') 
            question = pattern_data.get('question', '')
            pattern = pattern_data.get('pattern', 'psalm_query')  # This is the actual pattern
            
            logger.info(f"🔍 DEBUG _query_psalms received pattern: {pattern}")
            logger.info(f"🔍 DEBUG Available prompt templates: {list(self.prompt_templates.keys())}")
            
            if not psalm_number:
                return {"error": "psalm_number is required"}, 400
            
            # CONVERT TYPES
            try:
                psalm_number = int(psalm_number)
                if verse_number:
                    verse_number = int(verse_number)
            except (ValueError, TypeError) as e:
                logger.error(f"Type conversion error in processor: {e}")
                return {"error": f"Invalid number format: {e}"}, 400
            
            # USE INTELLIGENT RETRIEVER
            context = self.retriever.retrieve_relevant_context(question, psalm_number, verse_number)
            
            if not question:
                if verse_number:
                    question = f"Explain Psalm {psalm_number}:{verse_number} and Augustine's interpretation"
                else:
                    question = f"Explain Psalm {psalm_number} and Augustine's interpretation"
            
            # FIX: Use the actual pattern variable, not hardcoded 'psalm_query'
            prompt_template = self.prompt_templates.get(pattern)
            if not prompt_template:
                logger.warning(f"Pattern {pattern} not found in templates, available: {list(self.prompt_templates.keys())}")
                # Try fallback to psalm_query if augustine_psalm_query not found
                if pattern == 'augustine_psalm_query':
                    prompt_template = self.prompt_templates.get('psalm_query')
            if not prompt_template:
                logger.error(f"No suitable prompt template found for pattern: {pattern}")
                return {"error": f"No prompt template for pattern: {pattern}"}, 500
            
            logger.info(f"🔍 DEBUG Using prompt template for pattern: {pattern}")
            
            # FIX: Use the dynamic prompt_template variable
            prompt = prompt_template.format(context=context, question=question)
            
            return self._call_ai_provider(prompt, model, stream, original_data, context)
            
        except Exception as e:
            logger.error(f"❌ _query_psalms failed: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return {"error": f"Query processing failed: {str(e)}"}, 500

        
        
    
    def _analyze_psalm_word(self, pattern_data, model, stream, original_data):
        """Word analysis using intelligent retriever"""
        word_form = pattern_data.get('word_form')
        psalm_number = pattern_data.get('psalm_number')
        verse_number = pattern_data.get('verse_number')
        question = pattern_data.get('question', '')
        
        if not all([word_form, psalm_number]):
            return {"error": "word_form and psalm_number are required"}, 400
        
        # Create a focused question for the retriever
        focused_question = f"analyze the word {word_form} in psalm {psalm_number}"
        if verse_number:
            focused_question += f" verse {verse_number}"
        
        # USE INTELLIGENT RETRIEVER
        context = self.retriever.retrieve_relevant_context(focused_question, psalm_number, verse_number)
        
        if not question:
            location = f"Psalm {psalm_number}" + (f":{verse_number}" if verse_number else "")
            question = f"Analyze the word '{word_form}' in {location}"
        
        prompt = self.prompt_templates['word_analysis'].format(
            word_form=word_form, psalm_number=psalm_number,
            context=context, question=question
        )
        
        return self._call_ai_provider(prompt, model, stream, original_data, context)
    
    def _call_ai_provider(self, prompt, model, stream, original_data, context):
        """Call AI provider with proper streaming handling"""
        try:
            options = {
                "temperature": original_data.get('temperature', 0.1),
                "top_p": original_data.get('top_p', 0.9),
                "max_tokens": original_data.get('max_tokens', 2000)
            }
            
            messages = [{"role": "user", "content": prompt}]
            
            logger.info("=== ENHANCED PSALM RAG PROMPT ===")
            logger.info(f"Context length: {len(context)} characters")
            logger.info(f"Prompt preview: {prompt[:200]}...")
            logger.info("=== END PROMPT ===")
            
            if stream:
                # Make sure we're getting the raw streaming response
                response = self.ai_provider.generate_openai_compatible(
                    messages, model, stream=True, **options
                )
                
                # Log the first few chunks to see what format we're getting
                logger.info("🔍 Checking streaming response format...")
                temp_chunks = []
                for i, chunk in enumerate(response):
                    if i < 3:  # Just check first 3 chunks
                        temp_chunks.append(chunk)
                        logger.info(f"🔍 Chunk {i}: {chunk}")
                    else:
                        break
                
                # Reset the response generator (we need to recreate it)
                response = self.ai_provider.generate_openai_compatible(
                    messages, model, stream=True, **options
                )
                
                return self._format_streaming_response(response, model, context)
            else:
                response = self.ai_provider.generate_openai_compatible(
                    messages, model, stream=False, **options
                )
                return self._format_response(response, model, context)
                
        except Exception as e:
            logger.error(f"Psalm RAG query failed: {str(e)}")
            return {"error": f"Psalm RAG query failed: {str(e)}"}, 500
            
    
    def _format_streaming_response(self, response, model, context):
        """Format streaming response with proper Ollama to OpenAI conversion"""
        def generate():
            try:
                chunk_count = 0
                full_response = ""
                
                for line in response:
                    if line:
                        try:
                            # Decode if it's bytes
                            if isinstance(line, bytes):
                                line = line.decode('utf-8')
                            
                            logger.debug(f"📨 Raw line: {line.strip()}")
                            
                            # Parse the JSON response from Ollama
                            data = json.loads(line)
                            
                            # Extract content from Ollama's format
                            content = ""
                            if 'message' in data and 'content' in data['message']:
                                content = data['message']['content']
                            elif 'response' in data:
                                content = data['response']
                            elif 'content' in data:
                                content = data['content']
                            
                            if content:
                                chunk_count += 1
                                full_response += content
                                logger.info(f"📤 Streaming chunk {chunk_count}: '{content}'")
                                
                                # Format as OpenAI streaming response
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
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON decode error on line: {line}, error: {e}")
                            continue
                        except Exception as e:
                            logger.warning(f"Error processing line: {e}")
                            continue
                
                logger.info(f"✅ Stream completed. Sent {chunk_count} chunks. Full response: {full_response}")
                
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
                error_chunk = {
                    'error': str(e)
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        # Return the generator function directly - the Flask route will handle the Response creation
        return generate()
                    
   
    
    
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
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            return {"error": f"Error formatting response: {str(e)}"}

    def health_check(self):
        """Health check for Psalm RAG processor"""
        db_status = self.cassandra_client.health_check()  # Updated to use cassandra_client
        return {
            "status": "healthy",
            "processor": "psalm_rag_processor",
            "supported_patterns": ["psalm_query", "psalm_word_analysis"],
            "database": db_status
        }
