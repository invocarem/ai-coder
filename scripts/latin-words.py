# scripts/latin-words.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.simple_whitaker_client import SimpleWhitakerClient

client = SimpleWhitakerClient(port=9090)

# Health check
print(client.health_check())

# Analyze Latin words
result = client.analyze_word("dominus")
result = client.analyze_text("In principio erat Verbum")

# Batch process
words = ["amor", "deus", "homo", "verbum"]
batch_result = client.batch_analyze(words)