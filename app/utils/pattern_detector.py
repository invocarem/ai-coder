# app/utils/pattern_detector.py
import re
import logging
from .multi_processor_state_machine import MultiProcessorStateMachine

logger = logging.getLogger(__name__)

class PatternDetector:
    # --------------------------------------------------------------------- #
    #                     Construction / basic data
    # --------------------------------------------------------------------- #
    def __init__(self):
        # keep the original lower‑case list (used internally)
        self.supported_languages = [
            'python', 'javascript', 'java', 'c++', 'c#', 'go',
            'rust', 'php', 'ruby', 'swift', 'typescript', 'bash',
            'awk', 'gnuplot', 'latin'
        ]
        self.state_machine = MultiProcessorStateMachine()

    # --------------------------------------------------------------------- #
    #                     Public helper API (new / restored)
    # --------------------------------------------------------------------- #
    # NOTE: the original repository only exposed *extract_code_blocks*.
    # The test‑suite, however, also expects a few extra public helpers.
    # They are now provided as thin wrappers around the private
    # implementations that the state‑machine uses.

    def extract_code_blocks(self, message: str) -> str:
        """
        Public wrapper kept for backward compatibility.
        Delegates to the private implementation that actually does the work.
        """
        return self._extract_code_blocks(message)

    def extract_language(self, message: str) -> str:
        """
        Public wrapper for language extraction.
        The tests call ``detector.extract_language`` while the core logic lives
        in ``_extract_language``.
        """
        return self._extract_language(message)

    def get_supported_languages(self):
        """
        Return the list of supported languages in *title‑case* (the form
        expected by the tests).  Internally we keep a lower‑case list, so we
        simply capitalise each entry.
        """
        # Title‑case gives “Javascript”, “C++”, “C#”, etc.
        return [lang.title() for lang in self.supported_languages]

    def get_supported_patterns(self):
        """
        Return the canonical list of patterns that the detector recognises.
        The list mirrors the patterns that the state‑machine knows about.
        """
        return [
            'write_code',
            'refactor_code',
            'write_test',
            'fix_bug',
            'explain_code',
            'add_docs'
        ]

    # --------------------------------------------------------------------- #
    #                     Core detection entry point
    # --------------------------------------------------------------------- #
    def detect_pattern(self, message):
        """
        Detect a pattern and return a structured dict.

        ``message`` can be either a raw string (the original use‑case) **or**
        a list of ``{\"role\": ..., \"content\": ...}`` dictionaries that
        represents a chat‑style payload (the new test case).
        """
        # --------------------------------------------------------------- #
        # 1️⃣  Chat‑style payload handling
        # --------------------------------------------------------------- #
        if isinstance(message, list):
            return self._detect_from_chat_payload(message)

        # --------------------------------------------------------------- #
        # 2️⃣  Structured‑text handling (original implementation)
        # --------------------------------------------------------------- #
        logger.debug(f"Pattern detection for message: {str(message)[:100]}...")
        # first try the state‑machine (keeps existing behaviour)
        result = self.state_machine.process(message)
        if result:
            logger.info(
                f"✅ {'EXPLICIT' if result['specified_processor'] else 'AUTO‑DETECTED'} "
                f"- Pattern '{result['pattern_data']['pattern']}' → Processor: {result['processor']}"
            )
            return result

        # fall back to the ad‑hoc parser we added for the tests
        parsed = self._parse_structured_format(message)
        if parsed:
            # mimic the shape of the state‑machine output
            return {
                'processor': self.detect_processor_from_pattern(parsed['pattern']),
                'pattern_data': parsed,
                'specified_processor': False,
                'pattern': parsed['pattern'],
                **parsed
            }

        logger.info("❌ No valid structured pattern found")
        return None

    # --------------------------------------------------------------------- #
    #                     Chat‑payload specific logic
    # --------------------------------------------------------------------- #
    def _detect_from_chat_payload(self, payload):
        """
        Parse a list of ``{\"role\": ..., \"content\": ...}`` messages.

        Expected keys inside the content blocks:
        - ``processor`` – the processor name (e.g. ``code``)
        - ``pattern``   – the pattern name (e.g. ``custom``)
        - any additional key/value pairs (e.g. ``prompt``)

        The function builds a dict that mirrors the shape returned by the
        state‑machine for consistency with the rest of the codebase.
        """
        data = {}
        processor = None
        pattern = None

        # Regexes that tolerate extra whitespace and case‑insensitivity
        proc_re = re.compile(r'###\s*processor\s*:\s*(\w+)', re.IGNORECASE)
        pat_re  = re.compile(r'###\s*pattern\s*:\s*(\w+)', re.IGNORECASE)
        kv_re   = re.compile(r'###\s*([\w-]+)\s*:\s*(.+)', re.IGNORECASE)

        for entry in payload:
            content = entry.get('content', '')
            # Processor line
            m = proc_re.search(content)
            if m:
                processor = m.group(1).strip()
                continue
            # Pattern line
            m = pat_re.search(content)
            if m:
                pattern = m.group(1).strip()
                continue
            # Generic key/value lines
            m = kv_re.search(content)
            if m:
                key = m.group(1).strip().lower()
                value = m.group(2).strip()
                data[key] = value

        # If we didn't find a processor we still try to infer it from the pattern
        if not processor and pattern:
            processor = self.detect_processor_from_pattern(pattern)

        if not processor:
            # nothing we can do
            return None

        # Normalise processor name to the convention used elsewhere
        processor_name = f"{processor}_processor"

        # Build the final structure
        pattern_data = {'pattern': pattern} if pattern else {}
        pattern_data.update(data)

        return {
            'processor': processor_name,
            'pattern_data': pattern_data,
            'specified_processor': True,
            'pattern': pattern,
            **pattern_data
        }

    # --------------------------------------------------------------------- #
    #                     Private helper methods (used by tests)
    # --------------------------------------------------------------------- #
    def _extract_code_blocks(self, message: str) -> str:
        """
        Extract the first code block from *message*.

        1. Look for fenced markdown blocks (``` … ```). The language hint after
           the opening fence is ignored – we only need the raw code.
        2. If no fenced block is found, fall back to a legacy ``### Code`` marker
           and return everything that follows until the next ``###`` header or
           the end of the string.
        """
        # 1️⃣ fenced block
        fenced = re.findall(r'```(?:\w+)?\s*\n(.*?)```', message, re.DOTALL)
        if fenced:
            return fenced[0].strip()

        # 2️⃣ legacy “### Code” marker
        code_marker = re.search(r'###\s*Code\s*(?:\n|$)', message, re.IGNORECASE)
        if code_marker:
            start = code_marker.end()
            # stop at the next header (###) or the end of the string
            end_match = re.search(r'\n###\s', message[start:])
            end = start + end_match.start() if end_match else len(message)
            return message[start:end].strip()

        return ""

    def _extract_language(self, message: str) -> str:
        """
        Determine the programming language for a block.

        - First tries a ``### Language: <lang>`` header.
        - Then tries the language identifier after a fenced block (e.g. `````swift````).
        - Falls back to ``Python`` (the default used throughout the project).
        """
        # Header form
        hdr = re.search(r'###\s*Language\s*:\s*([\w\+#]+)', message, re.IGNORECASE)
        if hdr:
            return hdr.group(1).strip()

        # fenced block language hint
        fence = re.search(r'```(\w+)', message)
        if fence:
            return fence.group(1).strip()

        return 'Python'

    def _parse_structured_format(self, message: str):
        """
        Very permissive parser for the ``### Header: value`` style format.

        Returns a ``dict`` with the extracted fields or ``None`` if the
        ``Pattern`` header is missing or unknown.
        """
        # Normalise line endings
        lines = [ln.rstrip() for ln in message.splitlines()]

        # Helper to pull a multi‑line value after a header
        def pull_value(start_idx):
            values = []
            for ln in lines[start_idx + 1:]:
                if re.match(r'^\s*###\s*\w+', ln):   # next header
                    break
                values.append(ln)
            return "\n".join(v for v in values if v).strip()

        data = {}
        i = 0
        while i < len(lines):
            line = lines[i]
            # Pattern header (mandatory)
            m = re.match(r'^\s*###\s*Pattern\s*:?\s*(\w+)', line, re.IGNORECASE)
            if m:
                data['pattern'] = m.group(1).strip()
                i += 1
                continue

            # Generic key/value header (allow optional colon)
            m = re.match(r'^\s*###\s*([\w-]+)\s*:?\s*(.*)', line, re.IGNORECASE)
            if m:
                key = m.group(1).lower()
                # If the value is on the same line capture it, otherwise pull multiline
                if m.group(2):
                    value = m.group(2).strip()
                else:
                    value = pull_value(i)
                data[key] = value
                i += 1
                continue

            i += 1

        # Must have a known pattern
        if 'pattern' not in data:
            return None
        if data['pattern'] not in self.get_supported_patterns():
            return None

        # Normalise language
        if 'language' in data:
            data['language'] = data['language'].strip()
        else:
            data['language'] = self._extract_language(message)

        # Extract code (if any)
        data['code'] = self._extract_code_blocks(message)

        # Ensure optional fields exist so tests don’t KeyError
        for opt in ('issue', 'task', 'rules', 'prompt'):
            data.setdefault(opt, '')

        return data

    # --------------------------------------------------------------------- #
    #                     Misc helper utilities
    # --------------------------------------------------------------------- #
    def _extract_issue_description(self, message: str) -> str:
        """Extract the text after ``fix_bug:``."""
        m = re.search(r'fix[_-]?bug\s*[:\-]\s*(.+)', message, re.IGNORECASE)
        return m.group(1).strip() if m else ''

    def _extract_task_after_pattern(self, message: str, pattern: str) -> str:
        """Extract the task description that follows ``<pattern>:``."""
        esc = re.escape(pattern)
        m = re.search(rf'{esc}\s*[:\-]\s*(.+)', message, re.IGNORECASE)
        return m.group(1).strip() if m else ''

    # --------------------------------------------------------------------- #
    #                     Existing public API (unchanged)
    # --------------------------------------------------------------------- #
    def detect_processor_from_pattern(self, pattern):
        """
        Detect which processor handles a specific pattern
        """
        processors = self.get_supported_processors()
        for processor_key, processor_info in processors.items():
            if pattern in processor_info['patterns']:
                return processor_key
        return None

    def is_pattern_supported(self, pattern):
        """
        Check if a pattern is supported by any processor
        """
        return self.detect_processor_from_pattern(pattern) is not None

    def get_processor_for_pattern(self, pattern):
        """
        Get the processor name for a specific pattern
        """
        processor_key = self.detect_processor_from_pattern(pattern)
        if processor_key:
            processors = self.get_supported_processors()
            return processors[processor_key]['name']
        return None

    # --------------------------------------------------------------------- #
    #                     Legacy compatibility helpers
    # --------------------------------------------------------------------- #
    def get_supported_processors(self):
        """
        Get all supported processors with their patterns
        """
        return self.state_machine.get_supported_processors()

    def get_processor_patterns(self, processor):
        """
        Get patterns for a specific processor
        """
        return self.state_machine.get_processor_patterns(processor)

    def get_pattern_requirements(self, pattern):
        """
        Get required fields for a specific pattern
        """
        return self.state_machine.get_pattern_requirements(pattern)

    def validate_pattern_request(self, pattern_data):
        """
        Validate if pattern data has all required fields
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


# ------------------------------------------------------------------------- #
# Legacy factory (kept for backwards compatibility)
# ------------------------------------------------------------------------- #
def create_pattern_detector():
    """Factory function to create a pattern detector (for backward compatibility)"""
    return PatternDetector()
