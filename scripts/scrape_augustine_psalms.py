# scrape_augustine_psalms.py
#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import time
import sys
import os
import json
from datetime import datetime
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.simple_cassandra_client import SimpleCassandraClient

class AugustinePsalmsScraper:
    def __init__(self):
        self.base_url = "https://www.newadvent.org/fathers"
        self.client = SimpleCassandraClient(host=os.getenv("CASSANDRA_HOSTS", "127.0.0.1"))
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "data", "augustine")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
    
    def generate_psalm_url(self, psalm_number):
        """Generate the URL for a given psalm number"""
        if psalm_number < 10:
            return f"{self.base_url}/180100{psalm_number}.htm"
        elif psalm_number < 100:
            return f"{self.base_url}/18010{psalm_number:02d}.htm"
        else:
            return f"{self.base_url}/1801{psalm_number:03d}.htm"
    
    def save_psalm_to_json(self, psalm_number, content, source_url, success=True):
        """Save psalm data to JSON file"""
        psalm_data = {
            'psalm_number': psalm_number,
            'source_url': source_url,
            'scrape_timestamp': datetime.now().isoformat(),
            'success': success,
            'content': content if success else None,
            'error': None if success else content
        }
        
        filename = f"psalm_{psalm_number:03d}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(psalm_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved Psalm {psalm_number} to {filename}")
            return True
        except Exception as e:
            print(f"❌ Failed to save Psalm {psalm_number} to JSON: {e}")
            return False
    
    def load_psalm_from_json(self, psalm_number):
        """Load psalm data from JSON file"""
        filename = f"psalm_{psalm_number:03d}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load Psalm {psalm_number} from JSON: {e}")
            return None
    
    def scrape_psalm_exposition(self, psalm_number, force_refresh=False):
        """Scrape the exposition for a single psalm, with local caching"""
        
        # Check if we already have local data
        if not force_refresh:
            local_data = self.load_psalm_from_json(psalm_number)
            if local_data and local_data.get('success'):
                print(f"📁 Using cached data for Psalm {psalm_number}")
                return local_data['content']
        
        url = self.generate_psalm_url(psalm_number)
        
        try:
            print(f"🌐 Scraping Psalm {psalm_number}: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract the main content
            content = self.extract_content(soup)
            
            if content:
                # Save to local JSON
                self.save_psalm_to_json(psalm_number, content, url, success=True)
                return content
            else:
                error_msg = "No content found in HTML"
                self.save_psalm_to_json(psalm_number, error_msg, url, success=False)
                return None
            
        except requests.RequestException as e:
            error_msg = f"Network error: {e}"
            print(f"❌ Error scraping Psalm {psalm_number}: {error_msg}")
            self.save_psalm_to_json(psalm_number, error_msg, url, success=False)
            return None
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            print(f"❌ Unexpected error with Psalm {psalm_number}: {error_msg}")
            self.save_psalm_to_json(psalm_number, error_msg, url, success=False)
            return None
    
    def extract_content(self, soup):
        """Extract the main content from the HTML"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find the main content area
        content_areas = []
        
        # Look for common content containers in New Advent
        possible_selectors = [
            "body",
            ".content",
            "#content",
            "main",
            "article"
        ]
        
        for selector in possible_selectors:
            elements = soup.select(selector)
            if elements:
                content_areas.extend(elements)
        
        # If no specific containers found, use the whole body
        if not content_areas:
            content_areas = [soup.find('body')] if soup.find('body') else [soup]
        
        # Extract text from all content areas
        full_text = ""
        for area in content_areas:
            if area:
                text = area.get_text(separator='\n', strip=True)
                full_text += text + "\n\n"
        
        # Clean up the text
        cleaned_text = self.clean_text(full_text)
        return cleaned_text
    
    def clean_text(self, text):
        """Clean and format the extracted text"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Remove very short lines that are likely navigation or ads
        meaningful_lines = [line for line in lines if len(line) > 20]
        
        # Join back with reasonable spacing
        cleaned = '\n\n'.join(meaningful_lines)
        
        # Limit length to avoid database issues
        max_length = 100000
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length] + "... [TEXT TRUNCATED]"
            
        return cleaned
    
    def import_psalm_to_database(self, psalm_number):
        """Import a single psalm from local JSON to database"""
        local_data = self.load_psalm_from_json(psalm_number)
        
        if not local_data or not local_data.get('success'):
            print(f"❌ No valid local data for Psalm {psalm_number}")
            return False
        
        content = local_data['content']
        source_url = local_data['source_url']
        
        try:
            success = self.client.insert_psalm_exposition(
                psalm_number=psalm_number,
                verse_start=1,  # Whole psalm commentary
                verse_end=999,  # Indicates whole psalm
                work_title="Enarrationes in Psalmos",
                latin_text="",  # Primary content will be in english_translation
                english_translation=content,
                key_terms={"augustine", "exposition", f"psalm{psalm_number}"},
                source_url=source_url
            )
            
            if success:
                print(f"✅ Imported Psalm {psalm_number} to database")
            else:
                print(f"❌ Failed to import Psalm {psalm_number} to database")
            
            return success
            
        except Exception as e:
            print(f"❌ Error importing Psalm {psalm_number} to database: {e}")
            return False
    
    def scrape_all_psalms(self, start_psalm=1, end_psalm=150, force_refresh=False):
        """Scrape all psalms in the given range and save locally"""
        successful_scrapes = 0
        
        for psalm_num in range(start_psalm, end_psalm + 1):
            content = self.scrape_psalm_exposition(psalm_num, force_refresh)
            if content:
                successful_scrapes += 1
            
            # Be respectful to the server - add delay between requests
            time.sleep(2)
        
        print(f"\n🎉 Scraping completed!")
        print(f"📊 Local files saved: {successful_scrapes} out of {end_psalm - start_psalm + 1} psalms")
        print(f"📍 Location: {self.data_dir}")
        
        return successful_scrapes
    
    def import_all_psalms(self, start_psalm=1, end_psalm=150):
        """Import all locally saved psalms to database"""
        successful_imports = 0
        
        for psalm_num in range(start_psalm, end_psalm + 1):
            if self.import_psalm_to_database(psalm_num):
                successful_imports += 1
        
        print(f"\n🎉 Import completed!")
        print(f"📊 Psalms imported to database: {successful_imports} out of {end_psalm - start_psalm + 1}")
        
        return successful_imports
    
    def get_scraping_stats(self):
        """Get statistics about locally saved psalms"""
        if not os.path.exists(self.data_dir):
            return {"total": 0, "successful": 0, "failed": 0}
        
        json_files = [f for f in os.listdir(self.data_dir) if f.endswith('.json')]
        total = len(json_files)
        successful = 0
        
        for filename in json_files:
            try:
                filepath = os.path.join(self.data_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('success'):
                        successful += 1
            except:
                pass
        
        return {
            "total": total,
            "successful": successful,
            "failed": total - successful
        }
    
    def close(self):
        """Close the database connection"""
        self.client.close()

def main():
    parser = argparse.ArgumentParser(description="Scrape Augustine's Expositions on the Psalms")
    parser.add_argument('action', choices=['scrape', 'import', 'both', 'stats'], 
                       nargs='?', default='stats',
                       help='Action to perform: scrape (web to local), import (local to db), both, or stats (default)')
    parser.add_argument('--start', type=int, default=1, help='Start psalm number (default: 1)')
    parser.add_argument('--end', type=int, default=150, help='End psalm number (default: 150)')
    parser.add_argument('--force', action='store_true', help='Force refresh existing local files')
    
    args = parser.parse_args()
    
    print("🔍 Augustine's Expositions on the Psalms Scraper")
    print("📚 Source: New Advent Fathers of the Church")
    
    scraper = AugustinePsalmsScraper()
    
    try:
        # Show current stats
        stats = scraper.get_scraping_stats()
        print(f"📊 Current local files: {stats['successful']} successful, {stats['failed']} failed, {stats['total']} total")
        
        if args.action == 'stats':
            # Just show stats and exit
            scraper.close()
            return
        
        if args.action in ['scrape', 'both']:
            print(f"\n🌐 Scraping Psalms {args.start} to {args.end} from web...")
            if args.force:
                print("🔄 Force refresh enabled - re-scraping all psalms")
            scraper.scrape_all_psalms(args.start, args.end, force_refresh=args.force)
        
        if args.action in ['import', 'both']:
            print(f"\n💾 Importing Psalms {args.start} to {args.end} to database...")
            scraper.import_all_psalms(args.start, args.end)
        
        # Final stats
        stats = scraper.get_scraping_stats()
        print(f"\n📊 Final local files: {stats['successful']} successful, {stats['failed']} failed, {stats['total']} total")
        
    except KeyboardInterrupt:
        print("\n⏹️ Operation interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
