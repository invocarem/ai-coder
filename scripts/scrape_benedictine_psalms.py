# scrape_benedictine_psalms.py
#!/usr/bin/env python3
import json
import sys
import os
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.simple_cassandra_client import SimpleCassandraClient

class BenedictinePsalmsScraper:
    def __init__(self):
        self.client = SimpleCassandraClient()
    
    def load_psalms_from_json(self, json_file_path: str) -> List[Dict[str, Any]]:
        """Load Psalms data from JSON file"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                psalms_data = json.load(f)
            print(f"✅ Loaded {len(psalms_data)} Psalms from {json_file_path}")
            return psalms_data
        except Exception as e:
            print(f"❌ Error loading JSON file: {e}")
            return []
    
    def insert_psalm_with_sections(self, psalm_data: Dict[str, Any]) -> bool:
        """Insert a single Psalm with section support"""
        try:
            psalm_number = psalm_data['number']
            section = psalm_data.get('section', '')  # Default to empty string if no section
            
            latin_verses = psalm_data.get('text', [])
            english_verses = psalm_data.get('englishText', [])
            
            # Insert each verse
            for verse_num, (latin_text, english_text) in enumerate(zip(latin_verses, english_verses), 1):
                success = self.client.insert_psalm_verse(
                    psalm_number=psalm_number,
                    section=section,  # NEW: Include section
                    verse_number=verse_num,
                    latin_text=latin_text,
                    english_translation=english_text,
                    grammatical_notes=""  # You can add grammatical analysis later
                )
                
                if not success:
                    print(f"❌ Failed to insert Psalm {psalm_number}{section}:{verse_num}")
                    return False
            
            print(f"✅ Inserted Psalm {psalm_number}{f' ({section})' if section else ''} with {len(latin_verses)} verses")
            return True
            
        except Exception as e:
            print(f"❌ Error inserting Psalm {psalm_data.get('number', 'unknown')}: {e}")
            return False
    
    def scrape_all_psalms(self, json_file_path: str):
        """Scrape all Psalms from JSON file to Cassandra"""
        psalms_data = self.load_psalms_from_json(json_file_path)
        
        if not psalms_data:
            print("❌ No Psalms data loaded")
            return
        
        successful_psalms = 0
        total_verses = 0
        
        for psalm in psalms_data:
            if self.insert_psalm_with_sections(psalm):
                successful_psalms += 1
                total_verses += len(psalm.get('text', []))
        
        print(f"\n🎉 Scraping completed!")
        print(f"📊 Summary:")
        print(f"  Successful Psalms: {successful_psalms}/{len(psalms_data)}")
        print(f"  Total verses inserted: {total_verses}")
        
        return successful_psalms
    
    def close(self):
        """Close database connection"""
        self.client.close()

def main():
    print("📖 Benedictine Office Psalms Scraper")
    print("📚 Loading liturgical Psalms with sections...")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    json_file_path = os.path.join(project_root, "app", "data", "psalms.json")
    
    print(f"🔍 Looking for Psalms data at: {json_file_path}")
    
    if not os.path.exists(json_file_path):
        print(f"❌ JSON file not found: {json_file_path}")
        print("Please make sure your psalms.json file is in the ai-coder/data/ folder")
        return
   
    scraper = BenedictinePsalmsScraper()
    
    try:
        scraper.scrape_all_psalms(json_file_path)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()