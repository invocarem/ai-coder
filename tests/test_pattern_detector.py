# tests/test_pattern_detector.py
import pytest
import re
from app.utils.pattern_detector import PatternDetector


class TestPatternDetector:
    """Test suite for PatternDetector class"""

    @pytest.fixture
    def detector(self):
        """Create a PatternDetector instance for testing"""
        return PatternDetector()

    def test_initialization(self, detector):
        """Test that PatternDetector initializes correctly"""
        assert detector.supported_languages is not None
        assert len(detector.supported_languages) > 0
        assert 'python' in detector.supported_languages
        assert 'swift' in detector.supported_languages

    def test_detect_pattern_explain_code_structured(self, detector):
        """Test detecting explain_code pattern with structured format"""
        message = """### Pattern: explain_code
### Language: Swift

```swift
private let text = [
    /* 1 */ "Benedictus Dominus die quotidie; prosperum iter faciet nobis Deus salutarium nostrorum.",
    /* 2 */ "Deus noster, Deus salvos faciendi; et Domini Domini exitus mortis."
]
```"""

        result = detector.detect_pattern(message)
        
        assert result is not None
        assert result['pattern'] == 'explain_code'
        assert result['language'] == 'Swift'
        assert len(result['code']) > 0
        assert 'private let text' in result['code']
        assert 'Benedictus Dominus' in result['code']

    def test_detect_pattern_fix_bug_structured(self, detector):
        """Test detecting fix_bug pattern with structured format"""
        message = """### Pattern: fix_bug
### Issue: /* N */ is non-sequencial
### Language: swift
### Rules:
- A string trailing with ',' is a vaild array element in Swift.
- remove /* N */ comment in the code

```swift
private let text = [
    /* 1 */ "Benedictus Dominus die quotidie; prosperum iter faciet nobis Deus salutarium nostrorum.",
    /* 2 */ "Deus noster, Deus salvos faciendi; et Domini Domini exitus mortis."
]
```"""

        result = detector.detect_pattern(message)
        
        assert result is not None
        assert result['pattern'] == 'fix_bug'
        assert result['language'].lower() == 'swift'
        assert result['issue'] == '/* N */ is non-sequencial'
        assert 'A string trailing' in result['rules']
        assert len(result['code']) > 0

    def test_detect_pattern_write_code_structured(self, detector):
        """Test detecting write_code pattern with structured format"""
        message = """### Pattern: write_code
### Task: write code to add two numbers
### Language: awk

Some additional text here."""

        result = detector.detect_pattern(message)
        
        assert result is not None
        assert result['pattern'] == 'write_code'
        assert result['language'].lower() == 'awk'
        assert 'write code to add two numbers' in result['task']

    def test_detect_pattern_no_pattern(self, detector):
        """Test detecting no pattern in message"""
        message = "Just a regular message without any pattern markers"
        
        result = detector.detect_pattern(message)
        
        assert result is None


    def test_extract_code_blocks_with_blank_lines(self, detector):
        """Test code block extraction with blank lines"""
        message = """### Pattern: explain_code
    ### Language: Swift
    ### Code

    private let text = [
        /* 1 */ "Benedictus Dominus die quotidie; prosperum iter faciet nobis Deus salutarium nostrorum."
    ]"""

        code = detector._extract_code_blocks(message)
        
        assert code is not None
        assert len(code) > 0
        assert 'private let text' in code
        assert 'Benedictus Dominus' in code

    def test_extract_code_blocks_multiple_blocks(self, detector):
        """Test code block extraction with multiple code blocks"""
        message = """First code block:
    ### Code
    print("hello")
    Some text in between
    ### Code
    let greeting = "hello"
    Last code block."""

        code = detector.extract_code_blocks(message)
        
        # Should extract the first non-empty code block
        assert code is not None
        assert len(code) > 0

    def test_extract_code_blocks_no_blocks(self, detector):
        """Test code block extraction when no code blocks exist"""
        message = "Just regular text without any code blocks"
        
        code = detector.extract_code_blocks(message)
        
        assert code == ''

    def test_extract_language_from_code_block(self, detector):
        """Test extracting language from code block identifier"""
        message = """### Code
    private let text = ["hello"]"""

        language = detector._extract_language(message)
        
        # Should fallback to default since no language specified
        assert language == 'Python'

    def test_extract_language_from_language_header(self, detector):
        """Test extracting language from ### Language: header"""
        message = """### Pattern: explain_code
    ### Language: Python
    ### Code
    print("hello")"""

        result = detector.detect_pattern(message)
        
        assert result is not None
        assert result['language'] == 'Python'

    def test_extract_language_fallback(self, detector):
        """Test language extraction fallback to default"""
        message = "Some message without explicit language"
        
        language = detector.extract_language(message)
        
        assert language == 'Python'  # Default

    def test_parse_structured_format_complete(self, detector):
        """Test complete structured format parsing"""
        message = """### Pattern: fix_bug
    ### Issue: variable not defined
    ### Language: python
    ### Rules:
    - Fix the undefined variable
    - Add proper initialization
    ### Code
    def test():
        return x  # x is not defined"""

        result = detector._parse_structured_format(message)
        
        assert result is not None
        assert result['pattern'] == 'fix_bug'
        assert result['issue'] == 'variable not defined'
        assert result['language'].lower() == 'python'
        assert 'Fix the undefined variable' in result['rules']
        assert 'def test():' in result['code']
        assert 'return x' in result['code']

    def test_parse_structured_format_no_code(self, detector):
        """Test structured format parsing without code blocks"""
        message = """### Pattern: write_code
    ### Task: create a function
    ### Language: javascript"""

        result = detector._parse_structured_format(message)
        
        assert result is not None
        assert result['pattern'] == 'write_code'
        assert result['task'] == 'create a function'
        assert result['language'].lower() == 'javascript'
        assert result['code'] == ''

    def test_parse_structured_format_invalid_pattern(self, detector):
        """Test structured format parsing with invalid pattern"""
        message = """### Pattern: invalid_pattern
    ### Language: python
    ### Code
    print("hello")"""

        result = detector._parse_structured_format(message)
        
        assert result is None

    def test_extract_issue_description_fix_bug(self, detector):
        """Test issue description extraction for fix_bug"""
        message = "fix_bug: variable not defined in function"
        
        issue = detector._extract_issue_description(message)
        
        assert issue == "variable not defined in function"

    def test_extract_task_after_pattern(self, detector):
        """Test task extraction after pattern name"""
        message = "write_code: create a sorting function in python"
        
        task = detector._extract_task_after_pattern(message, 'write_code')
        
        assert 'create a sorting function' in task

    def test_get_supported_languages(self, detector):
        """Test getting supported languages list"""
        languages = detector.get_supported_languages()
        
        assert len(languages) > 0
        assert 'Python' in languages
        assert 'Swift' in languages
        assert 'Javascript' in languages

    def test_get_supported_patterns(self, detector):
        """Test getting supported patterns list"""
        patterns = detector.get_supported_patterns()
        
        expected_patterns = [
            'write_code',
            'refactor_code', 
            'write_test',
            'fix_bug',
            'explain_code',
            'add_docs'
        ]
        
        for pattern in expected_patterns:
            assert pattern in patterns

    def test_debug_code_extraction(self, detector, capsys):
        """Test debug method for code extraction"""
        message = """### Pattern: explain_code
    ### Language: Swift
    ### Code
    private let text = ["hello"]"""
        
        # Test the actual extraction
        code = detector._extract_code_blocks(message)
        
        assert code is not None
        assert len(code) > 0
        assert 'private let text' in code

    def test_real_world_explain_code_scenario(self, detector):
        """Test the exact scenario that's failing"""
        message = """
        ### processor: code
        ### pattern: explain_code
    ### Language: Swift
    ```swift
    private let text = [
        /* 1 */ "Benedictus Dominus die quotidie; prosperum iter faciet nobis Deus salutarium nostrorum.",
        /* 2 */ "Deus noster, Deus salvos faciendi; et Domini Domini exitus mortis.",
        /* 3 */ "Verumtamen Deus confringet capita inimicorum suorum, verticem capilli perambulantium in delictis suis."
    ]"""
        
        result = detector.detect_pattern(message)

        print(f"Pattern: {result['pattern_data']['pattern'] if result else 'None'}")
        
        print(f"Language: {result['pattern_data']['language'] if result else 'None'}")
        print(f"Code length: {len(result['code']) if result and 'code' in result else 0}")
        if result and 'code' in result and result['code']:
            print(f"Code preview: {result['code'][:100]}...")
        
        assert result is not None
        assert result['pattern'] == 'explain_code'
        assert result['language'] == 'Swift'
        assert len(result['code']) > 0
        assert 'private let text' in result['code']
        assert 'Benedictus Dominus' in result['code']

    def test_code_extraction_with_comments(self, detector):
        """Test code extraction with extensive comments like your Swift example"""
        message = """### Pattern: explain_code
        ### Language: Swift
        ### Code
        private let text = [
            /* 1 */ "Benedictus Dominus die quotidie; prosperum iter faciet nobis Deus salutarium nostrorum.",
            /* 2 */ "Deus noster, Deus salvos faciendi; et Domini Domini exitus mortis.",
            /* 3 */ "Verumtamen Deus confringet capita inimicorum suorum, verticem capilli perambulantium in delictis suis.",
            /* 4 */ "Dixit Dominus: Ex Basan convertam, convertam in profundum maris."
        ]"""
        
        result = detector.detect_pattern(message)
        
        assert result is not None
        assert result['pattern'] == 'explain_code'
        assert result['language'] == 'Swift'
        assert len(result['code']) > 0
        assert 'private let text' in result['code']
        assert 'Benedictus Dominus' in result['code']



    def test_state_machine_structured_format_basic(self, detector):
        """Test state machine parsing with basic structured format"""
        message = """### Pattern: explain_code
        ### Language: Swift
        ### Code
        private let text = ["hello"]"""
        
        result = detector._parse_structured_format(message)
        
        if result:
            print(f"DEBUG - Code content: '{result['code']}'")
            print(f"DEBUG - Code length: {len(result['code'])}")
            print(f"DEBUG - Code repr: {repr(result['code'])}")

        assert result is not None
        assert result['pattern'] == 'explain_code'
        assert result['language'] == 'Swift'
        assert 'private let text' in result['code']

    def test_state_machine_multiline_values(self, detector):
        """Test state machine with multi-line task and issue"""
        message = """### Pattern: fix_bug
        ### Task: This is a multi-line
        task description that continues
        on multiple lines
        ### Language: python
        ### Issue: The issue also spans
        multiple lines for clarity
        ### Code
        def test():
            return x"""
            
        result = detector._parse_structured_format(message)
        
        assert result is not None
        assert result['pattern'] == 'fix_bug'
        assert 'multi-line\ntask description' in result['task']
        assert 'spans\nmultiple lines' in result['issue']
        assert 'def test():' in result['code']

    def test_state_machine_mixed_markers(self, detector):
        """Test state machine with mixed ### and ``` markers"""
        message = """### Pattern: write_code
        ### Language: javascript
        ### Task: Create a function
        ```javascript
        function hello() {
            return "world";
        }
        ```
        Some explanation here."""
        result = detector._parse_structured_format(message)

        assert result is not None
        assert result['pattern'] == 'write_code'
        assert result['language'] == 'javascript'
        assert 'function hello()' in result['code']
        assert 'Some explanation here.' not in result['code']


    def test_extract_code_block_for_psalm67b(self, detector):
        """Ensure _extract_code_blocks works when header tokens (Pattern, Language, Issue)
        are written without colons and with their values on the next line.
        The fenced Swift code block should still be detected correctly.
        """
        message = """### Pattern
        bug_fix

        ### Language
        Swift

        ### Issue
        Comment /* ... */ is not correct

        ### RULES

        1. Remove all comments in the array including /* 14 */ and /* 15 */
        2. Remove any leading whitespace of each string
        3. Capitalize the first character of each string (only the first character).
        4. Keep everything else exactly the same — punctuation, spelling, and order.

        ```swift
        private let text = [
            /* 1 */ "Benedictus Dominus die quotidie; prosperum iter faciet nobis Deus salutarium nostrorum.",
            /* 2 */ "Deus noster, Deus salvos faciendi; et Domini Domini exitus mortis.",
            /* 3 */ "Verumtamen Deus confringet capita inimicorum suorum, verticem capilli perambulantium in delictis suis.",
            /* 4 */ "Dixit Dominus: Ex Basan convertam, convertam in profundum maris.",
            /* 5 */ "Ut intingatur pes tuus in sanguine; lingua canum tuorum ex inimicis ab ipso.",
            /* 6 */ "Viderunt ingressus tuos, Deus, ingressus Dei mei, regis mei, qui est in sancto.",
            /* 7 */ "Praevenerunt principes conjuncti psallentibus, in medio juvencularum tympanistriarum.",
            /* 8 */ "In ecclesiis benedicite Deo Domino, de fontibus Israel.",
            /* 9 */ "Ibi Benjamin adolescentulus, in mentis excessu; ",
            "principes Juda, duces eorum; principes Zabulon, principes Nephthali.",
            /* 10 */ "Manda, Deus, virtuti tuae; confirma hoc, Deus, quod operatus es in nobis.",
            /* 11 */ "A templo tuo in Ierusalem, tibi offerent reges munera.",
            /* 12 */ "Increpa feras arundinis; congregatio taurorum in vaccis populorum, ut excludantur qui probati sunt argento;",
            " Dissipa gentes quae bella volunt. Venient legati ex Aegypto; Aethiopia praeveniet manus eius Deo.",
            /* 14 */ "Regna terrae, cantate Deo; psallite Domino.",
            /* 15 */ "Psallite Deo, qui ascendit super caelum caeli ad orientem; ",
            "ecce dabit voci suae vocem virtutis. Date gloriam Deo super Israel; magnificentia eius et virtus eius in nubibus.",
            /* 17 */ "Mirabilis Deus in sanctis suis; Deus Israel, ipse dabit virtutem et fortitudinem plebi suae; benedictus Deus."
        ]
        ```"""

        code = detector.extract_code_blocks(message)

        # Validation
        assert code is not None, "Expected non-None code extraction"
        assert len(code.strip()) > 0, "Expected non-empty code block"
        assert 'private let text' in code, "Swift code should be extracted"
        assert '/* 14 */' in code or '/* 15 */' in code, "Should include comment markers"
        assert 'Benedictus Dominus die quotidie' in code, "Expected recognizable psalm content"

    def test_detect_from_chat_format(self, detector):
        chat_payload = [
            {"role": "user", "content": "### processor: code"},
            {"role": "assistant", "content": "Got it"},
            {"role": "user", "content": "### pattern: custom"},
            {"role": "user", "content": "### prompt: Write a hello‑world function"},
        ]

        result = detector.detect_pattern(chat_payload)
        assert result is not None
        assert result["processor"] == "code_processor"
        assert result["pattern_data"]["prompt"].startswith("Write a hello")