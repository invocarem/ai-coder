### processor: psalm 
### pattern: psalm_word_analysis 
### word_form: abiit 
### psalm_number: 1 
### verse_number: 1 
### question: Analyze the Latin word "abiit" according to Augustine


### processor: psalm
### pattern: augustine_psalm_query
### psalm_number: 1
### verse_number: 1
### question: What does Augustine say about the word "abiit" in Psalm 1:1?

### processor: psalm
### pattern: augustine_psalm_query
### psalm_number: 1
### verse_number: 3
### question: What does Augustine say about the word "aquarem" in Psalm 1:3?


test augustine-mcp-tool with analyze_psalm, 
check the following input:
{
  "pattern_data": {
    "pattern": "augustine_psalm_query",
    "psalm_number": 1,
    "question": "What is Augustine's interpretation of 'blessed is the man'?"
  },
  "model": "llama3"
}
do nothing else.