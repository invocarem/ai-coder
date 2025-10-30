# app/utils/pattern_detector.py
import re
import logging
from .multi_processor_state_machine import MultiProcessorStateMachine

logger = logging.getLogger(__name__)

class PatternDetector:
    def __init__(self):
        self.supported_languages = [
            'python', 'javascript', 'java', 'c++', 'c#', 'go', 
            'rust', 'php', 'ruby', 'swift', 'typescript', 'bash', 
            'awk', 'gnuplot', 'latin'
        ]
        self.state_machine = MultiProcessorStateMachine()

    def detect_pattern(self, message):
        """
        Detect pattern and route to appropriate processor
        
        Args:
            message (str): User message in structured format
            
        Returns:
            dict or None: {
                'processor': 'processor_name',
                'pattern_data': { ... },
                'specified_processor': boolean
            } or None if no pattern detected
        """
        logger.debug(f"Pattern detection for message: {message[:100]}...")
        
        # Use the state machine for pattern detection
        result = self.state_machine.process(message)
        
        if result:
            processor = result['processor']
            pattern_data = result['pattern_data']
            specified = result['specified_processor']
            
            mode = "EXPLICIT" if specified else "AUTO-DETECTED"
            logger.info(f"✅ {mode} - Pattern '{pattern_data['pattern']}' → Processor: {processor}")
            logger.debug(f"Pattern data: {pattern_data}")
            return result
        
        logger.info("❌ No valid structured pattern found")
        return None

    def get_supported_processors(self):
        """
        Get all supported processors with their patterns
        
        Returns:
            dict: Processor information organized by processor key
        """
        return self.state_machine.get_supported_processors()
    
    def get_processor_patterns(self, processor):
        """
        Get patterns for a specific processor
        
        Args:
            processor (str): Processor key ('code', 'latin', 'psalm')
            
        Returns:
            list: Supported patterns for the processor
        """
        return self.state_machine.get_processor_patterns(processor)
    
    def get_pattern_requirements(self, pattern):
        """
        Get required fields for a specific pattern
        
        Args:
            pattern (str): Pattern name
            
        Returns:
            list: Required field names
        """
        return self.state_machine.get_pattern_requirements(pattern)

    def validate_pattern_request(self, pattern_data):
        """
        Validate if pattern data has all required fields
        
        Args:
            pattern_data (dict): Pattern data to validate
            
        Returns:
            tuple: (is_valid, missing_fields)
        """
        pattern = pattern_data.get('pattern')
        if not pattern:
            return False, ['pattern']
            
        required_fields = self.get_pattern_requirements(pattern)
        missing_fields = [field for field in required_fields if not pattern_data.get(field)]
        
        return len(missing_fields) == 0, missing_fields

    def get_usage_examples(self):
        """
        Get usage examples for all processors
        
        Returns:
            dict: Usage examples organized by processor
        """
        examples = {}
        processors = self.get_supported_processors()
        
        for processor_key, processor_info in processors.items():
            examples[processor_key] = {
                'name': processor_info['name'],
                'examples': self._get_processor_examples(processor_key, processor_info['patterns'])
            }
        
        return examples

    def _get_processor_examples(self, processor_key, patterns):
        """Get examples for a specific processor"""
        examples = {}
        
        if processor_key == 'code':
            examples = {
                'custom': "### processor: code\n### pattern: custom\n### language: python\n### prompt: Write a function to calculate factorial",
                'fix_bug': "### processor: code\n### pattern: fix_bug\n### language: python\n### issue: Function crashes on empty input\n### code: def process(data): return data.split()",
                'write_code': "### processor: code\n### pattern: write_code\n### language: javascript\n### task: Create a function that validates email addresses"
            }
        elif processor_key == 'latin':
            examples = {
                'latin_analysis': "### processor: latin\n### pattern: latin_analysis\n### word_form: abiit\n### context: from Psalm 95",
                'verse_lemmas': "### processor: latin\n### pattern: verse_lemmas\n### verse: In principio erat Verbum\n### translation: Provide English translation"
            }
        elif processor_key == 'psalm':
            examples = {
                'psalm_query': "### processor: psalm\n### pattern: psalm_query\n### question: What does Psalm 23 say about shepherds?\n### context: Sunday sermon preparation",
                'bible_query': "### processor: psalm\n### pattern: bible_query\n### question: Explain the meaning of John 3:16"
            }
        
        return examples

    def extract_code_blocks(self, message):
        """
        Extract code from markdown code blocks
        
        Args:
            message (str): Message containing code blocks
            
        Returns:
            str: Extracted code or empty string
        """
        # Try to extract fenced code blocks
        code_blocks = re.findall(r'```(?:\w+)?\s*\n(.*?)```', message, re.DOTALL)
        if code_blocks:
            return code_blocks[0].strip()
        
        # Fallback: look for inline code or other patterns
        return ""

    def detect_processor_from_pattern(self, pattern):
        """
        Detect which processor handles a specific pattern
        
        Args:
            pattern (str): Pattern name
            
        Returns:
            str or None: Processor key or None if not found
        """
        processors = self.get_supported_processors()
        for processor_key, processor_info in processors.items():
            if pattern in processor_info['patterns']:
                return processor_key
        return None

    def is_pattern_supported(self, pattern):
        """
        Check if a pattern is supported by any processor
        
        Args:
            pattern (str): Pattern name to check
            
        Returns:
            bool: True if pattern is supported
        """
        return self.detect_processor_from_pattern(pattern) is not None

    def get_processor_for_pattern(self, pattern):
        """
        Get the processor name for a specific pattern
        
        Args:
            pattern (str): Pattern name
            
        Returns:
            str or None: Processor name or None if not found
        """
        processor_key = self.detect_processor_from_pattern(pattern)
        if processor_key:
            processors = self.get_supported_processors()
            return processors[processor_key]['name']
        return None

# Legacy support - maintain backward compatibility
def create_pattern_detector():
    """Factory function to create pattern detector (for backward compatibility)"""
    return PatternDetector()