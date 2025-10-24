# app/utils/pattern_detector.py
import re

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
        
        elif 'fix_bug' in message_lower:
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
        # Make the regex case-insensitive for the key names
        pattern_match = re.search(r'###\s*Pattern:\s*(.+?)(?=###|\n\n|\n```|$)', message, re.IGNORECASE | re.DOTALL)
        issue_match = re.search(r'###\s*Issue:\s*(.+?)(?=###|\n\n|\n```|$)', message, re.IGNORECASE | re.DOTALL)
        rules_match = re.search(r'###\s*Rules:\s*(.+?)(?=###|\n\n|\n```|$)', message, re.IGNORECASE | re.DOTALL)
        code_match = re.search(r'```(\w+)?\s*(.*?)```', message, re.DOTALL)
        
        if pattern_match and code_match:
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
                clean_issue = issue_match.group(1).strip() if issue_match else ''
                clean_rules = rules_match.group(1).strip() if rules_match else ''
                
                return {
                    'pattern': internal_pattern,
                    'issue': clean_issue,
                    'rules': clean_rules,
                    'code': code_match.group(2).strip(),
                    'language': code_match.group(1) if code_match.group(1) else 'Python'
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
            
            return content_after_pattern
        return message

    def _extract_issue_description(self, message):
        """Extract issue description after fix_bug pattern"""
        if 'fix_bug' in message.lower():
            # Get everything after fix_bug
            content = message[message.lower().find('fix_bug') + len('fix_bug'):].strip()
            content = content.lstrip(':').strip()
            
            # If there's code, extract the issue part before the code
            code = self._extract_code_blocks(content)
            if code:
                return content.replace(f"```{code}```", "").strip()
            return content
        return "Unknown issue"

    def _extract_language(self, message):
        """Extract programming language from message"""
        message_lower = message.lower()
        for lang in self.supported_languages:
            if lang in message_lower:
                return lang.capitalize() if lang != 'c#' else 'C#'
        return 'Python'  # default

    def _extract_code_blocks(self, message):
        """Extract code from markdown code blocks or inline code"""
        # Match ```language\ncode\n``` or ```code```
        code_blocks = re.findall(r'```(?:\w+)?\n?(.*?)\n?```', message, re.DOTALL)
        if code_blocks:
            return code_blocks[0].strip()
        
        # Match inline code `code`
        inline_code = re.findall(r'`([^`]+)`', message)
        if inline_code:
            return inline_code[0]
        
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