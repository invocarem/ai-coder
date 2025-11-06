# scripts/latin-words-docker.py
import subprocess
import json
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

class DockerWhitakerClient:
    """
    Client for Whitaker that uses docker exec for CLI tools
    """
    
    def __init__(self, container_name: str = "ai-coder-whitaker-1"):
        self.container_name = container_name
        logger.info(f"Initializing Docker Whitaker client for container: {container_name}")
    
    def analyze_word(self, word: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a word using docker exec
        """
        try:
            # Replace with the actual command your whitaker binary expects
            result = subprocess.run([
                'docker', 'exec', self.container_name,
                '/opt/whitaker/words', word  # Adjust path and command as needed
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"✅ Analyzed word: {word}")
                # Parse the output into a structured format
                return self._parse_whitaker_output(result.stdout)
            else:
                logger.error(f"❌ Whitaker analysis failed for '{word}': {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to analyze word '{word}': {e}")
            return None
    
    def _parse_whitaker_output(self, output: str) -> Dict[str, Any]:
        """
        Parse Whitaker's CLI output into structured JSON
        You'll need to customize this based on the actual output format
        """
        # This is a placeholder - adjust based on actual Whitaker output
        return {
            "original_output": output,
            "parsed": True,
            "words": output.split('\n')
        }
    
    def health_check(self) -> str:
        """Check if the container is running and responsive"""
        try:
            result = subprocess.run([
                'docker', 'exec', self.container_name, 'echo', 'test'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return "✅ Whitaker container is running and responsive"
            else:
                return f"❌ Whitaker container issue: {result.stderr}"
        except Exception as e:
            return f"❌ Whitaker health check failed: {e}"

# Usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = DockerWhitakerClient()
    
    print(client.health_check())
    result = client.analyze_word("amor")
    if result:
        print(f"Result: {json.dumps(result, indent=2)}")