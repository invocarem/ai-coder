# check_data.py
#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.simple_cassandra_client import SimpleCassandraClient

def check_actual_data():
    print("🔍 Checking actual data in Cassandra...")
    
    client = SimpleCassandraClient(host=os.getenv("CASSANDRA_HOSTS", "127.0.0.1"))
    
    # Check Psalm 1:1 (with empty section)
    verse = client.get_psalm_verse(1, "", 1)  # Added section parameter
    print(f"\n📖 PSALM 1:1:")
    if verse:
        print(f"Section: '{verse['section']}'")
        print(f"Latin: {verse['latin_text']}")
        print(f"English: {verse['english_translation']}")
        print(f"Grammar: {verse.get('grammatical_notes', 'None')}")
    else:
        print("❌ No Psalm 1:1 found")
    
    # Check Augustine comments
    comments = client.get_augustine_comments(1, 1)
    print(f"\n📚 AUGUSTINE COMMENTARY (found {len(comments)}):")
    for i, comment in enumerate(comments):
        print(f"\n--- Comment {i+1} ---")
        print(f"Work: {comment['work_title']}")
        print(f"Verses: {comment['verse_start']}-{comment['verse_end']}")
        print(f"Latin: {comment['latin_text'][:100]}..." if comment['latin_text'] else "No Latin text")
        print(f"English: {comment['english_translation'][:100]}..." if comment['english_translation'] else "No English text")
        print(f"Key Terms: {comment.get('key_terms', [])}")
        if comment.get('source_url'):
            print(f"Source: {comment['source_url']}")
    
    # Check what Psalms we have in the database
    print(f"\n📊 DATABASE OVERVIEW:")
    
    # Count Psalm verses
    try:
        result = client.session.execute("SELECT COUNT(*) FROM psalm_verses")
        print(f"Total Psalm verses: {result.one()[0]}")
    except Exception as e:
        print(f"Error counting Psalm verses: {e}")
    
    # Count Augustine commentaries
    try:
        result = client.session.execute("SELECT COUNT(*) FROM augustine_commentaries")
        print(f"Total Augustine commentaries: {result.one()[0]}")
    except Exception as e:
        print(f"Error counting Augustine commentaries: {e}")
    
    # List unique Psalms
    try:
        result = client.session.execute("SELECT DISTINCT psalm_number, section FROM psalm_verses LIMIT 10")
        psalms = list(result)
        print(f"\nSample Psalms in database (first 10):")
        for psalm in psalms:
            print(f"  Psalm {psalm.psalm_number}{f' ({psalm.section})' if psalm.section else ''}")
    except Exception as e:
        print(f"Error listing Psalms: {e}")
    
    client.close()

def check_psalm_with_section(psalm_number, section, verse_number):
    """Check a specific Psalm with section"""
    print(f"\n🔍 Checking Psalm {psalm_number}{f' ({section})' if section else ''}:{verse_number}")
    
    client = SimpleCassandraClient()
    
    verse = client.get_psalm_verse(psalm_number, section, verse_number)
    if verse:
        print(f"✅ Found:")
        print(f"   Section: '{verse['section']}'")
        print(f"   Latin: {verse['latin_text'][:80]}...")
        print(f"   English: {verse['english_translation'][:80]}...")
    else:
        print(f"❌ Not found")
    
    client.close()

if __name__ == "__main__":
    check_actual_data()
    
    # You can also check specific Psalms with sections
    # Uncomment these if you have Psalms with sections like 9-A, 118-aleph, etc.
    # print("\n" + "="*50)
    # check_psalm_with_section(9, "A", 1)
    # check_psalm_with_section(9, "B", 1) 
    # check_psalm_with_section(118, "aleph", 1)
