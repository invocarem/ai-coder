# scripts/test_live_server.py
import requests
import time
import sys
import os

class LiveServerTester:
    """Test the live server running on localhost:5000"""
    
    def __init__(self, base_url="http://127.0.0.1:5000"):
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
    
    def test_generate_function(self):
        """Test generating a function"""
        print("\n🧪 Testing function generation...")
        url = f"{self.base_url}/api/generate_code"
        
        data = {
            "pattern": "generate_function",
            "language": "Python",
            "task": "write a function to calculate the sum of a list"
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=30)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Function generation successful ({elapsed_time:.2f}s)")
                print(f"   Response preview: {result.get('text', '')[:100]}...")
                return True
            else:
                print(f"❌ Function generation failed: Status {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Function generation test failed: {e}")
            return False
    
    def test_refactor_code(self):
        """Test refactoring code"""
        print("\n🔧 Testing code refactoring...")
        url = f"{self.base_url}/api/generate_code"
        
        data = {
            "pattern": "refactor_code",
            "language": "Python",
            "code": "def sum_list(lst):\n    total = 0\n    for i in range(len(lst)):\n        total += lst[i]\n    return total"
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=30)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Code refactoring successful ({elapsed_time:.2f}s)")
                print(f"   Response preview: {result.get('text', '')[:100]}...")
                return True
            else:
                print(f"❌ Code refactoring failed: Status {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Code refactoring test failed: {e}")
            return False
    
    def test_openai_chat_endpoint(self):
        """Test OpenAI-compatible chat endpoint"""
        print("\n🤖 Testing OpenAI-compatible endpoint...")
        url = f"{self.base_url}/v1/chat/completions"
        
        data = {
            "model": "deepseek-coder:6.7b",
            "messages": [
                {"role": "user", "content": "Write a Python function to calculate fibonacci sequence"}
            ],
            "temperature": 0.1
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=data, timeout=30)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ OpenAI endpoint successful ({elapsed_time:.2f}s)")
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0].get('message', {}).get('content', '')
                    print(f"   Response preview: {content[:100]}...")
                return True
            else:
                print(f"❌ OpenAI endpoint failed: Status {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ OpenAI endpoint test failed: {e}")
            return False
    
    def test_fix_bug_pattern(self):
        """Test bug fixing pattern"""
        print("\n🐛 Testing bug fixing...")
        url = f"{self.base_url}/api/generate_code"
        
        data = {
            "pattern": "fix_bug",
            "language": "Python",
            "code": "def divide_numbers(a, b):\n    return a / b\n\nresult = divide_numbers(10, 0)",
            "issue": "division by zero error"
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=30)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Bug fixing successful ({elapsed_time:.2f}s)")
                print(f"   Response preview: {result.get('text', '')[:100]}...")
                return True
            else:
                print(f"❌ Bug fixing failed: Status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Bug fixing test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all live server tests"""
        print("🚀 Starting Live Server Tests")
        print("=" * 50)
        
        # Test server connection first
        if not self.test_server_connection():
            print("\n💥 Cannot proceed - server is not accessible")
            return False
        
        # Run all tests
        tests = [
            self.test_generate_function,
            self.test_refactor_code, 
            self.test_fix_bug_pattern,
            self.test_openai_chat_endpoint
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
            print("🎉 All live server tests passed!")
        else:
            print("❌ Some tests failed. Check the server logs for details.")
        
        return passed == total

def main():
    """Main function to run live server tests"""
    tester = LiveServerTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code for CI/CD
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()