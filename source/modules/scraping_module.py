import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import logging

# Nastavení loggeru
logger = logging.getLogger(__name__)

class BaseScraper:
    """Základní třída pro scrapery článků s běžnou funkcionalitou"""
    
    def __init__(self, article_url):
        self.url = article_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def fetch(self):
        """Načte HTML obsah článku"""
        response = requests.get(self.url, headers=self.headers)
        response.raise_for_status()
        return response.text
    
    def scrape(self):
        """Vyextrahuje data článku"""
        html = self.fetch()
        return self.parse(html)
        
    def parse(self, html):
        """Zpracuje HTML a extrahuje data článku - musí být implementováno v podtřídách"""
        raise NotImplementedError("Podtřídy musí implementovat metodu parse")


class SeznamZpravyArticleScraper(BaseScraper):
    """Scraper pro články ze Seznam Zprávy"""
    
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
    """Scraper pro články z Novinky.cz"""
    
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
        
        # Titulek je obvykle v h1
        title_elem = soup.select_one('h1')
        if title_elem:
            article_data['title'] = title_elem.get_text(strip=True)
        
        # Novinky často mají perex/souhrn ve specifické třídě
        summary_elem = soup.select_one('.perex')
        if summary_elem:
            article_data['summary'] = summary_elem.get_text(strip=True)
            
        # Autor může být na různých místech
        author_elem = soup.select_one('.author') or soup.select_one('[itemprop="author"]')
        if author_elem:
            article_data['author'] = author_elem.get_text(strip=True)
            
        # Datum je často v elementu time nebo ve specifické třídě
        date_elem = soup.select_one('time') or soup.select_one('.article-date')
        if date_elem:
            date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
            article_data['published_date'] = date_str
            
        # Obsah článku je obvykle v elementu article nebo specifickém kontejneru
        content_elems = soup.select('.article-content p') or soup.select('article p')
        if content_elems:
            article_data['content'] = '\n\n'.join([p.get_text(strip=True) for p in content_elems if p.get_text(strip=True)])
            
        return article_data


class CT24ArticleScraper(BaseScraper):
    """Scraper pro články z ČT24"""
    
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
        
        # Extrakce titulku
        title_elem = soup.select_one('h1')
        if title_elem:
            article_data['title'] = title_elem.get_text(strip=True)
        
        # ČT24 často má lead/souhrn pod jinou třídou
        summary_elem = soup.select_one('.article-perex') or soup.select_one('.article-lead')
        if summary_elem:
            article_data['summary'] = summary_elem.get_text(strip=True)
            
        # Autor může být v byline nebo specifickém atributu
        author_elem = soup.select_one('.article-author') or soup.select_one('[itemprop="author"]')
        if author_elem:
            article_data['author'] = author_elem.get_text(strip=True)
            
        # Datum publikace
        date_elem = soup.select_one('time') or soup.select_one('.article-date')
        if date_elem:
            date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
            article_data['published_date'] = date_str
            
        # Obsah - ČT24 může mít odlišnou strukturu obsahu
        content_elems = soup.select('.article-body p') or soup.select('.article-content p') or soup.select('article p')
        if content_elems:
            article_data['content'] = '\n\n'.join([p.get_text(strip=True) for p in content_elems if p.get_text(strip=True)])
            
        return article_data


class IDnesArticleScraper(BaseScraper):
    """Scraper pro články z iDNES.cz"""
    
    def __init__(self, article_url):
        if not article_url.startswith('http'):
            article_url = urljoin('https://www.idnes.cz', article_url)
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
            'source': 'iDNES.cz'
        }
        
        # Titulek
        title_elem = soup.select_one('h1')
        if title_elem:
            article_data['title'] = title_elem.get_text(strip=True)
        
        # Perex
        summary_elem = soup.select_one('.opener')
        if summary_elem:
            article_data['summary'] = summary_elem.get_text(strip=True)
            
        # Autor
        author_elem = soup.select_one('.authors')
        if author_elem:
            article_data['author'] = author_elem.get_text(strip=True)
            
        # Datum
        date_elem = soup.select_one('time')
        if date_elem:
            date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
            article_data['published_date'] = date_str
            
        # Obsah
        content_elems = soup.select('.text p')
        if content_elems:
            article_data['content'] = '\n\n'.join([p.get_text(strip=True) for p in content_elems if p.get_text(strip=True)])
            
        return article_data


class AktualneArticleScraper(BaseScraper):
    """Scraper pro články z Aktuálně.cz"""
    
    def __init__(self, article_url):
        if not article_url.startswith('http'):
            article_url = urljoin('https://www.aktualne.cz', article_url)
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
            'source': 'Aktuálně.cz'
        }
        
        # Titulek
        title_elem = soup.select_one('h1')
        if title_elem:
            article_data['title'] = title_elem.get_text(strip=True)
        
        # Perex
        summary_elem = soup.select_one('.perex')
        if summary_elem:
            article_data['summary'] = summary_elem.get_text(strip=True)
            
        # Autor
        author_elem = soup.select_one('.author')
        if author_elem:
            article_data['author'] = author_elem.get_text(strip=True)
            
        # Datum
        date_elem = soup.select_one('time')
        if date_elem:
            date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
            article_data['published_date'] = date_str
            
        # Obsah
        content_elems = soup.select('.article-content p')
        if content_elems:
            article_data['content'] = '\n\n'.join([p.get_text(strip=True) for p in content_elems if p.get_text(strip=True)])
            
        return article_data


class DenikArticleScraper(BaseScraper):
    """Scraper pro články z Deník.cz"""
    
    def __init__(self, article_url):
        if not article_url.startswith('http'):
            article_url = urljoin('https://www.denik.cz', article_url)
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
            'source': 'Deník.cz'
        }
        
        # Titulek
        title_elem = soup.select_one('h1')
        if title_elem:
            article_data['title'] = title_elem.get_text(strip=True)
        
        # Perex
        summary_elem = soup.select_one('.perex')
        if summary_elem:
            article_data['summary'] = summary_elem.get_text(strip=True)
            
        # Autor
        author_elem = soup.select_one('.author')
        if author_elem:
            article_data['author'] = author_elem.get_text(strip=True)
            
        # Datum
        date_elem = soup.select_one('time')
        if date_elem:
            date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
            article_data['published_date'] = date_str
            
        # Obsah
        content_elems = soup.select('.article-content p')
        if content_elems:
            article_data['content'] = '\n\n'.join([p.get_text(strip=True) for p in content_elems if p.get_text(strip=True)])
            
        return article_data


class GenericArticleScraper(BaseScraper):
    """Obecný scraper pro nepodporované zpravodajské portály"""
    
    def __init__(self, article_url):
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
            'source': urlparse(self.url).netloc
        }
        
        # Pokus o extrakci titulku - zkusíme různé běžné selektory
        title_selectors = [
            'h1',  # Nejběžnější
            'article h1',  # Článek v article tagu
            '.article-title',  # Běžná třída
            '.post-title',
            '.entry-title',
            '[itemprop="headline"]',  # Schema.org
            'meta[property="og:title"]'  # Open Graph
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                if selector.startswith('meta'):
                    article_data['title'] = title_elem.get('content', '').strip()
                else:
                    article_data['title'] = title_elem.get_text(strip=True)
                break
        
        # Pokus o extrakci perexu/souhrnu
        summary_selectors = [
            '.perex',
            '.summary',
            '.article-summary',
            '.article-lead',
            '.article-intro',
            'meta[name="description"]',
            'meta[property="og:description"]'
        ]
        
        for selector in summary_selectors:
            summary_elem = soup.select_one(selector)
            if summary_elem:
                if selector.startswith('meta'):
                    article_data['summary'] = summary_elem.get('content', '').strip()
                else:
                    article_data['summary'] = summary_elem.get_text(strip=True)
                break
        
        # Pokus o extrakci autora
        author_selectors = [
            '.author',
            '.article-author',
            '.post-author',
            '[itemprop="author"]',
            'meta[name="author"]'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                if selector.startswith('meta'):
                    article_data['author'] = author_elem.get('content', '').strip()
                else:
                    article_data['author'] = author_elem.get_text(strip=True)
                break
        
        # Pokus o extrakci data
        date_selectors = [
            'time',
            '.date',
            '.article-date',
            '.post-date',
            '[itemprop="datePublished"]',
            'meta[property="article:published_time"]'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                if selector.startswith('meta'):
                    article_data['published_date'] = date_elem.get('content', '').strip()
                else:
                    date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    article_data['published_date'] = date_str
                break
        
        # Pokus o extrakci obsahu
        content_selectors = [
            'article p',  # Nejběžnější
            '.article-content p',
            '.post-content p',
            '.entry-content p',
            '[itemprop="articleBody"] p',
            '.text p',
            '.content p'
        ]
        
        for selector in content_selectors:
            content_elems = soup.select(selector)
            if content_elems:
                # Filtrujeme prázdné odstavce a reklamy
                filtered_content = []
                for p in content_elems:
                    text = p.get_text(strip=True)
                    if text and len(text) > 20 and not any(ad in text.lower() for ad in ['reklama', 'sponzor', 'advertisement']):
                        filtered_content.append(text)
                
                if filtered_content:
                    article_data['content'] = '\n\n'.join(filtered_content)
                    break
        
        # Pokud nemáme obsah, zkusíme najít jakýkoliv text v článku
        if not article_data['content']:
            main_content_selectors = [
                'article',
                '.article-content',
                '.post-content',
                '.entry-content',
                '[itemprop="articleBody"]',
                '.text',
                '.content'
            ]
            
            for selector in main_content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Odstraníme skripty, styly a komentáře
                    for script in content_elem(['script', 'style', 'nav', 'header', 'footer']):
                        script.decompose()
                    
                    # Získáme text a rozdělíme na odstavce
                    text = content_elem.get_text('\n', strip=True)
                    paragraphs = [p.strip() for p in text.split('\n') if p.strip() and len(p.strip()) > 20]
                    
                    if paragraphs:
                        article_data['content'] = '\n\n'.join(paragraphs)
                        break
        
        return article_data


def detect_portal(url):
    """Detekuje, kterému zpravodajskému portálu URL patří"""
    domain = urlparse(url).netloc.lower()
    
    if 'seznamzpravy.cz' in domain:
        return 'seznam'
    elif 'novinky.cz' in domain:
        return 'novinky'
    elif 'ceskatelevize.cz' in domain or 'ct24.cz' in domain:
        return 'ct24'
    elif 'idnes.cz' in domain:
        return 'idnes'
    elif 'aktualne.cz' in domain:
        return 'aktualne'
    elif 'denik.cz' in domain:
        return 'denik'
    else:
        return 'generic'


def scrape_article(article_url, portal=None):
    """
    Extrahuje obsah článku z URL.
    
    Parametry:
        article_url (str): URL článku ke zpracování
        portal (str, optional): Portál, ze kterého se má extrahovat.
                              Pokud není specifikován, použije se automatická detekce podle URL.
        
    Vrací:
        dict: Slovník obsahující data článku (url, title, published_date, 
              author, content, summary, source)
              
    Vyjímky:
        ValueError: Pokud portál není podporován
    """
    # Automatická detekce portálu, pokud není specifikován
    if not portal:
        portal = detect_portal(article_url)
    
    try:
        # Výběr vhodného scraperu podle portálu
        if portal.lower() == 'seznam':
            scraper = SeznamZpravyArticleScraper(article_url)
        elif portal.lower() == 'novinky':
            scraper = NovinkyArticleScraper(article_url)
        elif portal.lower() == 'ct24':
            scraper = CT24ArticleScraper(article_url)
        elif portal.lower() == 'idnes':
            scraper = IDnesArticleScraper(article_url)
        elif portal.lower() == 'aktualne':
            scraper = AktualneArticleScraper(article_url)
        elif portal.lower() == 'denik':
            scraper = DenikArticleScraper(article_url)
        elif portal.lower() == 'generic':
            scraper = GenericArticleScraper(article_url)
        else:
            logger.warning(f"Nepodporovaný portál: {portal}, použití obecného scraperu")
            scraper = GenericArticleScraper(article_url)
        
        return scraper.scrape()
        
    except Exception as e:
        logger.error(f"Chyba při scrapování článku {article_url}: {str(e)}")
        # Pokud selže specializovaný scraper, zkusíme obecný
        if portal.lower() != 'generic':
            logger.info(f"Zkouším obecný scraper pro {article_url}")
            try:
                scraper = GenericArticleScraper(article_url)
                return scraper.scrape()
            except Exception as e2:
                logger.error(f"Selhal i obecný scraper pro {article_url}: {str(e2)}")
                raise
        else:
            raise