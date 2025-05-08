import requests
from source.modules.config import config
import logging

# Nastavení loggeru
logger = logging.getLogger(__name__)

# Získání API klíče z konfigurace
#api_key = os.getenv("GOOGLE_API_KEY")
#search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

api_key = config.GOOGLE_API_KEY  # Použití API klíče z konfiguračního souboru
search_engine_id = config.GOOGLE_SEARCH_ENGINE_ID  # Použití ID vyhledávače z konfiguračního souboru

def google_search(query):
    """
    Provádí vyhledávání pomocí Google Custom Search API.
    
    Args:
        query (str): Dotaz pro vyhledávání
        
    Returns:
        list: Seznam výsledků vyhledávání, nebo None v případě chyby
    """
    # Základní URL pro Google Custom Search API
    base_url = "https://www.googleapis.com/customsearch/v1"
    
    # Parametry pro HTTP požadavek
    params = {
        'key': config.GOOGLE_API_KEY,
        'cx': config.GOOGLE_SEARCH_ENGINE_ID,
        'q': query,
        'num': 10,  # Maximální počet výsledků
        'lr': 'lang_cs',  # Omezení na české výsledky
        'gl': 'cz',  # Geografické omezení na ČR
        'safe': 'active'  # Bezpečné vyhledávání
    }
    
    try:
        # Odeslání GET požadavku
        response = requests.get(base_url, params=params, timeout=10)
        
        # Kontrola, zda byl požadavek úspěšný
        response.raise_for_status()
        
        # Získání odpovědi ve formátu JSON
        results = response.json()
        
        # Extrakce pouze potřebných informací
        simplified_results = []
        for item in results.get('items', []):
            # Získání metadat stránky
            metatags = item.get('pagemap', {}).get('metatags', [{}])[0]
            
            # Vytvoření záznamu s rozšířenými informacemi
            result_item = {
                'title': item.get('title'),
                'link': item.get('link'),
                'snippet': item.get('snippet'),
                'display_link': item.get('displayLink'),
                'source': metatags.get('og:site_name') or item.get('displayLink'),
                'published_date': metatags.get('article:published_time') or metatags.get('date'),
                'author': metatags.get('author') or metatags.get('article:author'),
                'description': metatags.get('og:description') or metatags.get('description')
            }
            
            # Přidání pouze pokud máme alespoň základní informace
            if result_item['title'] and result_item['link']:
                simplified_results.append(result_item)
        
        if not simplified_results:
            logger.warning(f"Nenalezeny žádné výsledky pro dotaz: {query}")
            return None
            
        return simplified_results
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Chyba při vyhledávání: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Neočekávaná chyba při vyhledávání: {str(e)}")
        return None

# Ukázkové použití
if __name__ == "__main__":
    query = "Anna K zpěvačka zemřela 2025"
    results = google_search(query)
    
    if results:
        for item in results:
            print(f"Název: {item['title']}")
            print(f"Odkaz: {item['link']}")
            print(f"Zdroj: {item['source']}")
            print(f"Datum: {item['published_date']}")
            print(f"Autor: {item['author']}")
            print(f"Popis: {item['description']}")
            print("-" * 50)