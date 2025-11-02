# app/processors/processor_router.py
import logging
from flask import jsonify

logger = logging.getLogger(__name__)

class ProcessorRouter:
    def __init__(self, config):
        self.config = config
        self.ai_provider = None
        self.processors = {}
        self._initialized = False
    
    def initialize_processors(self):
        """Lazy initialization of processors"""
        if self._initialized:
            return
            
        from app.utils.ai_provider import AIProviderFactory
        from app.processors.code_processor import CodeProcessor
        from app.processors.latin_processor import LatinProcessor
        from app.processors.psalm_rag_processor import PsalmRAGProcessor
        
        self.ai_provider = AIProviderFactory.create_provider(self.config)
        
        self.processors = {
            'code_processor': CodeProcessor(self.ai_provider),
            'latin_processor': LatinProcessor(self.ai_provider),
            'psalm_processor': PsalmRAGProcessor(self.ai_provider)
        }
        self._initialized = True
        logger.info("ProcessorRouter initialized with processors: %s", list(self.processors.keys()))
    
    def route_request(self, detection_result, model, stream, original_data, api_key=None):
        """Route request to appropriate processor based on detection result or API key"""
        if not self._initialized:
            self.initialize_processors()
        
        logger.info(f"Router received detection result: {detection_result}, API key: {api_key}")
        
        # Extract processor name and pattern data from detection result
        processor_name = None
        pattern_data = {}
        
        if detection_result:
            # Extract pattern_data and processor from detection result
            pattern_data = detection_result.get('pattern_data', {})
            processor_name = detection_result.get('processor')
            logger.info(f"Pattern detection found processor: {processor_name}, pattern_data: {pattern_data}")
        
        # Processor selection priority:
        # 1. Processor specified in message content (from pattern detection) - highest priority
        # 2. API key - used as fallback when no processor detected in message
        if processor_name:
            # Processor was specified in message content - use it (don't override with API key)
            logger.info(f"Using processor '{processor_name}' from message content (API key '{api_key}' ignored for processor selection)")
            
            # If pattern_data is empty or incomplete, try to enhance it based on the detected processor
            if not pattern_data or not pattern_data.get('pattern'):
                # Extract short processor name for creating defaults
                short_processor_name = processor_name
                # Reverse mapping: if it's already a full name like 'latin_processor', extract 'latin'
                reverse_mapping = {
                    'code_processor': 'code',
                    'latin_processor': 'latin',
                    'psalm_processor': 'psalm'
                }
                if processor_name in reverse_mapping:
                    short_processor_name = reverse_mapping[processor_name]
                
                default_pattern_data = self._create_default_pattern_data(short_processor_name, original_data)
                # Merge: use existing pattern_data but fill in missing fields from default
                if not pattern_data:
                    pattern_data = default_pattern_data
                else:
                    # Merge pattern_data with defaults
                    for key, value in default_pattern_data.items():
                        if key not in pattern_data or not pattern_data[key]:
                            pattern_data[key] = value
        elif api_key:
            # No processor in message content - use API key as fallback
            processor_name = api_key
            logger.info(f"No processor in message content, using API key '{api_key}' as processor selector")
            
            # Create default pattern data based on the API key
            if not pattern_data or not pattern_data.get('pattern'):
                default_pattern_data = self._create_default_pattern_data(api_key, original_data)
                if not pattern_data:
                    pattern_data = default_pattern_data
                else:
                    # Merge pattern_data with defaults
                    for key, value in default_pattern_data.items():
                        if key not in pattern_data or not pattern_data[key]:
                            pattern_data[key] = value
        else:
            # No pattern detected and no API key - return error
            logger.error("No processor specified in detection result and no API key provided")
            return self._handle_no_pattern(original_data)
        
        # Map short processor names to full processor names
        processor_name_mapping = {
            'code': 'code_processor',
            'latin': 'latin_processor',
            'psalm': 'psalm_processor'
        }
        if processor_name in processor_name_mapping:
            processor_name = processor_name_mapping[processor_name]
            logger.info(f"Mapped processor name to: {processor_name}")
        
        processor = self.processors.get(processor_name)
        if not processor:
            logger.error(f"Processor not found: {processor_name}. Available: {list(self.processors.keys())}")
            return jsonify({"error": f"Processor not found: {processor_name}"}), 500
        
        try:
            pattern = pattern_data.get('pattern', 'unknown')
            logger.info(f"🚀 Routing to {processor_name} with pattern: {pattern}")
            
            # Call the processor with the consistent interface
            return processor.process(pattern_data, model, stream, original_data)
            
        except Exception as e:
            logger.error(f"Processor {processor_name} failed: {str(e)}")
            return jsonify({"error": f"Processor error: {str(e)}"}), 500
    
    def _handle_no_pattern(self, original_data):
        """Handle requests without detected patterns"""
        logger.warning("No pattern detected in request")
        
        # Provide helpful error message with examples
        examples = {
            "code_processor": "### processor: code\n### pattern: custom\n### language: gnuplot\n### prompt: your request here",
            "latin_processor": "### processor: latin\n### pattern: latin_analysis\n### word_form: abiit", 
            "psalm_processor": "### processor: psalm\n### pattern: psalm_query\n### question: your question here"
        }
        
        return jsonify({
            "error": "No valid pattern detected. Use structured format with ### headers",
            "supported_processors": list(self.processors.keys()),
            "usage_examples": examples
        }), 400
    
    def health_check(self):
        """Comprehensive health check for all processors"""
        if not self._initialized:
            self.initialize_processors()
        
        health_status = {
            "status": "healthy",
            "processors": {},
            "ai_provider": self.config.get("AI_PROVIDER", "unknown")
        }
        
        for name, processor in self.processors.items():
            try:
                if hasattr(processor, 'health_check'):
                    processor_health = processor.health_check()
                    health_status["processors"][name] = {
                        "status": "healthy",
                        "details": processor_health.get_json() if hasattr(processor_health, 'get_json') else processor_health
                    }
                else:
                    health_status["processors"][name] = {"status": "healthy", "details": "No health check method"}
            except Exception as e:
                health_status["processors"][name] = {"status": "unhealthy", "error": str(e)}
        
        # Check if any processor is unhealthy
        unhealthy_processors = [name for name, status in health_status["processors"].items() 
                              if status["status"] == "unhealthy"]
        if unhealthy_processors:
            health_status["status"] = "degraded"
            health_status["unhealthy_processors"] = unhealthy_processors
        
        return jsonify(health_status)
    
    def get_processor_info(self, processor_name=None):
        """Get information about processors"""
        if not self._initialized:
            self.initialize_processors()
        
        if processor_name:
            processor = self.processors.get(processor_name)
            if processor and hasattr(processor, 'get_processor_info'):
                return processor.get_processor_info()
            else:
                return {"error": f"Processor {processor_name} not found or no info available"}
        
        # Return info for all processors
        info = {
            "available_processors": list(self.processors.keys()),
            "default_processor": "code_processor",
            "ai_provider": self.config.get("AI_PROVIDER", "unknown")
        }
        
        for name, processor in self.processors.items():
            if hasattr(processor, 'get_processor_info'):
                info[name] = processor.get_processor_info()
        
        return info

    def get_supported_patterns(self):
        """Get all supported patterns from all processors"""
        if not self._initialized:
            self.initialize_processors()
        
        all_patterns = {}
        for processor_name, processor in self.processors.items():
            if hasattr(processor, 'get_supported_patterns'):
                all_patterns[processor_name] = processor.get_supported_patterns()
        
        return all_patterns
    
    def _create_default_pattern_data(self, api_key, original_data):
        """Create default pattern data structure based on API key when pattern detection fails"""
        # Get user message from original_data if available
        messages = original_data.get('messages', [])
        user_message = ""
        for message in reversed(messages):
            if message.get('role') == 'user':
                user_message = message.get('content', '')
                break
        
        # Create pattern_data based on processor type
        pattern_data = {}
        
        if api_key == 'code':
            # For code processor, use 'custom' pattern with the user message as prompt
            pattern_data = {
                'pattern': 'custom',
                'prompt': user_message,
                'language': 'Python'  # default language
            }
        elif api_key == 'latin':
            # For latin processor, try to extract word_form from user message
            # Simple extraction: if message looks like a word, use it
            word_form = user_message.strip()
            # Remove markdown formatting if present
            word_form = word_form.replace('**', '').replace('*', '').strip()
            pattern_data = {
                'pattern': 'latin_analysis',
                'word_form': word_form
            }
        elif api_key in ['psalm', 'augustine']:
            # For RAG processors, use the user message as question/prompt
            pattern_data = {
                'pattern': 'psalm_query' if api_key == 'psalm' else 'patristic_exposition',
                'question': user_message if api_key == 'psalm' else None,
                'passage': user_message if api_key == 'augustine' else None
            }
        
        logger.info(f"Created default pattern_data for {api_key}: {pattern_data}")
        return pattern_data