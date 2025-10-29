import logging
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from cassandra.auth import PlainTextAuthProvider
import uuid
from typing import Optional, List

logger = logging.getLogger(__name__)

class SimpleCassandraClient:
    """
    Simple Cassandra client using native Python driver (no cqlsh dependency)
    """
    
    def __init__(self, host: str = "100.71.199.46", port: int = 9042):
        self.host = host
        self.port = port
        self.keyspace = "augustine_psalms"
        self.cluster = None
        self.session = None
        
        logger.info(f"Initializing Cassandra client for {host}:{port}")
        
        try:
            # Connect to Cassandra
            self.cluster = Cluster([host], port=port)
            self.session = self.cluster.connect()
            
            # Setup schema
            self._setup_schema()
            
            logger.info("✅ Cassandra client initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Cassandra: {e}")
            raise
    
    def _setup_schema(self):
        """Create keyspace and tables if they don't exist"""
        logger.info("Setting up Cassandra schema...")
        
        schema_queries = [
            # Keyspace
            f"""
            CREATE KEYSPACE IF NOT EXISTS {self.keyspace} 
            WITH replication = {{
                'class': 'SimpleStrategy', 
                'replication_factor': 1
            }}
            """,
            
            # Psalm verses table
            f"""
            CREATE TABLE IF NOT EXISTS {self.keyspace}.psalm_verses (
                psalm_number int,
                verse_number int,
                latin_text text,
                english_translation text,
                grammatical_notes text,
                PRIMARY KEY (psalm_number, verse_number)
            )
            """,
            
            # Augustine commentaries table  
            f"""
            CREATE TABLE IF NOT EXISTS {self.keyspace}.augustine_commentaries (
                id UUID PRIMARY KEY,
                psalm_number int,
                verse_start int,
                verse_end int,
                work_title text,
                latin_text text,
                english_translation text,
                key_terms set<text>
            )
            """
        ]
        
        for query in schema_queries:
            try:
                self.session.execute(query)
                logger.info("✅ Schema query executed successfully")
            except Exception as e:
                logger.warning(f"Schema setup issue (might already exist): {e}")
        
        # Switch to our keyspace for future queries
        self.session.set_keyspace(self.keyspace)
        logger.info(f"✅ Using keyspace: {self.keyspace}")
    
    def health_check(self) -> str:
        """Check if Cassandra is accessible"""
        try:
            result = self.session.execute("SELECT keyspace_name FROM system_schema.keyspaces")
            keyspaces = [row.keyspace_name for row in result]
            if self.keyspace in keyspaces:
                return f"✅ Connected to Cassandra, keyspace '{self.keyspace}' exists"
            else:
                return f"⚠️ Connected to Cassandra but keyspace '{self.keyspace}' not found"
        except Exception as e:
            return f"❌ Health check failed: {e}"
    
    def insert_psalm_verse(self, psalm_number: int, verse_number: int, 
                          latin_text: str, english_translation: str, 
                          grammatical_notes: str = "") -> bool:
        """Insert a Psalm verse"""
        query = """
            INSERT INTO psalm_verses 
            (psalm_number, verse_number, latin_text, english_translation, grammatical_notes)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            self.session.execute(query, (psalm_number, verse_number, latin_text, 
                                       english_translation, grammatical_notes))
            logger.info(f"✅ Inserted Psalm {psalm_number}:{verse_number}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to insert Psalm {psalm_number}:{verse_number}: {e}")
            return False
    
    def insert_augustine_commentary(self, psalm_number: int, verse_start: int, verse_end: int,
                                   work_title: str, latin_text: str, english_translation: str,
                                   key_terms: set) -> bool:
        """Insert Augustine commentary"""
        query = """
            INSERT INTO augustine_commentaries 
            (id, psalm_number, verse_start, verse_end, work_title, latin_text, english_translation, key_terms)
            VALUES (uuid(), %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            self.session.execute(query, (psalm_number, verse_start, verse_end, work_title, 
                                       latin_text, english_translation, key_terms))
            logger.info(f"✅ Inserted Augustine commentary for Psalm {psalm_number}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to insert Augustine commentary for Psalm {psalm_number}: {e}")
            return False
    
    def get_psalm_verse(self, psalm_number: int, verse_number: int) -> Optional[dict]:
        """Get a Psalm verse as dictionary"""
        query = """
            SELECT * FROM psalm_verses 
            WHERE psalm_number = %s AND verse_number = %s
        """
        try:
            result = self.session.execute(query, (psalm_number, verse_number))
            row = result.one()
            if row:
                return {
                    'psalm_number': row.psalm_number,
                    'verse_number': row.verse_number,
                    'latin_text': row.latin_text,
                    'english_translation': row.english_translation,
                    'grammatical_notes': row.grammatical_notes
                }
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get Psalm verse: {e}")
            return None


    def get_augustine_comments(self, psalm_number: int, verse_number: Optional[int] = None) -> List[dict]:
        """Get Augustine commentaries as list of dictionaries"""
        try:
            if verse_number:
                # For verse-specific queries, we need ALLOW FILTERING or better indexing
                query = """
                    SELECT * FROM augustine_commentaries 
                    WHERE psalm_number = %s 
                    ALLOW FILTERING
                """
                result = self.session.execute(query, (psalm_number,))
            else:
                query = "SELECT * FROM augustine_commentaries WHERE psalm_number = %s"
                result = self.session.execute(query, (psalm_number,))
            
            # Filter results in Python instead of Cassandra for verse-specific queries
            comments = []
            for row in result:
                if verse_number:
                    # Check if the commentary covers this specific verse
                    if row.verse_start <= verse_number <= row.verse_end:
                        comments.append({
                            'id': row.id,
                            'psalm_number': row.psalm_number,
                            'verse_start': row.verse_start,
                            'verse_end': row.verse_end,
                            'work_title': row.work_title,
                            'latin_text': row.latin_text,
                            'english_translation': row.english_translation,
                            'key_terms': row.key_terms
                        })
                else:
                    # Return all commentaries for this psalm
                    comments.append({
                        'id': row.id,
                        'psalm_number': row.psalm_number,
                        'verse_start': row.verse_start,
                        'verse_end': row.verse_end,
                        'work_title': row.work_title,
                        'latin_text': row.latin_text,
                        'english_translation': row.english_translation,
                        'key_terms': row.key_terms
                    })
            return comments
        except Exception as e:
            logger.error(f"❌ Failed to get Augustine comments: {e}")
            return []        
    
    
    
    def close(self):
        """Close the connection"""
        if self.cluster:
            self.cluster.shutdown()
            logger.info("✅ Cassandra connection closed")