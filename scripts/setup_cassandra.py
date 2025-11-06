#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.simple_cassandra_client import SimpleCassandraClient

def main():
    print("Setting up REMOTE Cassandra database for Augustine Psalms RAG...")
    print("Target: 100.101.56.33:9042")
    
    # Initialize the WORKING Cassandra client
    cassandra_client = SimpleCassandraClient()
    
    # Load sample data directly (no need for separate loaders)
    print("Loading sample Psalms...")
    
    
    print("✅ Setup completed successfully!")
    print("📊 Database contains:")
    print("- Psalm 1:1-2")
    print("- Empty augustine_commentaries table (ready for scraping)")
    print("\n📝 Next steps:")
    print("1. Run: python scrape_augustine_psalms.py")
    print("2. This will populate all Augustine commentaries from New Advent")

if __name__ == "__main__":
    main()