import logging
import requests
import json
from typing import Optional, Dict, List, Any
import time

logger = logging.getLogger(__name__)

class SimpleWhitakerClient:
    """
    Simple Whitaker client for interacting with the Whitaker service
    """
    
    def __init__(self, host: str = "localhost", port: int = 9090, base_url: str = None):
        self.host = host
        self.port = port
        self.base_url = base_url or f"http://{host}:{port}"
        
        logger.info(f"Initializing Whitaker client for {self.base_url}")
        
        # Test connection on init
        try:
            health = self.health_check()
            logger.info(f"✅ Whitaker client initialized successfully: {health}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Whitaker service: {e}")
            raise
    
    def health_check(self) -> str:
        """Check if Whitaker service is accessible"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                return f"✅ Whitaker service is healthy: {response.text}"
            else:
                return f"⚠️ Whitaker service responded with status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return "❌ Cannot connect to Whitaker service - is it running?"
        except Exception as e:
            return f"❌ Health check failed: {e}"
    
    def analyze_word(self, word: str, language: str = "la") -> Optional[Dict[str, Any]]:
        """
        Analyze a single word using Whitaker
        """
        endpoint = f"{self.base_url}/analyze"
        
        try:
            response = requests.post(
                endpoint,
                json={"word": word, "language": language},
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Analyzed word: {word}")
                return response.json()
            else:
                logger.error(f"❌ Whitaker analysis failed for '{word}': {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to analyze word '{word}': {e}")
            return None
    
    def analyze_text(self, text: str, language: str = "la") -> Optional[Dict[str, Any]]:
        """
        Analyze a full text passage using Whitaker
        """
        endpoint = f"{self.base_url}/analyze/text"
        
        try:
            response = requests.post(
                endpoint,
                json={"text": text, "language": language},
                timeout=60
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Analyzed text (length: {len(text)} chars)")
                return response.json()
            else:
                logger.error(f"❌ Whitaker text analysis failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to analyze text: {e}")
            return None
    
    def get_dictionary_entry(self, word: str) -> Optional[Dict[str, Any]]:
        """
        Get dictionary entry for a word
        """
        endpoint = f"{self.base_url}/dictionary/{word}"
        
        try:
            response = requests.get(endpoint, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"✅ Retrieved dictionary entry for: {word}")
                return response.json()
            else:
                logger.error(f"❌ Dictionary lookup failed for '{word}': {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get dictionary entry for '{word}': {e}")
            return None
    
    def batch_analyze(self, words: List[str], language: str = "la") -> Optional[Dict[str, Any]]:
        """
        Analyze multiple words in batch
        """
        endpoint = f"{self.base_url}/analyze/batch"
        
        try:
            response = requests.post(
                endpoint,
                json={"words": words, "language": language},
                timeout=60
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Batch analyzed {len(words)} words")
                return response.json()
            else:
                logger.error(f"❌ Batch analysis failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to batch analyze words: {e}")
            return None
    
    def get_service_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the Whitaker service
        """
        endpoint = f"{self.base_url}/info"
        
        try:
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Failed to get service info: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get service info: {e}")
            return None
    
    def wait_for_service(self, timeout: int = 60) -> bool:
        """
        Wait for Whitaker service to become available
        """
        logger.info(f"⏳ Waiting for Whitaker service (timeout: {timeout}s)...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                health = self.health_check()
                if "healthy" in health.lower() or "200" in health:
                    logger.info("✅ Whitaker service is now available!")
                    return True
            except:
                pass
            
            time.sleep(2)
        
        logger.error(f"❌ Whitaker service did not become available within {timeout} seconds")
        return False


# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize client
    client = SimpleWhitakerClient(port=9090)
    
    # Test connection
    print(client.health_check())
    
    # Analyze a word
    result = client.analyze_word("amor")
    if result:
        print(f"Analysis result: {json.dumps(result, indent=2)}")
    
    # Analyze text
    text_result = client.analyze_text("Amo Deum et proximum.")
    if text_result:
        print(f"Text analysis: {json.dumps(text_result, indent=2)}")