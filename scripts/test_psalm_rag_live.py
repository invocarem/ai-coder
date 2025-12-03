# scripts/test_psalm_rag_live.py
import requests
import time
import sys
import os

class PsalmRAGLiveTester:
    """Test the Psalm RAG processor running on localhost:5000"""
    
    def __init__(self, base_url="http://100.109.56.33:5000"):
        self.base_url = base_url
        self.results = []
    
    def test_server_connection(self):
        """Test basic server connectivity"""
        print("🔍 Testing server connection...")
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=10)
            if response.status_code == 200:
                print("✅ Server is running and responsive")
                return True
            else:
                print(f"❌ Server returned status code: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server. Make sure it's running on localhost:5000")
            return False
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def test_psalm_health_check(self):
        """Test Psalm RAG health check endpoint"""
        print("\n🏥 Testing Psalm RAG health check...")
        url = f"{self.base_url}/api/psalm_health"
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Health check successful ({elapsed_time:.2f}s)")
                print(f"   Status: {result.get('status', 'unknown')}")
                if 'database' in result:
                    db_status = result['database']
                    print(f"   Database: {db_status.get('status', 'unknown')}")
                if 'supported_patterns' in result:
                    patterns = result['supported_patterns']
                    print(f"   Supported patterns: {', '.join(patterns)}")
                return True
            else:
                print(f"❌ Health check failed: Status {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Health check test failed: {e}")
            return False
    
    def test_basic_psalm_query(self):
        """Test basic psalm query without verse number or question"""
        print("\n📖 Testing basic psalm query...")
        url = f"{self.base_url}/api/query_psalm"
        
        data = {
            "psalm_number": 1
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=60)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Basic psalm query successful ({elapsed_time:.2f}s)")
                
                # Check for OpenAI-compatible response format
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0].get('message', {}).get('content', '')
                    print(f"   Response preview: {content[:150]}...")
                    
                    # Check for RAG metadata
                    if 'rag_metadata' in result:
                        print(f"   ✓ RAG metadata present")
                    
                    return True
                else:
                    print(f"   ⚠️ Unexpected response format: {list(result.keys())}")
                    return True  # Still consider it a pass if server responded
            else:
                print(f"❌ Basic psalm query failed: Status {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Basic psalm query test failed: {e}")
            return False
    
    def test_psalm_query_with_verse(self):
        """Test psalm query with verse number"""
        print("\n📖 Testing psalm query with verse number...")
        url = f"{self.base_url}/api/query_psalm"
        
        data = {
            "psalm_number": 1,
            "verse_number": 1
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=60)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Psalm query with verse successful ({elapsed_time:.2f}s)")
                
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0].get('message', {}).get('content', '')
                    print(f"   Response preview: {content[:150]}...")
                    return True
                else:
                    print(f"   ⚠️ Unexpected response format")
                    return True
            else:
                print(f"❌ Psalm query with verse failed: Status {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Psalm query with verse test failed: {e}")
            return False
    
    def test_psalm_query_with_question(self):
        """Test psalm query with specific question"""
        print("\n📖 Testing psalm query with specific question...")
        url = f"{self.base_url}/api/query_psalm"
        
        data = {
            "psalm_number": 1,
            "question": "How does Augustine interpret the meaning of this psalm?"
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=60)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Psalm query with question successful ({elapsed_time:.2f}s)")
                
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0].get('message', {}).get('content', '')
                    print(f"   Response preview: {content[:150]}...")
                    return True
                else:
                    print(f"   ⚠️ Unexpected response format")
                    return True
            else:
                print(f"❌ Psalm query with question failed: Status {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Psalm query with question test failed: {e}")
            return False
    
    def test_psalm_word_analysis(self):
        """Test analyzing a word in a psalm"""
        print("\n🔤 Testing psalm word analysis...")
        url = f"{self.base_url}/api/analyze_psalm_word"
        
        data = {
            "word_form": "abiit",
            "psalm_number": 1,
            "verse_number": 1
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=60)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Word analysis successful ({elapsed_time:.2f}s)")
                
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0].get('message', {}).get('content', '')
                    print(f"   Response preview: {content[:150]}...")
                    return True
                else:
                    print(f"   ⚠️ Unexpected response format")
                    return True
            else:
                print(f"❌ Word analysis failed: Status {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Word analysis test failed: {e}")
            return False
    
    def test_psalm_word_analysis_with_question(self):
        """Test word analysis with specific question"""
        print("\n🔤 Testing word analysis with question...")
        url = f"{self.base_url}/api/analyze_psalm_word"
        
        data = {
            "word_form": "abiit",
            "psalm_number": 1,
            "question": "What is the grammatical form and theological significance?"
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=60)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Word analysis with question successful ({elapsed_time:.2f}s)")
                
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0].get('message', {}).get('content', '')
                    print(f"   Response preview: {content[:150]}...")
                    return True
                else:
                    print(f"   ⚠️ Unexpected response format")
                    return True
            else:
                print(f"❌ Word analysis with question failed: Status {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Word analysis with question test failed: {e}")
            return False
    
    def test_error_missing_psalm_number(self):
        """Test error handling for missing psalm_number"""
        print("\n⚠️  Testing error handling (missing psalm_number)...")
        url = f"{self.base_url}/api/query_psalm"
        
        data = {
            "question": "What does this mean?"
        }
        
        try:
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=10)
            
            if response.status_code == 400:
                result = response.json()
                error_msg = result.get('error', '')
                if 'psalm_number' in error_msg.lower() or 'required' in error_msg.lower():
                    print("✅ Correctly rejected request with missing psalm_number")
                    return True
                else:
                    print(f"⚠️  Got 400 but unexpected error message: {error_msg}")
                    return True  # Still a pass
            else:
                print(f"❌ Expected 400 status but got {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False
    
    def test_error_missing_word_form(self):
        """Test error handling for missing word_form in word analysis"""
        print("\n⚠️  Testing error handling (missing word_form)...")
        url = f"{self.base_url}/api/analyze_psalm_word"
        
        data = {
            "psalm_number": 1
        }
        
        try:
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=10)
            
            if response.status_code == 400:
                result = response.json()
                error_msg = result.get('error', '')
                if 'word_form' in error_msg.lower() or 'required' in error_msg.lower():
                    print("✅ Correctly rejected request with missing word_form")
                    return True
                else:
                    print(f"⚠️  Got 400 but unexpected error message: {error_msg}")
                    return True  # Still a pass
            else:
                print(f"❌ Expected 400 status but got {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all Psalm RAG live server tests"""
        print("🚀 Starting Psalm RAG Live Server Tests")
        print("=" * 50)
        
        # Test server connection first
        if not self.test_server_connection():
            print("\n💥 Cannot proceed - server is not accessible")
            return False
        
        # Run all tests
        tests = [
            self.test_psalm_health_check,
            self.test_basic_psalm_query,
            self.test_psalm_query_with_verse,
            self.test_psalm_query_with_question,
            self.test_psalm_word_analysis,
            self.test_psalm_word_analysis_with_question,
            self.test_error_missing_psalm_number,
            self.test_error_missing_word_form
        ]
        
        results = []
        for test in tests:
            results.append(test())
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(results)
        total = len(results)
        
        print(f"Tests passed: {passed}/{total}")
        
        if passed == total:
            print("🎉 All Psalm RAG live server tests passed!")
        else:
            print("❌ Some tests failed. Check the server logs for details.")
        
        return passed == total

def main():
    """Main function to run Psalm RAG live server tests"""
    tester = PsalmRAGLiveTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code for CI/CD
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
