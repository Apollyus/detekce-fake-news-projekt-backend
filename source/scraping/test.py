import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import datetime

class SeznamZpravyArticleScraper:
    def __init__(self, article_url):
        if not article_url.startswith('http'):
            # If URL doesn't start with http, assume it's a path and join with base URL
            self.url = urljoin('https://www.seznamzpravy.cz', article_url)
        else:
            self.url = article_url
            
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def fetch(self):
        print(f"Fetching article from: {self.url}")
        response = requests.get(self.url, headers=self.headers)
        response.raise_for_status()
        return response.text
        
    def parse(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract the article information
        article_data = {
            'url': self.url,
            'title': None,
            'published_date': None,
            'author': None,
            'content': None,
            'summary': None
        }
        
        # Extract title - usually in h1
        title_elem = soup.select_one('h1')
        if title_elem:
            article_data['title'] = title_elem.get_text(strip=True)
        
        # Extract summary/perex - often in a specific class
        summary_elem = soup.select_one('.e_Ig')  # Adjust selector based on actual HTML structure
        if summary_elem:
            article_data['summary'] = summary_elem.get_text(strip=True)
            
        # Extract author
        author_elem = soup.select_one('[data-dot="author"]') or soup.select_one('.article__author')
        if author_elem:
            article_data['author'] = author_elem.get_text(strip=True)
            
        # Extract date - might be in various formats
        date_elem = soup.select_one('time')
        if date_elem:
            date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
            article_data['published_date'] = date_str
            
        # Extract content - usually in article paragraphs
        content_elems = soup.select('.article__body p') or soup.select('article p')
        if content_elems:
            article_data['content'] = '\n\n'.join([p.get_text(strip=True) for p in content_elems if p.get_text(strip=True)])
            
        return article_data
        
    def scrape(self):
        html = self.fetch()
        return self.parse(html)


if __name__ == '__main__':
    try:
        # Example article URL - replace with the actual article URL you want to scrape
        article_url = "https://www.novinky.cz/clanek/krimi-tragicka-nehoda-na-sokolovsku-tri-mrtvi-40516448"
        
        scraper = SeznamZpravyArticleScraper(article_url)
        print("Fetching article data...")
        html = scraper.fetch()
        print(f"Fetched {len(html)} bytes of HTML")
        
        # Save the HTML for inspection
        with open("debug_output.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        # Debug - check what elements are available
        soup = BeautifulSoup(html, 'html.parser')
        print("\nHTML structure exploration:")
        print("H1 element:", soup.select_one('h1').text if soup.select_one('h1') else "Not found")
        print("Article elements:", len(soup.select('article')))
        
        # Extract the actual article data
        article_data = scraper.parse(html)
        
        # Print the results
        print("\nArticle Data:")
        for key, value in article_data.items():
            if key == 'content':
                print(f"{key}: {value}" if value else "None")
            else:
                print(f"{key}: {value}")
                
    except Exception as e:
        print(f"Error occurred: {type(e).__name__}: {e}")