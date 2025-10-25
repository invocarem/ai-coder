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
        """Parse structured ###Key: value format with code blocks"""
        # Extract pattern name
        pattern_match = re.search(r'###\s*Pattern:\s*(.+?)(?=###|\n\n|\n```|$)', message, re.IGNORECASE | re.DOTALL)
        
        # Extract task - capture only the content after "Task:"
        task_match = re.search(r'###\s*Task:\s*(.+?)(?=###|\n\n|\n```|$)', message, re.IGNORECASE | re.DOTALL)
        
        # Extract language - capture only the content after "Language:"
        language_match = re.search(r'###\s*Language:\s*(.+?)(?=###|\n\n|\n```|$)', message, re.IGNORECASE | re.DOTALL)
        
        # Extract issue description
        issue_match = re.search(r'###\s*Issue:\s*(.+?)(?=###\s*Rules:|\n\n|\n```|$)', message, re.IGNORECASE | re.DOTALL)
        
        # Extract rules - capture everything after "Rules:" until next ### or code block
        rules_match = re.search(r'###\s*Rules:\s*(.+?)(?=###|\n```|$)', message, re.IGNORECASE | re.DOTALL)
        
        # Extract code from ### Code section (with or without colon)
        code_match_structured = re.search(r'###\s*Code:?\s*\n?(.+?)(?=###|\n```|$)', message, re.IGNORECASE | re.DOTALL)
        
        # Extract code using robust method
        code = self._extract_code_blocks(message)
        language_from_code = 'Python'
        
        # Try to detect language from code blocks
        code_blocks = re.findall(r'```(\w+)?\s*\n', message)
        if code_blocks:
            for lang in code_blocks:
                if lang and lang.lower() in self.supported_languages:
                    language_from_code = lang.capitalize() if lang != 'c#' else 'C#'
                    break
        
        if pattern_match:
            pattern_name = pattern_match.group(1).strip().lower()
            
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
            
            internal_pattern = pattern_map.get(pattern_name)
            if internal_pattern:
                # Clean extracted values
                clean_task = task_match.group(1).strip() if task_match else ''
                clean_language = language_match.group(1).strip() if language_match else ''
                clean_issue = issue_match.group(1).strip() if issue_match else ''
                clean_rules = rules_match.group(1).strip() if rules_match else ''
                
                # Remove any ### patterns that might have been captured
                clean_task = re.sub(r'###\s*\w+:?', '', clean_task).strip()
                clean_language = re.sub(r'###\s*\w+:?', '', clean_language).strip()
                clean_issue = re.sub(r'###\s*\w+:?', '', clean_issue).strip()
                clean_rules = re.sub(r'###\s*\w+:?', '', clean_rules).strip()
                
                # Use language from ### Language: if provided, otherwise from code block
                final_language = clean_language or language_from_code
                
                # Debug logging
                logger.info(f"Pattern detected: {internal_pattern}")
                logger.info(f"Language: {final_language}")
                logger.info(f"Code length: {len(code)}")
                logger.info(f"Issue: {clean_issue}")
                logger.info(f"Rules: {clean_rules}")
                
                return {
                    'pattern': internal_pattern,
                    'task': clean_task,
                    'issue': clean_issue,
                    'rules': clean_rules,
                    'code': code,
                    'language': final_language
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
        """Extract code from markdown code blocks"""
        # Method 1: Simple range approach - most reliable
        start_idx = message.find('```')
        if start_idx != -1:
            # Find the end of the opening backticks line
            start_idx = message.find('\n', start_idx)
            if start_idx != -1:
                # Find the last closing backticks
                end_idx = message.rfind('```')
                if end_idx > start_idx:
                    code_content = message[start_idx+1:end_idx].strip()
                    if code_content:
                        return code_content
        
        # Method 2: Regex approach as fallback
        try:
            code_blocks = re.findall(r'```(?:\w+)?\s*\n(.*?)```', message, re.DOTALL)
            if code_blocks:
                for code_content in code_blocks:
                    if code_content.strip():
                        return code_content.strip()
        except Exception:
            pass
        
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