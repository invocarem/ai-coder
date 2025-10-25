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

class CodeProcessor:
    def __init__(self):
        """Initialize the code processor with configuration and dependencies"""
        self.config = load_config()
        self.pattern_detector = PatternDetector()
        self.ai_provider = AIProviderFactory.create_provider(self.config)
        self.default_model = self.config["DEFAULT_MODEL"]
        
        # Define prompt templates for different code generation patterns
        self.prompt_patterns = {
            "generate_function": "Write a {language} function to {task}. Include type hints and docstring. Provide only the code without explanations.",
            "fix_bug": 
            """Fix this {language} code bug:
```{language}
{code}
 Issue: {issue}
 Additional Rules:
 {rules} 
 """
            "Fix this {language} code: ```{language}\n{code}\n```. The issue is: {issue}. Provide the fixed code with comments explaining the changes.",
            "explain_code": "Explain how this {language} code works: ```{language}\n{code}\n```. Provide a clear explanation of what the code does, how it works, and any important details.",
            "refactor_code": "Refactor this {language} code for better readability and performance: ```{language}\n{code}\n```. Provide the refactored code with comments explaining the improvements.",
            "write_tests": "Write comprehensive unit tests for this {language} function: ```{language}\n{code}\n```. Include test cases for edge cases and normal scenarios.",
            "add_docs": "Add detailed docstring and comments to this {language} code: ```{language}\n{code}\n```. Provide the documented code with clear explanations.",
            "custom": "{prompt}"
        }

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
                "max_tokens": data.get('max_tokens', 4096)
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
                    
                return jsonify({"text": text})            
                
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"AI provider connection error: {str(e)}"}), 503
        except Exception as e:
            return jsonify({"error": f"Code generation failed: {str(e)}"}), 500

    def _format_streaming_response(self, response, model):
        """Format streaming response in OpenAI-compatible format"""
        def generate():
            for line in response:
                if line:
                    try:
                        # Decode bytes to string if needed
                        if isinstance(line, bytes):
                            line = line.decode('utf-8')
                        
                        # Parse the response line based on provider format
                        if line.startswith('data: '):
                            # OpenAI format
                            data = json.loads(line[6:])
                            if 'choices' in data and data['choices']:
                                content = data['choices'][0].get('delta', {}).get('content', '')
                                if content:
                                    yield f"data: {json.dumps({
                                        'id': f'chatcmpl-{int(time.time())}',
                                        'object': 'chat.completion.chunk',
                                        'created': int(time.time()),
                                        'model': model,
                                        'choices': [{
                                            'index': 0,
                                            'delta': {'content': content},
                                            'finish_reason': None
                                        }]
                                    })}\n\n"
                        else:
                            # Ollama format
                            data = json.loads(line)
                            content = data.get('response', '')
                            if content:
                                yield f"data: {json.dumps({
                                    'id': f'chatcmpl-{int(time.time())}',
                                    'object': 'chat.completion.chunk',
                                    'created': int(time.time()),
                                    'model': model,
                                    'choices': [{
                                        'index': 0,
                                        'delta': {'content': content},
                                        'finish_reason': None
                                    }]
                                })}\n\n"
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"Error processing stream line: {e}")
                        continue
            
            # Send final done chunk
            yield f"data: {json.dumps({
                'id': f'chatcmpl-{int(time.time())}',
                'object': 'chat.completion.chunk',
                'created': int(time.time()),
                'model': model,
                'choices': [{
                    'index': 0,
                    'delta': {},
                    'finish_reason': 'stop'
                }]
            })}\n\n"
            yield "data: [DONE]\n\n"
        
        return Response(generate(), mimetype='text/event-stream')

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
        if pattern == "generate_function":
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
                filled_prompt = pattern_data.get('prompt', '')
            else:
                # Get all required parameters with defaults
                language = pattern_data.get('language', 'Python')
                code = pattern_data.get('code', '')
                task = pattern_data.get('task', '')
                issue = pattern_data.get('issue', '')
                rules = pattern_data.get('rules', '')  # Add rules extraction
            
                filled_prompt = self.prompt_patterns[pattern_data['pattern']].format(
                    language=language,
                    code=code,
                    task=task,
                    issue=issue,
                    rules=rules  # Add rules parameter
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
                "max_tokens": original_data.get('max_tokens', 4096)
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
                "max_tokens": original_data.get('max_tokens', 4096)
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
        if hasattr(response, 'get') and 'choices' in response:  # OpenAI format
            content = response["choices"][0]["message"]["content"]
        elif hasattr(response, 'get') and 'response' in response:  # Ollama format
            content = response["response"]
        else:
            content = str(response)
        
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
                "requires_task": pattern_name == "generate_function",
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
            "generate_function": "Generate a function with type hints and documentation",
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