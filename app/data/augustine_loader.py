# app/data/augustine_loader.py
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class AugustineLoader:
    def __init__(self, cassandra_client):
        self.cassandra_client = cassandra_client
    
    def load_augustine_commentaries(self):
        """Load Augustine's Psalm commentaries"""
        commentaries = [
            {
                'psalm_number': 1,
                'verse_start': 1,
                'verse_end': 1,
                'work_title': 'Enarrationes in Psalmos',
                'book_reference': 'Enarratio in Psalmum 1',
                'latin_commentary': '''In his verbis tria sunt: "abiit", "stetit", "sedit". 
                Primo consentit consilio impiorum, secudo perseveravit in via peccatorum, 
                tertio confirmatus est in cathedra pestilentiae.''',
                'english_translation': '''In these words there are three things: "he walked", 
                "he stood", "he sat". First he consented to the counsel of the wicked, 
                second he persevered in the way of sinners, third he was confirmed in the seat of pestilence.''',
                'key_phrases': {'abiit', 'stetit', 'sedit', 'threefold progression', 'sin'},
                'theological_themes': {'sin progression', 'free will', 'spiritual descent'},
                'language': 'latin',
                'source_edition': 'Patrologia Latina 36'
            },
            {
                'psalm_number': 1,
                'verse_start': 2,
                'verse_end': 2,
                'work_title': 'Enarrationes in Psalmos',
                'book_reference': 'Enarratio in Psalmum 1',
                'latin_commentary': '''"In lege Domini voluntas eius": hic iam non timor, sed amor. 
                Timor enim cogit, amor delectat.''',
                'english_translation': '''"His will is in the law of the Lord": here now is not fear, but love. 
                For fear compels, love delights.''',
                'key_phrases': {'lege Domini', 'voluntas', 'amor', 'timor'},
                'theological_themes': {'love of God', 'law', 'delight'},
                'language': 'latin', 
                'source_edition': 'Patrologia Latina 36'
            }
            # Add more commentaries...
        ]
        
        insert_commentary = self.cassandra_client.session.prepare("""
            INSERT INTO augustine_expositions 
            (id, psalm_number, verse_start, verse_end, work_title, book_reference,
             latin_commentary, english_translation, key_phrases, theological_themes,
             language, source_edition, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        
        for commentary in commentaries:
            self.cassandra_client.session.execute(insert_commentary, (
                uuid.uuid4(),
                commentary['psalm_number'],
                commentary['verse_start'],
                commentary['verse_end'],
                commentary['work_title'],
                commentary['book_reference'],
                commentary['latin_commentary'],
                commentary['english_translation'],
                commentary['key_phrases'],
                commentary['theological_themes'],
                commentary['language'],
                commentary['source_edition'],
                datetime.now()
            ))
        
        logger.info(f"Loaded {len(commentaries)} Augustine commentaries")
    
    def load_word_studies(self):
        """Load word study data"""
        word_studies = [
            ('abiit', 'latin', 1, 1, 'perfect indicative active, 3rd singular',
             'Augustine sees "abiit" as voluntary departure from God''s way, representing initial consent to evil counsel',
             'Represents the first stage of sin: initial association and consent',
             {'abeo', 'departure', 'walking'},
             {'Psalm 1:1', 'Proverbs 1:10'}
            ),
            ('stetit', 'latin', 1, 1, 'perfect indicative active, 3rd singular',
             'Interpreted by Augustine as persistence and habituation in sinful ways',
             'Second stage: establishment and persistence in sinful lifestyle', 
             {'sto', 'stand', 'persist'},
             {'Psalm 1:1', 'Psalm 36:12'}
            ),
            ('sedit', 'latin', 1, 1, 'perfect indicative active, 3rd singular',
             'Augustine explains this as full identification with scornful attitudes',
             'Third stage: complete adoption of scornful mindset and identity',
             {'sedeo', 'sit', 'dwell'},
             {'Psalm 1:1', 'Psalm 107:10'}
            )
        ]
        
        insert_study = self.cassandra_client.session.prepare("""
            INSERT INTO word_studies 
            (word, language, psalm_number, verse_number, grammatical_form,
             augustine_interpretation, theological_significance, related_terms, cross_references)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        
        for study in word_studies:
            self.cassandra_client.session.execute(insert_study, study)
        
        logger.info(f"Loaded {len(word_studies)} word studies")
