# app/rag/cassandra_client.py
import logging
import os
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

logger = logging.getLogger(__name__)

class CassandraClient:
    def __init__(self):
        self.cluster = None
        self.session = None
        self.connect()
        self.initialize_schema()
    
    def connect(self):
        try:
            if os.getenv('CASSANDRA_CLOUD', False):
                # Astra DB
                cloud_config = {'secure_connect_bundle': os.getenv('ASTRA_SECURE_BUNDLE_PATH')}
                auth_provider = PlainTextAuthProvider(
                    os.getenv('ASTRA_CLIENT_ID'), os.getenv('ASTRA_CLIENT_SECRET')
                )
                self.cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
            else:
                # Local Cassandra
                contact_points = os.getenv('CASSANDRA_HOSTS', 'localhost').split(',')
                self.cluster = Cluster(contact_points)
            
            self.session = self.cluster.connect()
            logger.info("Connected to Cassandra successfully")
            
        except Exception as e:
            logger.error(f"Cassandra connection failed: {e}")
            raise
    
    def initialize_schema(self):
        """Create keyspace and tables"""
        from app.rag.schema import CASSANDRA_SCHEMA
        
        try:
            # Create keyspace
            self.session.execute(CASSANDRA_SCHEMA['keyspace'])
            self.session.set_keyspace('augustine_psalms')
            
            # Create tables
            for table_name, create_stmt in CASSANDRA_SCHEMA.items():
                if table_name != 'keyspace':
                    self.session.execute(create_stmt)
            
            logger.info("Cassandra schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            raise
    
    def semantic_search(self, query_embedding, limit=5, filters=None):
        """Perform vector similarity search"""
        try:
            # This requires Cassandra with vector support (Stargate or Astra DB)
            search_query = """
                SELECT chunk_id, content_text, metadata, 
                       similarity_cosine(embedding, %s) as similarity
                FROM text_embeddings
            """
            
            params = [query_embedding]
            
            if filters:
                where_clauses = []
                for key, value in filters.items():
                    where_clauses.append(f"metadata['{key}'] = %s")
                    params.append(str(value))
                
                if where_clauses:
                    search_query += " WHERE " + " AND ".join(where_clauses)
            
            search_query += " ORDER BY similarity DESC LIMIT %s"
            params.append(limit)
            
            results = self.session.execute(search_query, params)
            return list(results)
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            # Fallback to metadata search
            return self.metadata_search(filters, limit)
    
    def metadata_search(self, filters, limit=5):
        """Fallback search using metadata filtering"""
        query = "SELECT * FROM text_embeddings WHERE "
        where_clauses = []
        params = []
        
        for key, value in filters.items():
            where_clauses.append(f"metadata['{key}'] = %s")
            params.append(str(value))
        
        query += " AND ".join(where_clauses) + " LIMIT %s"
        params.append(limit)
        
        return list(self.session.execute(query, params))
    
    def execute_query(self, query, parameters=None):
        try:
            return self.session.execute(query, parameters)
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
    def health_check(self):
        try:
            self.session.execute("SELECT now() FROM system.local")
            return "connected"
        except Exception as e:
            return f"disconnected: {e}"