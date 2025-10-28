# app/utils/pattern_detector.py
import re
import logging
logger = logging.getLogger(__name__)

# State constants
STATE_START = 0
STATE_IN_PATTERN = 1
STATE_IN_TASK = 2
STATE_IN_LANGUAGE = 3
STATE_IN_ISSUE = 4
STATE_IN_RULES = 5
STATE_IN_CODE = 6
STATE_IN_LATIN = 7

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
                'pattern': 'write_code',
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
        elif 'improve_code' in message_lower:
            code = self._extract_code_blocks(message)
            return {
                'pattern': 'improve_code',
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
        
        # Parse using state machine
        result = self._parse_with_state_machine(lines)
        
        # Process and validate results
        return self._process_parsed_results(result)

    def _parse_with_state_machine(self, lines):
        """State machine implementation for parsing structured format"""
        current_state = STATE_START
        
        # Results storage
        result = {
            'pattern': None,
            'task': "",
            'language': "",
            'issue': "",
            'rules': [],
            'code_lines': []
        }
        
        for i, line in enumerate(lines):
            current_state, should_continue = self._process_line(
                line, i, lines, current_state, result
            )
            if not should_continue:
                break
        
        return result

    def _process_line(self, line, line_index, all_lines, current_state, result):
        """Process a single line in the state machine"""
        stripped_line = line.strip()
        
        # Check for state transitions
        if stripped_line.startswith('###'):
            return self._handle_header_line(stripped_line, line_index, all_lines, current_state, result)
        elif stripped_line.startswith('```'):
            return self._handle_code_block_marker(stripped_line, current_state, result)
        else:
            return self._handle_content_line(stripped_line, line, current_state, result)

    def _handle_header_line(self, stripped_line, line_index, all_lines, current_state, result):
        """Handle ### header lines and transition states"""
        # If we're in CODE state and encounter any ### marker, end the code block
        if current_state == STATE_IN_CODE:
            current_state = STATE_START
        
        # Extract key and value from header
        key_name, value_part = self._extract_header_key_value(stripped_line)
        
        if not key_name:
            return current_state, True  # Continue processing
        
        # Handle different header types
        if key_name == 'pattern':
            current_state = STATE_IN_PATTERN
            result['pattern'] = value_part or self._get_value_from_next_line(line_index, all_lines)
        elif key_name == 'task':
            current_state = STATE_IN_TASK
            if value_part:
                result['task'] = value_part
            else:
                result['task'] = self._get_value_from_next_line(line_index, all_lines) or ""
        elif key_name == 'language':
            current_state = STATE_IN_LANGUAGE
            if value_part:
                result['language'] = value_part
            else:
                result['language'] = self._get_value_from_next_line(line_index, all_lines) or ""
        elif key_name == 'issue':
            current_state = STATE_IN_ISSUE
            if value_part:
                result['issue'] = value_part
            else:
                result['issue'] = self._get_value_from_next_line(line_index, all_lines) or ""
        elif key_name == 'rules':
            current_state = STATE_IN_RULES
            if value_part:
                result['rules'].append(value_part)
            else:
                next_line_value = self._get_value_from_next_line(line_index, all_lines)
                if next_line_value:
                    result['rules'].append(next_line_value)
        elif key_name == 'code':
            current_state = STATE_IN_CODE
        
        return current_state, True

    def _handle_code_block_marker(self, stripped_line, current_state, result):
        """Handle ``` code block markers"""
        if current_state == STATE_IN_CODE:
            # Ending code block with ```
            return STATE_START, True
        else:
            # Starting code block with ```
            current_state = STATE_IN_CODE
            # Extract language from code block if not already set
            if not result['language']:
                lang_match = re.match(r'```(\w+)', stripped_line)
                if lang_match:
                    potential_lang = lang_match.group(1).lower()
                    if potential_lang in self.supported_languages:
                        result['language'] = potential_lang.capitalize() if potential_lang != 'c#' else 'C#'
            return current_state, True

    def _handle_content_line(self, stripped_line, original_line, current_state, result):
        """Handle regular content lines based on current state"""
        if current_state == STATE_IN_PATTERN and not result['pattern']:
            result['pattern'] = stripped_line
        elif current_state == STATE_IN_TASK:
            result['task'] = self._append_to_field(result['task'], stripped_line)
        elif current_state == STATE_IN_LANGUAGE and not result['language']:
            result['language'] = stripped_line
        elif current_state == STATE_IN_ISSUE:
            result['issue'] = self._append_to_field(result['issue'], stripped_line)
        elif current_state == STATE_IN_RULES:
            if stripped_line:
                result['rules'].append(stripped_line)
        elif current_state == STATE_IN_CODE:
            result['code_lines'].append(original_line)  # Keep original line
        elif current_state == STATE_IN_LATIN:
            result['word_form'] = self._append_to_field(result.get('word_form', ''), stripped_line)
        return current_state, True

    def _extract_header_key_value(self, stripped_line):
        """Extract key and value from ### header line"""
        key_match = re.match(r'###\s*(\w+):?\s*(.*)', stripped_line, re.IGNORECASE)
        if key_match:
            return key_match.group(1).lower(), key_match.group(2).strip()
        return None, None

    def _get_value_from_next_line(self, current_index, all_lines):
        """Get value from next line if it's not another header or code block"""
        if current_index + 1 < len(all_lines):
            next_line = all_lines[current_index + 1].strip()
            if not next_line.startswith('###') and not next_line.startswith('```'):
                return next_line
        return None

    def _append_to_field(self, field, new_content):
        """Append new content to a field with proper newline handling"""
        if field and new_content:
            return field + '\n' + new_content
        elif new_content:
            return new_content
        else:
            return field

    def _process_parsed_results(self, result):
        """Process and validate the parsed results"""
        pattern = result['pattern']
        if not pattern:
            return None
        
        pattern = pattern.strip().lower()
        
        # Map pattern names to internal patterns
        pattern_map = {
            'fix_bug': 'fix_bug',
            'bug_fix': 'fix_bug',
            'improve_code': 'improve_code',
            'write_code': 'write_code', 
            'refactor_code': 'refactor_code',
            'write_test': 'write_tests',
            'explain_code': 'explain_code',
            'add_docs': 'add_docs',
            'custom': 'custom'
        }
        
        internal_pattern = pattern_map.get(pattern)
        if not internal_pattern:
            return None
        
        # Prepare final result
        code = '\n'.join(result['code_lines']).strip()
        
        # If no language specified but we detected from code block, use it
        if not result['language']:
            language_from_code = self._extract_language('\n'.join(result['code_lines']))
            if language_from_code != 'Python':  # Only use if not default
                result['language'] = language_from_code
        
        return {
            'pattern': internal_pattern,
            'task': result['task'].strip(),
            'issue': result['issue'].strip(),
            'rules': '; '.join(result['rules']).strip(),
            'code': code,
            'language': result['language'].strip() or 'Python'
        }

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
        """Extract issue description after fix_bug or improve_code pattern"""
        message_lower = message.lower()
        
        # Handle both fix_bug and improve_code patterns
        patterns_to_check = ['fix_bug', 'improve_code']
        
        for pattern in patterns_to_check:
            if pattern in message_lower:
                # Get everything after the pattern
                content = message[message_lower.find(pattern) + len(pattern):].strip()
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
        """Extract code from markdown code blocks or from '### Code' headers.

        Behavior:
        - First, try to find fenced ```code``` blocks (existing behavior).
        - If none found, look for '### Code' headers and collect following lines
          (skip the header line, allow one or more blank lines before actual code).
        - Return the first non-empty code block found, else return empty string.
        """
        lines = message.split('\n')

        # 1) Try fenced code blocks first (preserve original formatting)
        in_code_block = False
        code_lines = []
        code_blocks = []

        for line in lines:
            stripped = line.strip()

            if stripped.startswith('```'):
                if in_code_block:
                    # End of fenced code block
                    if code_lines:
                        code_blocks.append('\n'.join(code_lines))
                    code_lines = []
                    in_code_block = False
                else:
                    # Start of fenced code block
                    in_code_block = True
            elif in_code_block:
                code_lines.append(line)  # Keep original formatting

        # Return first non-empty fenced block if present
        for block in code_blocks:
            if block.strip():
                return block.strip()

        # 2) No fenced blocks found — look for '### Code' style headers
        header_pattern = re.compile(r'###\s*code\b', re.IGNORECASE)
        n = len(lines)
        i = 0
        while i < n:
            if header_pattern.match(lines[i].strip()):
                # Collect lines after this header until next '###' header or end
                i += 1  # move to the line after the header
                # collect lines (preserve formatting), but skip leading blank lines
                collected = []
                # skip initial blank lines but allow blank lines once code has started
                code_started = False
                while i < n:
                    stripped = lines[i].strip()
                    if stripped.startswith('###'):
                        break  # next header starts, end this code block
                    # If the line is not empty, mark code_started
                    if stripped != '':
                        code_started = True
                        collected.append(lines[i])
                    else:
                        # only append blank lines if we've already started capturing code
                        if code_started:
                            collected.append(lines[i])
                        else:
                            # skip leading blank lines
                            pass
                    i += 1

                block = '\n'.join(collected).strip()
                if block:
                    return block  # return first non-empty code block found
                # otherwise continue searching for the next '### Code'
            else:
                i += 1

        # Nothing found
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


        # In pattern_detector.py - add the new patterns
    def detect_latin_pattern(self, message):
        """Detect various types of Latin analysis requests"""
        message_lower = message.lower()
        
        # Check for specific word analysis
        latin_word = self._extract_target_latin_word(message)
        if latin_word:
            return {
                'pattern': 'latin_analysis',
                'word_form': latin_word,
                'context': self._extract_context(message),
                'sentence': self._extract_sentence_context(message)
            }
        
        # Check for verse lemma analysis
        if any(phrase in message_lower for phrase in ['lemmas for', 'lemma of', 'analyze verse', 'word by word']):
            verse = self._extract_latin_verse(message)
            if verse:
                return {
                    'pattern': 'verse_lemmas', 
                    'verse': verse,
                    'translation': self._extract_translation(message)
                }
        
        return None

    def _detect_patristic_pattern(self, message):
        """Detect requests for Church Father expositions"""
        message_lower = message.lower()
        
        patristic_indicators = [
            'augustine', 'church father', 'patristic', 'exposition',
            'commentary', 'homily', 'sermon', 'treatise'
        ]
        
        biblical_indicators = [
            'psalm', 'gospel', 'epistle', 'verse', 'scripture'
        ]
        
        if any(indicator in message_lower for indicator in patristic_indicators):
            if any(indicator in message_lower for indicator in biblical_indicators):
                return {
                    'pattern': 'patristic_exposition',
                    'passage': self._extract_bible_reference(message),
                    'church_father': self._extract_church_father(message),
                    'translation': self._extract_translation(message)
                }
        
        return None

    def _extract_target_latin_word(self, message):
        """Extract the specific Latin word to analyze"""
        # Look for quoted Latin words
        quoted_match = re.search(r'[\'"`](\w+)[\'"`]', message)
        if quoted_match:
            return quoted_match.group(1)
        
        # Look for "word X" or "analyze X" patterns
        analyze_match = re.search(r'(?:word|analyze|parse)\s+(\w+)', message, re.IGNORECASE)
        if analyze_match:
            return analyze_match.group(1)
        
        # Look for obvious Latin words in context
        words = message.split()
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if self._looks_latin(clean_word):
                return clean_word
        
        return None

    def _extract_latin_verse(self, message):
        """Extract Latin verse text"""
        # Look for quoted Latin text
        quoted_match = re.search(r'[\'"`]([^\'"`]+)[\'"`]', message)
        if quoted_match:
            text = quoted_match.group(1)
            if any(word in text.lower() for word in ['qui', 'et', 'non', 'in', 'est']):
                return text
        
        return None

    def _extract_church_father(self, message):
        """Extract which Church Father is requested"""
        message_lower = message.lower()
        
        if 'augustine' in message_lower:
            return 'Augustine'
        elif 'ambrose' in message_lower:
            return 'Ambrose'
        elif 'jerome' in message_lower:
            return 'Jerome'
        elif 'gregory' in message_lower:
            return 'Gregory the Great'
        elif 'john chrysostom' in message_lower:
            return 'John Chrysostom'
        else:
            return 'Augustine'  # default

    def _looks_latin(self, word):
        """Heuristic to check if a word looks Latin"""
        if len(word) < 3:
            return False
        
        latin_indicators = [
            word.endswith(('us', 'um', 'a', 'ae', 'i', 'o', 'is', 'it', 'nt', 'tur', 'mur')),
            'ae' in word,
            'ii' in word,
            'x' in word  # Common in Latin
        ]
        
        return any(latin_indicators)