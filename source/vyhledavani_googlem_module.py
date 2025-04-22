import requests
from source.config import config  # Import the config instance, not the module

# Get the API key from environment variables
#api_key = os.getenv("GOOGLE_API_KEY")
#search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

api_key = config.GOOGLE_API_KEY  # Use the API key from the config
search_engine_id = config.GOOGLE_SEARCH_ENGINE_ID  # Use the search engine ID from the config

def google_search(query):
    # Base URL for Google Custom Search API
    base_url = "https://www.googleapis.com/customsearch/v1"
    
    # Parameters for the request
    params = {
        'key': api_key,
        'cx': search_engine_id,
        'q': query
    }
    
    try:
        # Make the GET request
        response = requests.get(base_url, params=params)
        
        # Check if request was successful
        response.raise_for_status()
        
        # Get the JSON response
        results = response.json()
        
        # Extract only the required information
        simplified_results = []
        for item in results.get('items', []):
            simplified_results.append({
                'title': item.get('title'),
                'link': item.get('link'),
                'snippet': item.get('snippet')
            })
        
        return simplified_results
        
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

# Example usage
if __name__ == "__main__":
    query = "Anna K zpěvačka zemřela 2025"
    
    results = google_search(query)
    print(results)
    '''
    if results:
        # Print the first few search results
        for item in results.get('items', []):
            print(f"Title: {item.get('title')}")
            print(f"Link: {item.get('link')}")
            print(f"Snippet: {item.get('snippet')}")
            print("-" * 50)
    '''