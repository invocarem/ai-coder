# reset_database.py
#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.simple_cassandra_client import SimpleCassandraClient

def main():
    print("🔄 Database Reset Tool")
    print("⚠️  WARNING: This will delete ALL data in the database!")
    
    confirmation = input("Type 'RESET' to confirm: ")
    if confirmation != "RESET":
        print("❌ Reset cancelled")
        return
    
    client = SimpleCassandraClient()
    
    try:
        success = client.reset_database()
        if success:
            print("✅ Database reset completed successfully!")
            print("📊 You can now run your setup scripts to create fresh tables")
        else:
            print("❌ Database reset failed")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()