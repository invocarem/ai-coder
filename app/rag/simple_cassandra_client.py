import logging
import subprocess
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

class SimpleCassandraClient:
    """
    Simple Cassandra client that works with remote Docker setup
    Uses subprocess to run commands on the local machine
    """
    
    def __init__(self, host: str = "100.71.199.46", port: int = 9042):
        self.host = host
        self.port = port
        self.keyspace = "augustine_psalms"
        
        logger.info(f"Initializing Cassandra client for {host}:{port}")
        
        # Setup schema
        self._setup_schema()
    
    def _run_remote_cql(self, query: str) -> bool:
        """
        Run CQL query on remote Cassandra using cqlsh
        Returns True if successful, False otherwise
        """
        try:
            # Use cqlsh to connect to remote host
            cmd = f'cqlsh {self.host} {self.port} -e "{query}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return True
            else:
                logger.warning(f"Query may have failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Query timed out")
            return False
        except Exception as e:
            logger.error(f"Query failed: {e}")
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
            success = self._run_remote_cql(query)
            if success:
                logger.info("Schema created successfully")
            else:
                logger.warning("Schema setup had issues - tables might already exist")
    
    def insert_psalm_verse(self, psalm_number: int, verse_number: int, 
                          latin_text: str, english_translation: str, 
                          grammatical_notes: str = ""):
        """Insert a Psalm verse"""
        query = f"""
            INSERT INTO {self.keyspace}.psalm_verses 
            (psalm_number, verse_number, latin_text, english_translation, grammatical_notes)
            VALUES ({psalm_number}, {verse_number}, '{latin_text}', '{english_translation}', '{grammatical_notes}')
        """
        
        success = self._run_remote_cql(query)
        if success:
            logger.info(f"Inserted Psalm {psalm_number}:{verse_number}")
        else:
            logger.error(f"Failed to insert Psalm {psalm_number}:{verse_number}")
    
    def insert_augustine_commentary(self, psalm_number: int, verse_start: int, verse_end: int,
                                   work_title: str, latin_text: str, english_translation: str,
                                   key_terms: set):
        """Insert Augustine commentary"""
        # Convert set to CQL format
        key_terms_str = "{" + ", ".join([f"'{term}'" for term in key_terms]) + "}"
        
        query = f"""
            INSERT INTO {self.keyspace}.augustine_commentaries 
            (id, psalm_number, verse_start, verse_end, work_title, latin_text, english_translation, key_terms)
            VALUES (uuid(), {psalm_number}, {verse_start}, {verse_end}, '{work_title}', '{latin_text}', '{english_translation}', {key_terms_str})
        """
        
        success = self._run_remote_cql(query)
        if success:
            logger.info(f"Inserted Augustine commentary for Psalm {psalm_number}")
        else:
            logger.error(f"Failed to insert Augustine commentary for Psalm {psalm_number}")
    
    def health_check(self):
        """Check if Cassandra is accessible"""
        try:
            # Simple test query
            cmd = f'cqlsh {self.host} {self.port} -e "DESCRIBE KEYSPACES"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return "connected"
            else:
                return f"cqlsh error: {result.stderr[:100]}"
                
        except subprocess.TimeoutExpired:
            return "timeout - Cassandra not responding"
        except Exception as e:
            return f"connection failed: {e}"
    
    def get_psalm_verse(self, psalm_number: int, verse_number: int) -> Optional[str]:
        """Get a Psalm verse (simple string representation)"""
        query = f"SELECT * FROM {self.keyspace}.psalm_verses WHERE psalm_number = {psalm_number} AND verse_number = {verse_number}"
        
        cmd = f'cqlsh {self.host} {self.port} -e "{query}"'
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout
            return None
        except Exception as e:
            logger.error(f"Failed to get Psalm verse: {e}")
            return None
    
    def get_augustine_comments(self, psalm_number: int, verse_number: Optional[int] = None) -> Optional[str]:
        """Get Augustine commentaries (simple string representation)"""
        if verse_number:
            query = f"SELECT * FROM {self.keyspace}.augustine_commentaries WHERE psalm_number = {psalm_number} AND verse_start <= {verse_number} AND verse_end >= {verse_number}"
        else:
            query = f"SELECT * FROM {self.keyspace}.augustine_commentaries WHERE psalm_number = {psalm_number}"
        
        cmd = f'cqlsh {self.host} {self.port} -e "{query}"'
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout
            return None
        except Exception as e:
            logger.error(f"Failed to get Augustine comments: {e}")
            return None