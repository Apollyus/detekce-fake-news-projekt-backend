import requests
from source.modules.config import config  # Import konfiguračního objektu, ne celého modulu

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
        'key': api_key,
        'cx': search_engine_id,
        'q': query
    }
    
    try:
        # Odeslání GET požadavku
        response = requests.get(base_url, params=params)
        
        # Kontrola, zda byl požadavek úspěšný
        response.raise_for_status()
        
        # Získání odpovědi ve formátu JSON
        results = response.json()
        
        # Extrakce pouze potřebných informací
        simplified_results = []
        for item in results.get('items', []):
            simplified_results.append({
                'title': item.get('title'),
                'link': item.get('link'),
                'snippet': item.get('snippet')
            })
        
        return simplified_results
        
    except requests.exceptions.RequestException as e:
        print(f"Došlo k chybě: {e}")
        return None

# Ukázkové použití
if __name__ == "__main__":
    query = "Anna K zpěvačka zemřela 2025"
    
    results = google_search(query)
    print(results)
    '''
    if results:
        # Výpis prvních několika výsledků vyhledávání
        for item in results.get('items', []):
            print(f"Název: {item.get('title')}")
            print(f"Odkaz: {item.get('link')}")
            print(f"Úryvek: {item.get('snippet')}")
            print("-" * 50)
    '''