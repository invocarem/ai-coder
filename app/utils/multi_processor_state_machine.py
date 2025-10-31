# app/utils/multi_processor_state_machine.py
import re
import logging

logger = logging.getLogger(__name__)

class MultiProcessorStateMachine:
    def __init__(self):
        # Define states
        self.START = "START"
        self.IN_HEADER = "IN_HEADER"
        self.IN_CODE_BLOCK = "IN_CODE_BLOCK"
        self.COMPLETE = "COMPLETE"
        
        self.current_state = self.START
        self.result = {}
        
        # Processor registry - maps processor names to their patterns
        self.processor_registry = {
            'code': {
                'name': 'code_processor',
                'patterns': [
                    'custom', 'write_code', 'fix_bug', 'improve_code',
                    'explain_code', 'refactor_code', 'write_tests', 'add_docs'
                ]
            },
            'latin': {
                'name': 'latin_processor', 
                'patterns': [
                    'latin_analysis', 'latin_word', 'verse_lemmas', 'patristic_exposition'
                ]
            },
            'psalm': {
                'name': 'psalm_processor',
                'patterns': [
                    'augustine_psalm_query','psalm_query', 'psalm_search', 'bible_query', 'scripture_analysis'
                ]
            }
        }
        
        # Required fields for each pattern
        self.pattern_requirements = {
            # Code patterns
            'custom': ['prompt'],
            'write_code': ['task'],
            'fix_bug': ['code', 'issue'],
            'improve_code': ['code', 'issue'],
            'explain_code': ['code'],
            'refactor_code': ['code'],
            'write_tests': ['code'],
            'add_docs': ['code'],
            
            # Latin patterns
            'latin_analysis': ['word_form'],
            'latin_word': ['word_form'],
            'verse_lemmas': ['verse'],
            'patristic_exposition': ['passage'],
            
            # Psalm patterns
            'augustine_psalm_query': ['question'],
            'psalm_query': ['question'],
            'psalm_search': ['question'],
            'bible_query': ['question'],
            'scripture_analysis': ['passage']
        }
    
    def process(self, message):
        """Process message and determine which processor to use"""
        self._reset()
        lines = message.split('\n')
        
        for line in lines:
            if self.current_state == self.COMPLETE:
                break
            self._process_line(line.strip())
            
        return self._get_processor_result()
    
    def _reset(self):
        """Reset state machine for new message"""
        self.current_state = self.START
        self.result = {}
    
    def _process_line(self, line):
        """Process a single line based on current state"""
        if self.current_state == self.START:
            self._handle_start_state(line)
        elif self.current_state == self.IN_HEADER:
            self._handle_header_state(line)
        elif self.current_state == self.IN_CODE_BLOCK:
            self._handle_code_state(line)
    
    def _handle_start_state(self, line):
        """START state - look for valid starting tokens"""
        if line.startswith('```'):
            self.current_state = self.IN_CODE_BLOCK
            self._handle_code_state(line)
        elif line.startswith('###'):
            self.current_state = self.IN_HEADER
            self._handle_header_state(line)
    
    def _handle_header_state(self, line):
        """IN_HEADER state - process structured headers"""
        if line.startswith('```'):
            self.current_state = self.IN_CODE_BLOCK
            self._handle_code_state(line)
        elif line.startswith('###'):
            self._parse_header(line)
        else:
            self._capture_content(line)
    
    def _handle_code_state(self, line):
        """IN_CODE_BLOCK state - capture code content"""
        if line.startswith('```'):
            if self.result.get('code'):
                self.current_state = self.IN_HEADER
        else:
            current_code = self.result.get('code', '')
            self.result['code'] = current_code + '\n' + line if current_code else line
    
    def _parse_header(self, line):
        """Parse ### Key: value headers"""
        match = re.match(r'###\s*(\w+):\s*(.*)', line)
        if not match:
            return
            
        key = match.group(1).lower().strip()
        value = match.group(2).strip()
        
        # Store all headers in result
        self.result[key] = value
        
        # Special handling for processor and pattern headers
        if key == 'processor':
            # Validate processor exists
            if not self._is_valid_processor(value):
                logger.warning(f"Unknown processor: {value}")
                return
                
        elif key == 'pattern':
            pattern = value
            # If processor is specified, validate pattern belongs to that processor
            specified_processor = self.result.get('processor')
            if specified_processor and not self._is_valid_pattern_for_processor(pattern, specified_processor):
                logger.warning(f"Pattern '{pattern}' not valid for processor '{specified_processor}'")
                return
                
            if self._can_complete_pattern(pattern):
                self.current_state = self.COMPLETE
    
    def _capture_content(self, line):
        """Capture multi-line content for fields like prompt, question, etc."""
        if not line or line.startswith('#'):
            return
            
        pattern = self.result.get('pattern')
        if not pattern:
            return
            
        content_fields = {
            'custom': 'prompt',
            'write_code': 'task', 
            'fix_bug': 'issue',
            'improve_code': 'issue',
            'psalm_query': 'question',
            'psalm_search': 'question',
            'bible_query': 'question',
            'scripture_analysis': 'context',
            'patristic_exposition': 'context'
        }
        
        field = content_fields.get(pattern)
        if field and field in self.result:
            self.result[field] += '\n' + line
    
    def _is_valid_processor(self, processor):
        """Check if processor is in registry"""
        return processor in self.processor_registry
    
    def _is_valid_pattern_for_processor(self, pattern, processor):
        """Check if pattern is valid for the specified processor"""
        processor_info = self.processor_registry.get(processor)
        if not processor_info:
            return False
        return pattern in processor_info['patterns']
    
    def _can_complete_pattern(self, pattern):
        """Check if we have all required fields for this pattern"""
        required_fields = self.pattern_requirements.get(pattern, [])
        return all(field in self.result and self.result[field] for field in required_fields)
    
    def _get_processor_result(self):
        """Determine which processor to route to"""
        pattern = self.result.get('pattern')
        specified_processor = self.result.get('processor')
        
        # If no pattern specified, try to infer from processor and available fields
        if not pattern and specified_processor:
            pattern = self._infer_pattern_from_fields(specified_processor)
            if pattern:
                self.result['pattern'] = pattern
                logger.info(f"Inferred pattern '{pattern}' for processor '{specified_processor}'")
        
        if not pattern:
            return None
        
        # Determine processor
        processor_name = None
        
        if specified_processor:
            # Use explicitly specified processor
            processor_info = self.processor_registry.get(specified_processor)
            if processor_info and pattern in processor_info['patterns']:
                processor_name = processor_info['name']
            else:
                logger.warning(f"Pattern '{pattern}' not valid for specified processor '{specified_processor}'")
                return None
        else:
            # Auto-detect processor based on pattern
            for processor_key, processor_info in self.processor_registry.items():
                if pattern in processor_info['patterns']:
                    processor_name = processor_info['name']
                    break
        
        if not processor_name:
            return None
            
        # Validate required fields
        required_fields = self.pattern_requirements.get(pattern, [])
        missing_fields = [field for field in required_fields if not self.result.get(field)]
        
        if missing_fields:
            logger.warning(f"Pattern '{pattern}' missing required fields: {missing_fields}")
            return None
        
        # Set defaults
        if not self.result.get('language'):
            self.result['language'] = 'Python'
            
        # Clean up fields
        for field in self.result:
            if isinstance(self.result[field], str):
                self.result[field] = self.result[field].strip()
        
        return {
            'processor': processor_name,
            'pattern_data': self.result,
            'specified_processor': specified_processor is not None  # Track if processor was explicitly specified
        }
    
    def get_supported_processors(self):
        """Return all supported processors with their patterns"""
        return {
            processor_key: {
                'name': info['name'],
                'patterns': info['patterns']
            }
            for processor_key, info in self.processor_registry.items()
        }
    
    def get_processor_patterns(self, processor):
        """Get patterns for a specific processor"""
        processor_info = self.processor_registry.get(processor)
        return processor_info['patterns'] if processor_info else []
    
    def get_pattern_requirements(self, pattern):
        """Get required fields for a specific pattern"""
        return self.pattern_requirements.get(pattern, [])
    
    def _infer_pattern_from_fields(self, processor):
        """Infer pattern from available fields when pattern is not explicitly specified"""
        processor_info = self.processor_registry.get(processor)
        if not processor_info:
            return None
        
        # Check available fields in result
        available_fields = set(self.result.keys())
        
        # For latin processor, check if word_form is present
        if processor == 'latin':
            if 'word_form' in available_fields:
                return 'latin_analysis'
            elif 'verse' in available_fields:
                return 'verse_lemmas'
        
        # For code processor, check field combinations
        elif processor == 'code':
            if 'prompt' in available_fields:
                return 'custom'
            elif 'task' in available_fields:
                return 'write_code'
            elif 'code' in available_fields and 'issue' in available_fields:
                return 'fix_bug'
            elif 'code' in available_fields:
                return 'explain_code'
        
        # For psalm processor
        elif processor == 'psalm':
            if 'question' in available_fields:
                return 'psalm_query'
        
        return None