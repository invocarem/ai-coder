# enhanced_sample_data.py
#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.simple_cassandra_client import SimpleCassandraClient

def load_enhanced_data():
    print("📚 Loading enhanced Augustine commentary data...")
    
    client = SimpleCassandraClient()
    
    # Clear existing data first (optional)
    # client.session.execute("TRUNCATE augustine_commentaries")
    
    # Enhanced Augustine commentary focusing on "abiit"
    enhanced_comments = [
        {
            'psalm_number': 1,
            'verse_start': 1,
            'verse_end': 1,
            'work_title': "Enarrationes in Psalmos",
            'latin_text': "In his verbis tria sunt: abiit, stetit, sedit. Primo consentit consilio impiorum, secundo perseveravit in via peccatorum, tertio confirmatus est in cathedra pestilentiae. Abiit enim significat motum cordis ad malum.",
            'english_translation': "In these words there are three things: he walked, he stood, he sat. First he consented to the counsel of the wicked, second he persevered in the way of sinners, third he was confirmed in the seat of pestilence. For 'abiit' signifies the movement of the heart toward evil.",
            'key_terms': {"abiit", "stetit", "sedit", "threefold progression", "heart movement", "consent"}
        },
        {
            'psalm_number': 1,
            'verse_start': 1,
            'verse_end': 1,
            'work_title': "Sermones de Psalmis",
            'latin_text': "Abiit non pedibus corporis, sed affectu cordis. Qui enim consentit impiis, abiit a Domino, etsi corpore non recessit.",
            'english_translation': "He walked not with the feet of the body, but with the affection of the heart. For whoever consents to the wicked, has walked away from the Lord, even if he has not departed in body.",
            'key_terms': {"abiit", "heart affection", "consent", "spiritual departure"}
        },
        {
            'psalm_number': 1,
            'verse_start': 1,
            'verse_end': 2,
            'work_title': "De Civitate Dei",
            'latin_text': "Verbum 'abiit' hic non localem motum designat, sed moralem declinationem. Beatus vir est qui a tali abitione se custodit.",
            'english_translation': "The word 'abiit' here designates not a local motion, but a moral declination. Blessed is the man who guards himself from such walking away.",
            'key_terms': {"abiit", "moral declination", "spiritual motion", "blessed man"}
        }
    ]
    
    for comment in enhanced_comments:
        success = client.insert_augustine_commentary(
            psalm_number=comment['psalm_number'],
            verse_start=comment['verse_start'],
            verse_end=comment['verse_end'],
            work_title=comment['work_title'],
            latin_text=comment['latin_text'],
            english_translation=comment['english_translation'],
            key_terms=comment['key_terms']
        )
        if success:
            print(f"✅ Added: {comment['work_title']}")
        else:
            print(f"❌ Failed: {comment['work_title']}")
    
    print("\n🎉 Enhanced data loaded! Now test your query again.")
    client.close()

if __name__ == "__main__":
    load_enhanced_data()