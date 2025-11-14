# app/processors/code_processor.py
import json
import time
import requests
import logging

from flask import jsonify, Response
from app.utils.pattern_detector import PatternDetector
from app.utils.ai_provider import AIProviderFactory
from app.config import load_config

logger = logging.getLogger(__name__)
stream_logger = logging.getLogger("stream_debug")

class CodeProcessor:
    def __init__(self, ai_provider):
        """Initialize the code processor with configuration and dependencies"""
        self.config = load_config()
        self.pattern_detector = PatternDetector()
        self.ai_provider = ai_provider
        self.default_model = self.config["DEFAULT_MODEL"]

        self.prompt_patterns = {
            "write_code": """Write a {language} function to {task}. Include type hints and docstring. Provide only the code without explanations.
Additional requirements:
- Provide complete, runnable code
- Include comments for key sections
- Use best practices for the specified language
- Handle edge cases and error checking
- Include example usage if applicable
            """,
            
            "fix_bug": "Fix this {language} code: ```{language}\n{code}\n```. The issue is: {issue}.{rules_section}Provide the fixed code with comments explaining the changes.",
            
            "improve_code": "Improve this {language} code: ```{language}\n{code}\n```. The issue is: {issue}.{rules_section}Provide the improved code with comments explaining the changes.",
            
            "explain_code": "Explain how this {language} code works: ```{language}\n{code}\n```. Provide a clear explanation of what the code does, how it works, and any important details.",
            
            "refactor_code": "Refactor this {language} code for better readability and performance: ```{language}\n{code}\n```. Provide the refactored code with comments explaining the improvements.",
            
            "write_tests": "Write comprehensive unit tests for this {language} function: ```{language}\n{code}\n```. Include test cases for edge cases and normal scenarios.",
            
            "add_docs": "Add detailed docstring and comments to this {language} code: ```{language}\n{code}\n```. Provide the documented code with clear explanations.",
            
            "custom": """{prompt}"""

                    } 

    def process(self, pattern_data, model, stream, original_data):
        """
        Process method for router compatibility
        """
        try:
            # Use the existing pattern handling logic
            return self._handle_pattern_request(pattern_data, model, stream, original_data)
        except Exception as e:
            logger.error(f"Code processor failed: {str(e)}")
            return jsonify({"error": f"Code processor failed: {str(e)}"}), 500


    def generate_code(self, data):
        """
        Process code generation requests based on patterns
        
        Args:
            data (dict): Request data containing pattern, language, code, task, etc.
            
        Returns:
            Flask Response: JSON response with generated code or error
        """
        try:
            # Extract parameters with defaults
            pattern = data.get('pattern', 'custom')
            language = data.get('language', 'Python')
            code = data.get('code', '')
            task = data.get('task', '')
            issue = data.get('issue', '')
            prompt = data.get('prompt', '')
            model = data.get('model', self.default_model)
            stream = data.get('stream', False)

            # Validate required fields based on pattern
            validation_error = self._validate_pattern_data(pattern, language, code, task, prompt)
            if validation_error:
                return validation_error

            # Fill the prompt template
            if pattern == "custom":
                if not prompt:
                    return jsonify({"error": "Custom prompt is required for 'custom' pattern"}), 400
                filled_prompt = prompt
            else:
                filled_prompt = self.prompt_patterns[pattern].format(
                    language=language, 
                    code=code, 
                    task=task, 
                    issue=issue
                )

            # Prepare parameters for AI provider
            options = {
                "temperature": data.get('temperature', 0.1),
                "top_p": data.get('top_p', 0.9),
                "max_tokens": data.get('max_tokens', self.config.get("MAX_TOKENS", 4096))
            }

            # DEBUG: Log the messages being sent
            messages = [{"role": "user", "content": filled_prompt}]
            logger.debug("=== MESSAGES SENT TO AI ===")
            logger.debug(json.dumps(messages, indent=2))
            logger.debug("=== END MESSAGES ===")

            if stream:
                # Handle streaming response using OpenAI-compatible format
                messages = [{"role": "user", "content": filled_prompt}]
                response = self.ai_provider.generate_openai_compatible(messages, model, stream=True, **options)
                return self._format_streaming_response(response, model)
            else:
                # Handle non-streaming response
                messages = [{"role": "user", "content": filled_prompt}]
                response = self.ai_provider.generate_openai_compatible(messages, model, stream=False, **options)
                
                # Extract response based on provider
                if hasattr(response, 'get') and 'choices' in response:  # OpenAI format
                    text = response["choices"][0]["message"]["content"]
                elif hasattr(response, 'get') and 'response' in response:  # Ollama format
                    text = response["response"]
                else:
                    text = str(response)
                    
                return Response(
                    json.dumps({"text": text}),
                    mimetype='application/json; charset=utf-8'
                )            
                
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"AI provider connection error: {str(e)}"}), 503
        except Exception as e:
            return jsonify({"error": f"Code generation failed: {str(e)}"}), 500

    def _format_streaming_response(self, response, model):
        """Format streaming response in OpenAI-compatible format"""
        def generate():
            error_message = None
            content_emitted = False
            should_log_stream = bool(stream_logger.handlers) and stream_logger.isEnabledFor(logging.INFO)
            collected_chunks = [] if should_log_stream else None
            try:
                for line in response:
                    if line:
                        try:
                            # Decode bytes to string if needed
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
                                        if should_log_stream:
                                            collected_chunks.append(content)
                                        content_emitted = True
                                        chunk_data = {
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
                                        yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                                    if done:
                                        break
                                # OpenAI format: {"choices": [...]}
                                elif 'choices' in data and data['choices']:
                                    content = data['choices'][0].get('delta', {}).get('content', '')
                                    if content:
                                        if should_log_stream:
                                            collected_chunks.append(content)
                                        content_emitted = True
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
                                        yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                                # Ollama /api/generate format (backward compatibility): {"response": "..."}
                                elif 'response' in data:
                                    content = data.get('response', '')
                                    if content:
                                        if should_log_stream:
                                            collected_chunks.append(content)
                                        content_emitted = True
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
                                        yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                            except json.JSONDecodeError:
                                # Try SSE format (data: {...})
                                if line.startswith('data: '):
                                    try:
                                        data = json.loads(line[6:])
                                        if 'choices' in data and data['choices']:
                                            content = data['choices'][0].get('delta', {}).get('content', '')
                                            if content:
                                                if should_log_stream:
                                                    collected_chunks.append(content)
                                                content_emitted = True
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
                                                yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                                    except json.JSONDecodeError:
                                        continue
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.debug(f"Error processing stream line: {e}")
                            continue
            except requests.exceptions.ReadTimeout as exc:
                logger.warning("Upstream code stream timed out: %s", exc)
                error_message = "Upstream stream timed out"
            except requests.exceptions.RequestException as exc:
                logger.error("Upstream code stream failed: %s", exc, exc_info=True)
                error_message = "Upstream stream failed"
            except Exception as exc:
                logger.error("Unexpected streaming error: %s", exc, exc_info=True)
                error_message = str(exc)

            if error_message:
                error_chunk = {
                    'id': f'chatcmpl-{int(time.time())}',
                    'object': 'chat.completion.chunk',
                    'created': int(time.time()),
                    'model': model,
                    'choices': [{
                        'index': 0,
                        'delta': {'content': f"[server-error] {error_message}"},
                        'finish_reason': None
                    }]
                }
                yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
                if should_log_stream:
                    stream_logger.info("Streaming error emitted: %s", error_message)
            elif not content_emitted:
                warning_chunk = {
                    'id': f'chatcmpl-{int(time.time())}',
                    'object': 'chat.completion.chunk',
                    'created': int(time.time()),
                    'model': model,
                    'choices': [{
                        'index': 0,
                        'delta': {'content': "[server-warning] Upstream returned no content"},
                        'finish_reason': None
                    }]
                }
                yield f"data: {json.dumps(warning_chunk, ensure_ascii=False)}\n\n"
                if should_log_stream:
                    stream_logger.info("Streaming warning: upstream returned no content")
            elif should_log_stream and collected_chunks:
                merged = "".join(collected_chunks)
                preview = merged[:5000]
                stream_logger.info("Streaming response captured (%d chars)", len(merged))
                if preview:
                    stream_logger.info("Streaming preview: %s%s", preview, "..." if len(merged) > len(preview) else "")

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
            yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"


        logger.debug(
            "Returning SSE response with explicit charset (text/event-stream; charset=utf-8)"
        )
        return Response(
            generate(), 
            mimetype='text/event-stream;charset=utf-8',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'                 # disable proxy buffering
            }
        )

    def _validate_pattern_data(self, pattern, language, code, task, prompt):
        """
        Validate required data for each pattern
        
        Args:
            pattern (str): The pattern type
            language (str): Programming language
            code (str): Code content
            task (str): Task description
            prompt (str): Custom prompt
            
        Returns:
            Flask Response or None: Error response if validation fails, None if valid
        """
        # Validate language for non-custom patterns
        if pattern != "custom" and not language:
            return jsonify({"error": "Language is required"}), 400
            
        # Pattern-specific validations
        if pattern == "write_code":
            if not task:
                return jsonify({"error": "Task description is required"}), 400
                
        elif pattern in ["fix_bug", "explain_code", "refactor_code", "write_tests", "add_docs"]:
            if not code:
                return jsonify({"error": f"Code is required"}), 400
                
        elif pattern == "custom":
            if not prompt:
                return jsonify({"error": "Prompt is required for custom pattern"}), 400
                
        return None

    def chat_completions(self, data):
        """
        Handle OpenAI-compatible chat completions with pattern detection
        
        Args:
            data (dict): OpenAI-compatible request data
            
        Returns:
            Flask Response: OpenAI-compatible response
        """
        try:
            messages = data.get('messages', [])
            model = data.get('model', self.default_model)
            stream = data.get('stream', False)
            
            # Get the last user message (usually the most recent one)
            user_message = ""
            for message in reversed(messages):
                if message.get('role') == 'user':
                    user_message = message.get('content', '')
                    break
            
            if not user_message:
                return jsonify({"error": "No user message found"}), 400
            
            # Analyze the message to detect patterns
            pattern_data = self.pattern_detector.detect_pattern(user_message)
            
            if pattern_data:
                return self._handle_pattern_request(pattern_data, model, stream, data)
            else:
                return self._handle_direct_request(user_message, model, stream, data)
                
        except Exception as e:
            return jsonify({"error": f"Chat completion failed: {str(e)}"}), 500

    def _handle_pattern_request(self, pattern_data, model, stream, original_data):
        """
        Handle requests with detected patterns
        
        Args:
            pattern_data (dict): Detected pattern information
            model (str): Model to use
            stream (bool): Whether to stream response
            original_data (dict): Original request data
            
        Returns:
            Flask Response: Processed response
        """
        try:
            if pattern_data['pattern'] == 'custom':
                prompt = pattern_data.get('prompt', '')
                language = pattern_data.get('language', 'Python')
                code = pattern_data.get('code', '')  # Get the code if it exists
            
                if not prompt:
                    return jsonify({"error": "Custom prompt is required for 'custom' pattern"}), 400


                # Use the existing prompt pattern and add code/data if provided
                filled_prompt = self.prompt_patterns[pattern_data['pattern']].format(
                    prompt=prompt,
                    language=language
                )
            
                # Add code/data section if code exists
                if code and code.strip():
                    # For text data (like CSV), use a text or data code block
                    data_section = f"\n\nInput data:\n```\n{code}\n```"
                    filled_prompt += data_section
            
            else:
                # Get all required parameters with defaults
                language = pattern_data.get('language', 'Python')
                code = pattern_data.get('code', '')
                task = pattern_data.get('task', '')
                issue = pattern_data.get('issue', '')
                rules = pattern_data.get('rules', '')  # Add rules extraction
                rules_section = f" Additional rules: {rules}." if rules else ""

                filled_prompt = self.prompt_patterns[pattern_data['pattern']].format(
                    language=language,
                    code=code,
                    task=task,
                    issue=issue,
                    rules_section=rules_section  # Add rules parameter
                )

            # DEBUG: Log the final prompt being sent to AI
            logger.info("=== FINAL PROMPT SENT TO AI ===")
            logger.info(filled_prompt)
            logger.info("=== END PROMPT ===")
            
            # Use OpenAI-compatible format
            messages = [{"role": "user", "content": filled_prompt}]
            options = {
                "temperature": original_data.get('temperature', 0.1),
                "top_p": original_data.get('top_p', 0.9),
                "max_tokens": original_data.get('max_tokens', self.config.get("MAX_TOKENS", 4096))
            }
            
            if stream:
                response = self.ai_provider.generate_openai_compatible(messages, model, stream=True, **options)
                return self._format_streaming_response(response, model)
            else:
                response = self.ai_provider.generate_openai_compatible(messages, model, stream=False, **options)
                return self._format_openai_response(response, model)
            
        except Exception as e:
            return jsonify({"error": f"Pattern processing failed: {str(e)}"}), 500

    def _handle_direct_request(self, message, model, stream, original_data):
        """
        Fallback to direct AI provider call for general conversation
        
        Args:
            message (str): User message
            model (str): Model to use
            stream (bool): Whether to stream response
            original_data (dict): Original request data
            
        Returns:
            Flask Response: Direct AI provider response
        """
        try:
            # Use OpenAI-compatible format
            messages = [{"role": "user", "content": message}]
            options = {
                "temperature": original_data.get('temperature', 0.1),
                "top_p": original_data.get('top_p', 0.9),
                "max_tokens": original_data.get('max_tokens', self.config.get("MAX_TOKENS", 4096))
            }
            
            if stream:
                response = self.ai_provider.generate_openai_compatible(messages, model, stream=True, **options)
                return self._format_streaming_response(response, model)
            else:
                response = self.ai_provider.generate_openai_compatible(messages, model, stream=False, **options)
                return self._format_openai_response(response, model)
            
        except Exception as e:
            return jsonify({"error": f"Direct AI call failed: {str(e)}"}), 500


    def _format_openai_response(self, response, model):
        """Format non-streaming response in OpenAI-compatible format"""
        # Handle different response formats
        content = None
        
        # OpenAI format: {"choices": [{"message": {"content": "..."}}]}
        if hasattr(response, 'get') and 'choices' in response:
            content = response["choices"][0]["message"]["content"]
        # Ollama /api/chat format: {"message": {"content": "...", "role": "assistant"}}
        elif hasattr(response, 'get') and 'message' in response:
            content = response["message"].get("content", "")
        # Ollama /api/generate format (backward compatibility): {"response": "..."}
        elif hasattr(response, 'get') and 'response' in response:
            content = response["response"]
        else:
            content = str(response)
        
        # Ensure content is properly encoded
        if content and isinstance(content, str):
            content = content.encode('utf-8').decode('utf-8')
        
        logger.debug(f"Response content: {content}")
        logger.debug(f"Response content type: {type(content)}")
        logger.debug(f"Response content repr: {repr(content)}")
    
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
        
        # Return with explicit UTF-8 encoding
        flask_response = jsonify(response_data)
        flask_response.headers['Content-Type'] = 'application/json; charset=utf-8'
 
        import json
        response_str = json.dumps(response_data, ensure_ascii=False)
        logger.info(f"Final JSON response: {response_str}")

        return flask_response


    def health_check(self):
        """
        Health check endpoint implementation
        
        Returns:
            Flask Response: Health status
        """
        try:
            # For now, just check if we can create a provider
            # You might want to add actual health checks per provider later
            provider_type = self.config.get("AI_PROVIDER", "ollama")
            
            return jsonify({
                "status": "healthy",
                "ai_provider": provider_type,
                "default_model": self.default_model,
                "provider_connected": True  # Basic check for now
            })
            
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "ai_provider": self.config.get("AI_PROVIDER", "unknown"),
                "error": str(e)
            }), 500

    def get_supported_patterns(self):
        """
        Get list of supported patterns and their descriptions
        
        Returns:
            dict: Pattern information
        """
        patterns_info = {}
        for pattern_name, template in self.prompt_patterns.items():
            patterns_info[pattern_name] = {
                "description": self._get_pattern_description(pattern_name),
                "requires_language": pattern_name != "custom",
                "requires_code": pattern_name in ["fix_bug", "explain_code", "refactor_code", "write_tests", "add_docs"],
                "requires_task": pattern_name == "write_code",
                "requires_prompt": pattern_name == "custom"
            }
        return patterns_info

    def _get_pattern_description(self, pattern_name):
        """
        Get human-readable description for a pattern
        
        Args:
            pattern_name (str): Pattern identifier
            
        Returns:
            str: Pattern description
        """
        descriptions = {
            "write_code": "Generate a function with type hints and documentation",
            "fix_bug": "Fix bugs in provided code with explanation",
            "explain_code": "Explain how code works in detail",
            "refactor_code": "Refactor code for better readability and performance",
            "write_tests": "Write comprehensive unit tests",
            "add_docs": "Add documentation and comments to code",
            "custom": "Use a custom prompt for code generation"
        }
        return descriptions.get(pattern_name, "Unknown pattern")

    def batch_process(self, requests_data):
        """
        Process multiple code generation requests in batch
        
        Args:
            requests_data (list): List of request data dictionaries
            
        Returns:
            Flask Response: Batch processing results
        """
        try:
            results = []
            for request_data in requests_data:
                result = self.generate_code(request_data)
                results.append({
                    "request": request_data,
                    "response": result.get_json() if hasattr(result, 'get_json') else str(result)
                })
            
            return jsonify({
                "batch_id": f"batch_{int(time.time())}",
                "processed_count": len(results),
                "results": results
            })
            
        except Exception as e:
            return jsonify({"error": f"Batch processing failed: {str(e)}"}), 500

    def get_processor_info(self):
        """
        Get information about the code processor
        
        Returns:
            dict: Processor information
        """
        return {
            "name": "AI Code Processor",
            "version": "1.0.0",
            "default_model": self.default_model,
            "supported_patterns": list(self.prompt_patterns.keys()),
            "ai_provider": self.config.get("AI_PROVIDER", "ollama"),
            "max_tokens": 4096,
            "default_temperature": 0.1
        }
