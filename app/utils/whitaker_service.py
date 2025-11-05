# app/utils/whitaker_service.py
import subprocess
import logging
import re
import json

logger = logging.getLogger(__name__)

class WhitakerService:
    def __init__(self, docker_image="whitaker-builder:latest"):
        self.docker_image = docker_image
    
    def analyze_word(self, word_form):
        """Analyze Latin word using Whitaker's Words Docker container"""
        try:
            # Run Whitaker's Words via Docker
            cmd = [
                'docker', 'run', '--rm',
                self.docker_image,
                '/opt/whitakers-words/bin/words',
                word_form
            ]
            
            logger.info(f"🔍 Running Whitaker analysis for: {word_form}")
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode == 0:
                return self._parse_whitaker_output(result.stdout, word_form)
            else:
                logger.error(f"Whitaker error: {result.stderr}")
                return {"error": f"Whitaker analysis failed: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            logger.error(f"Whitaker analysis timed out for: {word_form}")
            return {"error": "Analysis timed out"}
        except Exception as e:
            logger.error(f"Whitaker service error: {str(e)}")
            return {"error": f"Service error: {str(e)}"}
    
    def _parse_whitaker_output(self, output, original_word):
        """Parse Whitaker's Words output into structured data"""
        # Your parsing logic here
        return {
            "original_word": original_word,
            "analyses": [],  # Parsed analyses
            "meanings": []   # Extracted meanings
        }