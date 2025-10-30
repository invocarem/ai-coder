# app/processors/processor_router.py
import logging
from flask import jsonify

logger = logging.getLogger(__name__)

class ProcessorRouter:
    def __init__(self, config):
        self.config = config
        self.ai_provider = None  # Will be initialized when needed
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
        from app.processors.augustine_rag_processor import AugustineRAGProcessor
        
        self.ai_provider = AIProviderFactory.create_provider(self.config)
        
        self.processors = {
            'code': CodeProcessor(self.ai_provider),
            'latin': LatinProcessor(self.ai_provider),
            'psalm': PsalmRAGProcessor(self.ai_provider),
            'augustine': AugustineRAGProcessor(self.ai_provider)
        }
        self._initialized = True
        logger.info("ProcessorRouter initialized with processors: %s", list(self.processors.keys()))
    
    def route_request(self, pattern_data, model, stream, original_data):
        """Route request to appropriate processor"""
        if not self._initialized:
            self.initialize_processors()
        
        processor_type = self._detect_processor_type(pattern_data)
        processor = self.processors.get(processor_type)
        
        if processor:
            logger.info("Routing to %s processor for pattern: %s", processor_type, pattern_data.get('pattern'))
            return processor.process(pattern_data, model, stream, original_data)
        else:
            # Fallback to code processor
            logger.info("No specific processor found, using code processor as fallback")
            return self.processors['code'].process(pattern_data, model, stream, original_data)
    
    def _detect_processor_type(self, pattern_data):
        """Detect which processor should handle this request"""
        pattern = pattern_data.get('pattern', '')
        
        if pattern.startswith('latin') or 'latin_word' in pattern_data:
            return 'latin'
        elif pattern.startswith('psalm') or 'psalm_number' in pattern_data:
            return 'psalm'
        elif pattern.startswith('augustin') in pattern_data:
            return 'augustine'
        else:
            return 'code'
    
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
    
    def get_processor_info(self, processor_type=None):
        """Get information about processors"""
        if not self._initialized:
            self.initialize_processors()
        
        if processor_type:
            processor = self.processors.get(processor_type)
            if processor and hasattr(processor, 'get_processor_info'):
                return processor.get_processor_info()
            else:
                return {"error": f"Processor {processor_type} not found or no info available"}
        
        # Return info for all processors
        info = {
            "available_processors": list(self.processors.keys()),
            "default_processor": "code",
            "ai_provider": self.config.get("AI_PROVIDER", "unknown")
        }
        
        for name, processor in self.processors.items():
            if hasattr(processor, 'get_processor_info'):
                info[name] = processor.get_processor_info()
        
        return info