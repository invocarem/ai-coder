#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.simple_cassandra_client import SimpleCassandraClient

def test_connection():
    print("Testing REMOTE Cassandra connection via Tailscale...")
    print("Target: 100.71.199.46:9042")
    
    try:
        client = SimpleCassandraClient()
        health = client.health_check()
        print(f"✅ Connection status: {health}")
        
        # Test basic query
        result = client.get_psalm_verse(1, 1)
        if result:
            print("✅ Can query data")
        else:
            print("ℹ️  No data yet - run setup script")
            
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        print("\n💡 Make sure:")
        print("1. Cassandra is running on iMac (100.71.199.46:9042)")
        print("2. Tailscale is connected")
        print("3. cqlsh is available on your laptop")

if __name__ == "__main__":
    test_connection()
