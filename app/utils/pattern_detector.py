# app/utils/pattern_detector.py
import re
import logging
logger = logging.getLogger(__name__)

class PatternDetector:
    def __init__(self):
        self.supported_languages = [
            'python', 'javascript', 'java', 'c++', 'c#', 'go', 
            'rust', 'php', 'ruby', 'swift', 'typescript', 'bash', 'awk'
        ]

    def detect_pattern(self, message):
        """
        Detect which pattern to use based on explicit pattern names in the message
        
        Args:
            message (str): The user message to analyze
            
        Returns:
            dict or None: Pattern data if detected, None otherwise
        """
        # First check for structured format
        structured_data = self._parse_structured_format(message)
        if structured_data:
            return structured_data
            
        message_lower = message.lower()
        
        # Only check for exact pattern names
        if 'write_code' in message_lower:
            language = self._extract_language(message)
            task = self._extract_task_after_pattern(message, 'write_code')
            return {
                'pattern': 'generate_function',
                'language': language,
                'task': task
            }
        
        elif 'refactor_code' in message_lower:
            code = self._extract_code_blocks(message)
            return {
                'pattern': 'refactor_code',
                'language': self._extract_language(message),
                'code': code
            }
        
        elif 'write_test' in message_lower:
            code = self._extract_code_blocks(message)
            return {
                'pattern': 'write_tests',
                'language': self._extract_language(message),
                'code': code
            }
        
        elif 'fix_bug' in message_lower or 'fix this' in message_lower:
            code = self._extract_code_blocks(message)
            return {
                'pattern': 'fix_bug',
                'language': self._extract_language(message),
                'code': code,
                'issue': self._extract_issue_description(message)
            }
        
        elif 'explain_code' in message_lower:
            code = self._extract_code_blocks(message)
            return {
                'pattern': 'explain_code',
                'language': self._extract_language(message),
                'code': code
            }
        
        elif 'add_docs' in message_lower:
            code = self._extract_code_blocks(message)
            return {
                'pattern': 'add_docs',
                'language': self._extract_language(message),
                'code': code
            }
        
        # For custom prompts that don't match any pattern
        return None
            
    def _parse_structured_format(self, message):
        """Parse structured ###Key: value format with code blocks using state machine"""
        lines = message.split('\n')
        
        # State machine states
        STATE_START = 0
        STATE_IN_PATTERN = 1
        STATE_IN_TASK = 2
        STATE_IN_LANGUAGE = 3
        STATE_IN_ISSUE = 4
        STATE_IN_RULES = 5
        STATE_IN_CODE = 6
        STATE_IN_EXPLANATION = 7  # New state for explanations after code
        
        current_state = STATE_START
        
        # Results
        pattern = None
        task = ""
        language = ""
        issue = ""
        rules = []
        code_lines = []
        explanation_lines = []  # New: for text after code blocks
        
        for line in lines:
            stripped_line = line.strip()
            
            # Check for state transitions (### markers)
            if stripped_line.startswith('###'):
                # Extract key from ### Key: format
                key_match = re.match(r'###\s*(\w+):?\s*(.*)', stripped_line, re.IGNORECASE)
                if key_match:
                    key_name = key_match.group(1).lower()
                    value_part = key_match.group(2).strip()
                    
                    # Any ### marker resets from explanation state
                    if current_state == STATE_IN_EXPLANATION:
                        current_state = STATE_START
                    
                    # Transition to new state based on key
                    if key_name == 'pattern':
                        current_state = STATE_IN_PATTERN
                        pattern = value_part
                    elif key_name == 'task':
                        current_state = STATE_IN_TASK
                        if value_part:
                            task = value_part
                    elif key_name == 'language':
                        current_state = STATE_IN_LANGUAGE
                        if value_part:
                            language = value_part
                    elif key_name == 'issue':
                        current_state = STATE_IN_ISSUE
                        if value_part:
                            issue = value_part
                    elif key_name == 'rules':
                        current_state = STATE_IN_RULES
                        if value_part:
                            rules.append(value_part)
                    elif key_name == 'code':
                        current_state = STATE_IN_CODE
                    else:
                        # Unknown key, stay in current state
                        continue
                else:
                    # Malformed ### line, ignore
                    continue
                    
            # Check for code block markers ```
            elif stripped_line.startswith('```'):
                if current_state == STATE_IN_CODE:
                    # Ending code block - transition to explanation state
                    current_state = STATE_IN_EXPLANATION
                else:
                    # Starting code block
                    current_state = STATE_IN_CODE
                    # Extract language from ```language if present
                    lang_match = re.match(r'```(\w+)', stripped_line)
                    if lang_match and not language:
                        potential_lang = lang_match.group(1).lower()
                        if potential_lang in self.supported_languages:
                            language = potential_lang.capitalize() if potential_lang != 'c#' else 'C#'
            
            # Process content based on current state
            else:
                if current_state == STATE_IN_PATTERN and not pattern:
                    pattern = stripped_line
                elif current_state == STATE_IN_TASK:
                    if task and stripped_line:
                        task += '\n' + stripped_line
                    elif stripped_line:
                        task = stripped_line
                elif current_state == STATE_IN_LANGUAGE and not language:
                    language = stripped_line
                elif current_state == STATE_IN_ISSUE:
                    if issue and stripped_line:
                        issue += '\n' + stripped_line
                    elif stripped_line:
                        issue = stripped_line
                elif current_state == STATE_IN_RULES:
                    if stripped_line:
                        rules.append(stripped_line)
                elif current_state == STATE_IN_CODE:
                    code_lines.append(line)  # Keep original line (with indentation)
                elif current_state == STATE_IN_EXPLANATION:
                    # Collect explanation text after code blocks
                    if stripped_line:  # Only non-empty lines
                        explanation_lines.append(stripped_line)
        
        # Process results
        if pattern:
            pattern = pattern.strip().lower()
            
            # Map pattern names to internal patterns
            pattern_map = {
                'fix_bug': 'fix_bug',
                'write_code': 'generate_function', 
                'refactor_code': 'refactor_code',
                'write_test': 'write_tests',
                'explain_code': 'explain_code',
                'add_docs': 'add_docs',
                'custom': 'custom'
            }
            
            internal_pattern = pattern_map.get(pattern)
            if internal_pattern:
                # Use code collected by state machine, fallback to extract_code_blocks
                code = '\n'.join(code_lines).strip()
                if not code:
                    code = self._extract_code_blocks(message)
                
                # Combine explanation lines
                explanation = '\n'.join(explanation_lines).strip()
                
                # If no language specified but we detected from code block, use it
                if not language:
                    language_from_code = self._extract_language(message)
                    if language_from_code != 'Python':  # Only use if not default
                        language = language_from_code
                
                # Debug logging
                logger.info(f"Pattern detected: {internal_pattern}")
                logger.info(f"Language: {language}")
                logger.info(f"Code length: {len(code)}")
                logger.info(f"Explanation: {explanation}")
                logger.info(f"Issue: {issue}")
                logger.info(f"Rules: {'; '.join(rules)}")
                
                return {
                    'pattern': internal_pattern,
                    'task': task.strip(),
                    'issue': issue.strip(),
                    'rules': '; '.join(rules).strip(),
                    'code': code,
                    'explanation': explanation,  # New field
                    'language': language.strip() or 'Python'
                }
        
        return None


        


    def _extract_task_after_pattern(self, message, pattern):
        """Extract the task description after the specific pattern name"""
        if pattern in message.lower():
            # Return text after the pattern name
            content_after_pattern = message[message.lower().find(pattern) + len(pattern):].strip()
            # Remove any leading colons, spaces, or "in language" phrases
            content_after_pattern = content_after_pattern.lstrip(':').strip()
            
            # Remove "in language" if present
            words = content_after_pattern.split()
            if len(words) >= 2 and words[0] == 'in':
                # Check if the second word is a programming language
                if words[1] in self.supported_languages:
                    return ' '.join(words[2:])
            
            # Remove any ### patterns that might be present
            content_after_pattern = re.sub(r'###\s*\w+:', '', content_after_pattern).strip()
            
            return content_after_pattern
        return message

    def _extract_issue_description(self, message):
        """Extract issue description after fix_bug pattern"""
        message_lower = message.lower()
        if 'fix_bug' in message_lower:
            # Get everything after fix_bug
            content = message[message_lower.find('fix_bug') + len('fix_bug'):].strip()
            content = content.lstrip(':').strip()
            
            # If there's code, extract the issue part before the code
            code = self._extract_code_blocks(content)
            if code:
                return content.replace(f"```{code}```", "").strip()
            return content
        elif 'fix this' in message_lower:
            # Handle "Fix this [language] code:" format
            # Look for "### Issue:" pattern first
            issue_start = message.find("### Issue:")
            if issue_start != -1:
                issue_content = message[issue_start + len("### Issue:"):].strip()
                # Extract issue description before ### Rules: or ```
                issue_match = re.search(r'^(.+?)(?=\n### Rules:|\n```|$)', issue_content, re.DOTALL)
                if issue_match:
                    return issue_match.group(1).strip()
                return issue_content
            
            # Fallback to "The issue is:" pattern
            issue_start = message.find("The issue is:")
            if issue_start != -1:
                issue_content = message[issue_start + len("The issue is:"):].strip()
                # Extract issue description before any code blocks
                issue_match = re.search(r'^(.+?)(?=\n###|\n```|$)', issue_content, re.DOTALL)
                if issue_match:
                    return issue_match.group(1).strip()
                return issue_content
            return "Unknown issue"
        return "Unknown issue"

    def _extract_language(self, message):
        """Extract programming language from message"""
        message_lower = message.lower()
        
        # First, try to find language in code blocks
        code_blocks = re.findall(r'```(\w+)?\s*\n', message)
        for lang in code_blocks:
            if lang and lang.lower() in self.supported_languages:
                return lang.capitalize() if lang != 'c#' else 'C#'
        
        # Fallback to searching the entire message
        for lang in self.supported_languages:
            if lang in message_lower:
                return lang.capitalize() if lang != 'c#' else 'C#'
        return 'Python'  # default


    def _extract_code_blocks(self, message):
        """Extract code from markdown code blocks using state machine approach"""
        lines = message.split('\n')
        in_code_block = False
        code_lines = []
        code_blocks = []
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('```'):
                if in_code_block:
                    # End of code block
                    if code_lines:
                        code_blocks.append('\n'.join(code_lines))
                    code_lines = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
            elif in_code_block:
                code_lines.append(line)  # Keep original formatting
        
        # Return the first non-empty code block, or all code joined
        for block in code_blocks:
            if block.strip():
                return block.strip()
        
        return ''


    def get_supported_languages(self):
        """Get list of supported programming languages"""
        return [lang.capitalize() if lang != 'c#' else 'C#' for lang in self.supported_languages]

    def get_supported_patterns(self):
        """Get list of supported patterns"""
        return [
            'write_code',
            'refactor_code', 
            'write_test',
            'fix_bug',
            'explain_code',
            'add_docs'
        ]