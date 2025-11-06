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
    
    def __init__(self, host: str = "100.109.56.33", port: int = 9042):
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
    
    def drop_all_tables(self):
        """Drop all tables in the keyspace - DANGEROUS! Use with caution"""
        logger.warning("🚨 DROPPING ALL TABLES - THIS WILL DELETE ALL DATA!")
        
        try:
            # Switch to our keyspace
            self.session.set_keyspace(self.keyspace)
            
            # Get all table names in the keyspace
            table_query = """
            SELECT table_name FROM system_schema.tables 
            WHERE keyspace_name = %s
            """
            result = self.session.execute(table_query, (self.keyspace,))
            
            tables = [row.table_name for row in result]
            logger.info(f"📋 Found tables to drop: {tables}")
            
            # Drop each table
            for table in tables:
                drop_query = f"DROP TABLE IF EXISTS {table}"
                self.session.execute(drop_query)
                logger.info(f"🗑️  Dropped table: {table}")
            
            logger.info("✅ All tables dropped successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to drop tables: {e}")
            return False
    
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

            f"""
            CREATE TABLE IF NOT EXISTS {self.keyspace}.psalm_verses (
                psalm_number int,
                section text,  
                verse_number int,
                latin_text text,
                english_translation text,
                grammatical_notes text,
                PRIMARY KEY ((psalm_number, section), verse_number)  
            )
            """,
            
            
            f"""
            CREATE TABLE IF NOT EXISTS {self.keyspace}.augustine_commentaries (
                id UUID PRIMARY KEY,
                psalm_number int,
                verse_start int,
                verse_end int,
                work_title text,
                latin_text text,
                english_translation text,
                key_terms set<text>,
                source_url text,
                scrape_timestamp timestamp
            )
            """
        ]
        
        for query in schema_queries:
            try:
                self.session.execute(query)
                logger.info("✅ Schema query executed successfully")
            except Exception as e:
                logger.warning(f"Schema setup issue (might already exist): {e}")
        
        # Create indexes for better querying
        index_queries = [
            f"CREATE INDEX IF NOT EXISTS ON {self.keyspace}.augustine_commentaries (psalm_number)",
            f"CREATE INDEX IF NOT EXISTS ON {self.keyspace}.augustine_commentaries (work_title)"
        ]
        
        for query in index_queries:
            try:
                self.session.execute(query)
                logger.info("✅ Index created successfully")
            except Exception as e:
                logger.warning(f"Index creation issue: {e}")
        
        # Switch to our keyspace for future queries
        self.session.set_keyspace(self.keyspace)
        logger.info(f"✅ Using keyspace: {self.keyspace}")
    
    def reset_database(self):
        """Completely reset the database by dropping and recreating all tables"""
        logger.warning("🔄 RESETTING DATABASE - ALL DATA WILL BE LOST!")
        
        try:
            # Drop all tables
            self.drop_all_tables()
            
            # Wait a moment for drops to complete
            import time
            time.sleep(2)
            
            # Recreate schema
            self._setup_schema()
            
            logger.info("✅ Database reset completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to reset database: {e}")
            return False
    
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


    def insert_psalm_verse(self, psalm_number: int, section: str, verse_number: int, 
                        latin_text: str, english_translation: str, 
                        grammatical_notes: str = "") -> bool:
        """Insert a Psalm verse with section support"""
        query = """
            INSERT INTO psalm_verses 
            (psalm_number, section, verse_number, latin_text, english_translation, grammatical_notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        try:
            self.session.execute(query, (psalm_number, section, verse_number, latin_text, 
                                    english_translation, grammatical_notes))
            logger.info(f"✅ Inserted Psalm {psalm_number}{f' ({section})' if section else ''}:{verse_number}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to insert Psalm {psalm_number}{f' ({section})' if section else ''}:{verse_number}: {e}")
            return False

    def get_psalm_verse(self, psalm_number: int, section: str, verse_number: int) -> Optional[dict]:
        """Get a Psalm verse with section support"""
        query = """
            SELECT * FROM psalm_verses 
            WHERE psalm_number = %s AND section = %s AND verse_number = %s
        """
        try:
            result = self.session.execute(query, (psalm_number, section, verse_number))
            row = result.one()
            if row:
                return {
                    'psalm_number': row.psalm_number,
                    'section': row.section,
                    'verse_number': row.verse_number,
                    'latin_text': row.latin_text,
                    'english_translation': row.english_translation,
                    'grammatical_notes': row.grammatical_notes
                }
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get Psalm verse: {e}")
            return None

    def get_psalm_section(self, psalm_number: int, section: str) -> List[dict]:
        """Get all verses from a specific Psalm section"""
        query = """
            SELECT * FROM psalm_verses 
            WHERE psalm_number = %s AND section = %s
        """
        try:
            result = self.session.execute(query, (psalm_number, section))
            verses = []
            for row in result:
                verses.append({
                    'psalm_number': row.psalm_number,
                    'section': row.section,
                    'verse_number': row.verse_number,
                    'latin_text': row.latin_text,
                    'english_translation': row.english_translation,
                    'grammatical_notes': row.grammatical_notes
                })
            return sorted(verses, key=lambda x: x['verse_number'])
        except Exception as e:
            logger.error(f"❌ Failed to get Psalm section: {e}")
            return []            
    
    
    def insert_augustine_commentary(self, psalm_number: int, verse_start: int, verse_end: int,
                                   work_title: str, latin_text: str, english_translation: str,
                                   key_terms: set, source_url: str = None) -> bool:
        """Insert Augustine commentary with enhanced fields"""
        query = """
            INSERT INTO augustine_commentaries 
            (id, psalm_number, verse_start, verse_end, work_title, latin_text, 
             english_translation, key_terms, source_url, scrape_timestamp)
            VALUES (uuid(), %s, %s, %s, %s, %s, %s, %s, %s, toTimestamp(now()))
        """
        try:
            self.session.execute(query, (psalm_number, verse_start, verse_end, work_title, 
                                       latin_text, english_translation, key_terms, source_url))
            logger.info(f"✅ Inserted Augustine commentary for Psalm {psalm_number}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to insert Augustine commentary for Psalm {psalm_number}: {e}")
            return False
    

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
                            'key_terms': row.key_terms,
                            'source_url': getattr(row, 'source_url', None),
                            'scrape_timestamp': getattr(row, 'scrape_timestamp', None)
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
                        'key_terms': row.key_terms,
                        'source_url': getattr(row, 'source_url', None),
                        'scrape_timestamp': getattr(row, 'scrape_timestamp', None)
                    })
            return comments
        except Exception as e:
            logger.error(f"❌ Failed to get Augustine comments: {e}")
            return []        

    def insert_psalm_exposition(self, psalm_number, verse_start, verse_end, work_title, 
                            latin_text, english_translation, key_terms, source_url=None):
        """Insert full psalm exposition with source URL"""
        try:
            query = """
            INSERT INTO augustine_commentaries 
            (id, psalm_number, verse_start, verse_end, work_title, latin_text, 
            english_translation, key_terms, source_url, scrape_timestamp)
            VALUES (uuid(), %s, %s, %s, %s, %s, %s, %s, %s, toTimestamp(now()))
            """
            
            self.session.execute(query, (
                psalm_number, verse_start, verse_end, work_title, latin_text,
                english_translation, key_terms, source_url
            ))
            return True
            
        except Exception as e:
            print(f"Error inserting psalm exposition: {e}")
            return False

    def get_psalm_exposition(self, psalm_number):
        """Retrieve exposition for a specific psalm"""
        try:
            query = """
            SELECT * FROM augustine_commentaries 
            WHERE psalm_number = %s 
            AND work_title = 'Enarrationes in Psalmos'
            ALLOW FILTERING
            """
            
            result = self.session.execute(query, (psalm_number,))
            return list(result)
            
        except Exception as e:
            print(f"Error retrieving psalm exposition: {e}")
            return []
    
    def close(self):
        """Close the connection"""
        if self.cluster:
            self.cluster.shutdown()
            logger.info("✅ Cassandra connection closed")