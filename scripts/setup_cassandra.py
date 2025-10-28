#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.simple_cassandra_client import SimpleCassandraClient

def main():
    print("Setting up REMOTE Cassandra database for Augustine Psalms RAG...")
    print("Target: 100.71.199.46:9042")
    
    # Initialize the WORKING Cassandra client
    cassandra_client = SimpleCassandraClient()
    
    # Load sample data directly (no need for separate loaders)
    print("Loading sample Psalms...")
    
    # Psalm 1:1
    cassandra_client.insert_psalm_verse(
        psalm_number=1,
        verse_number=1,
        latin_text="Beatus vir qui non abiit in consilio impiorum, et in via peccatorum non stetit, et in cathedra pestilentiae non sedit;",
        english_translation="Blessed is the man who walks not in the counsel of the wicked, nor stands in the way of sinners, nor sits in the seat of scoffers;",
        grammatical_notes="Verbs: abiit, stetit, sedit (all perfect tense)"
    )
    
    # Psalm 1:2
    cassandra_client.insert_psalm_verse(
        psalm_number=1,
        verse_number=2,
        latin_text="sed in lege Domini voluntas eius, et in lege eius meditabitur die ac nocte.",
        english_translation="but his delight is in the law of the Lord, and on his law he meditates day and night.",
        grammatical_notes="Verb: meditabitur (future tense)"
    )
    
    # Augustine commentary
    cassandra_client.insert_augustine_commentary(
        psalm_number=1,
        verse_start=1,
        verse_end=1,
        work_title="Enarrationes in Psalmos",
        latin_text="In his verbis tria sunt: abiit, stetit, sedit. Primo consentit consilio impiorum, secundo perseveravit in via peccatorum, tertio confirmatus est in cathedra pestilentiae.",
        english_translation="In these words there are three things: he walked, he stood, he sat. First he consented to the counsel of the wicked, second he persevered in the way of sinners, third he was confirmed in the seat of pestilence.",
        key_terms={"abiit", "stetit", "sedit", "threefold", "progression"}
    )
    
    print("✅ Setup completed successfully!")
    print("📊 Database contains:")
    print("- Psalm 1:1-2")
    print("- Augustine commentary on Psalm 1:1")

if __name__ == "__main__":
    main()