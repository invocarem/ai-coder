#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.simple_cassandra_client import SimpleCassandraClient
import uuid

def load_sample_data():
    print("Loading sample data to remote Cassandra...")
    
    client = SimpleCassandraClient(host=os.getenv("CASSANDRA_HOSTS", "127.0.0.1"))
    
    # Sample Psalm data
    psalm_data = [
        (1, 1, 
         "Beatus vir qui non abiit in consilio impiorum, et in via peccatorum non stetit, et in cathedra pestilentiae non sedit;",
         "Blessed is the man who walks not in the counsel of the wicked, nor stands in the way of sinners, nor sits in the seat of scoffers;",
         "Verbs: abiit, stetit, sedit (all perfect tense)"),
        
        (1, 2,
         "sed in lege Domini voluntas eius, et in lege eius meditabitur die ac nocte.",
         "but his delight is in the law of the Lord, and on his law he meditates day and night.",
         "Verb: meditabitur (future tense)")
    ]
    
    for psalm in psalm_data:
        client.insert_psalm_verse(*psalm)
    
    # Sample Augustine commentary
    augustine_data = [
        (1, 1, 1, "Enarrationes in Psalmos",
         "In his verbis tria sunt: abiit, stetit, sedit. Primo consentit consilio impiorum, secundo perseveravit in via peccatorum, tertio confirmatus est in cathedra pestilentiae.",
         "In these words there are three things: he walked, he stood, he sat. First he consented to the counsel of the wicked, second he persevered in the way of sinners, third he was confirmed in the seat of pestilence.",
         {"abiit", "stetit", "sedit", "threefold", "progression"})
    ]
    
    for data in augustine_data:
        client.insert_augustine_commentary(*data)
    
    print("✅ Sample data loaded to remote Cassandra!")
    print("📍 Location: Tailscale IP 100.71.199.46")
    
    # Verify the data was inserted
    print("\n📖 Verifying inserted data:")
    
    # Check Psalm verses
    verse_1 = client.get_psalm_verse(1, 1)
    if verse_1:
        print(f"✅ Psalm 1:1 - {verse_1['latin_text'][:50]}...")
    else:
        print("❌ Psalm 1:1 not found")
    
    verse_2 = client.get_psalm_verse(1, 2)
    if verse_2:
        print(f"✅ Psalm 1:2 - {verse_2['latin_text'][:50]}...")
    else:
        print("❌ Psalm 1:2 not found")
    
    # Check Augustine commentary
    comments = client.get_augustine_comments(1, 1)
    if comments:
        print(f"✅ Augustine commentary found - {comments[0]['work_title']}")
        print(f"   Latin: {comments[0]['latin_text'][:60]}...")
    else:
        print("❌ Augustine commentary not found")
    
    client.close()

if __name__ == "__main__":
    load_sample_data()
