import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

class BaseScraper:
    """Base class for article scrapers with common functionality"""
    
    def __init__(self, article_url):
        self.url = article_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def fetch(self):
        """Fetch the HTML content of the article"""
        response = requests.get(self.url, headers=self.headers)
        response.raise_for_status()
        return response.text
    
    def scrape(self):
        """Scrape the article data"""
        html = self.fetch()
        return self.parse(html)
        
    def parse(self, html):
        """Parse HTML and extract article data - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement parse method")


class SeznamZpravyArticleScraper(BaseScraper):
    """Scraper for Seznam Zprávy articles"""
    
    def __init__(self, article_url):
        if not article_url.startswith('http'):
            article_url = urljoin('https://www.seznamzpravy.cz', article_url)
        super().__init__(article_url)
        
    def parse(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        
        article_data = {
            'url': self.url,
            'title': None,
            'published_date': None,
            'author': None,
            'content': None,
            'summary': None,
            'source': 'Seznam Zprávy'
        }
        
        title_elem = soup.select_one('h1')
        if title_elem:
            article_data['title'] = title_elem.get_text(strip=True)
        
        summary_elem = soup.select_one('.e_Ig')
        if summary_elem:
            article_data['summary'] = summary_elem.get_text(strip=True)
            
        author_elem = soup.select_one('[data-dot="author"]') or soup.select_one('.article__author')
        if author_elem:
            article_data['author'] = author_elem.get_text(strip=True)
            
        date_elem = soup.select_one('time')
        if date_elem:
            date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
            article_data['published_date'] = date_str
            
        content_elems = soup.select('.article__body p') or soup.select('article p')
        if content_elems:
            article_data['content'] = '\n\n'.join([p.get_text(strip=True) for p in content_elems if p.get_text(strip=True)])
            
        return article_data


class NovinkyArticleScraper(BaseScraper):
    """Scraper for Novinky.cz articles"""
    
    def __init__(self, article_url):
        if not article_url.startswith('http'):
            article_url = urljoin('https://www.novinky.cz', article_url)
        super().__init__(article_url)
        
    def parse(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        
        article_data = {
            'url': self.url,
            'title': None,
            'published_date': None,
            'author': None,
            'content': None,
            'summary': None,
            'source': 'Novinky.cz'
        }
        
        # Title is usually in h1
        title_elem = soup.select_one('h1')
        if title_elem:
            article_data['title'] = title_elem.get_text(strip=True)
        
        # Novinky often has a perex/summary in a specific class
        summary_elem = soup.select_one('.perex')
        if summary_elem:
            article_data['summary'] = summary_elem.get_text(strip=True)
            
        # Author might be in various locations
        author_elem = soup.select_one('.author') or soup.select_one('[itemprop="author"]')
        if author_elem:
            article_data['author'] = author_elem.get_text(strip=True)
            
        # Date is often in time element or specific class
        date_elem = soup.select_one('time') or soup.select_one('.article-date')
        if date_elem:
            date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
            article_data['published_date'] = date_str
            
        # Content paragraphs are usually in article or specific container
        content_elems = soup.select('.article-content p') or soup.select('article p')
        if content_elems:
            article_data['content'] = '\n\n'.join([p.get_text(strip=True) for p in content_elems if p.get_text(strip=True)])
            
        return article_data


class CT24ArticleScraper(BaseScraper):
    """Scraper for CT24 articles"""
    
    def __init__(self, article_url):
        if not article_url.startswith('http'):
            article_url = urljoin('https://ct24.ceskatelevize.cz', article_url)
        super().__init__(article_url)
        
    def parse(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        
        article_data = {
            'url': self.url,
            'title': None,
            'published_date': None,
            'author': None,
            'content': None,
            'summary': None,
            'source': 'ČT24'
        }
        
        # Title extraction
        title_elem = soup.select_one('h1')
        if title_elem:
            article_data['title'] = title_elem.get_text(strip=True)
        
        # CT24 often has lead/summary under different class
        summary_elem = soup.select_one('.article-perex') or soup.select_one('.article-lead')
        if summary_elem:
            article_data['summary'] = summary_elem.get_text(strip=True)
            
        # Author might be in byline or specific attribute
        author_elem = soup.select_one('.article-author') or soup.select_one('[itemprop="author"]')
        if author_elem:
            article_data['author'] = author_elem.get_text(strip=True)
            
        # Published date
        date_elem = soup.select_one('time') or soup.select_one('.article-date')
        if date_elem:
            date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
            article_data['published_date'] = date_str
            
        # Content - CT24 might have different content structure
        content_elems = soup.select('.article-body p') or soup.select('.article-content p') or soup.select('article p')
        if content_elems:
            article_data['content'] = '\n\n'.join([p.get_text(strip=True) for p in content_elems if p.get_text(strip=True)])
            
        return article_data


def detect_portal(url):
    """Detect which news portal the URL belongs to"""
    domain = urlparse(url).netloc.lower()
    
    if 'seznamzpravy.cz' in domain:
        return 'seznam'
    elif 'novinky.cz' in domain:
        return 'novinky'
    elif 'ceskatelevize.cz' in domain or 'ct24.cz' in domain:
        return 'ct24'
    else:
        return 'unknown'


def scrape_article(article_url, portal=None):
    """
    Scrape article content from a URL.
    
    Args:
        article_url (str): URL of the article to scrape
        portal (str, optional): The portal to scrape from ('seznam', 'novinky', 'ct24').
                              If not provided, auto-detection based on URL is used.
        
    Returns:
        dict: Dictionary containing article data (url, title, published_date, 
              author, content, summary, source)
              
    Raises:
        ValueError: If portal is not supported
    """
    # Auto-detect portal if not specified
    if not portal:
        portal = detect_portal(article_url)
    
    # Select appropriate scraper based on portal
    if portal.lower() == 'seznam':
        scraper = SeznamZpravyArticleScraper(article_url)
    elif portal.lower() == 'novinky':
        scraper = NovinkyArticleScraper(article_url)
    elif portal.lower() == 'ct24':
        scraper = CT24ArticleScraper(article_url)
    else:
        raise ValueError(f"Unsupported portal: {portal}")
    
    return scraper.scrape()