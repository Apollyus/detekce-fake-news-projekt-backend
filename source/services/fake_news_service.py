from source.modules.generace_hledaci_vety_module import check_and_generate_search_phrase
from source.modules.vyhledavani_googlem_module import google_search
from source.modules.filtrace_clanku_module import filter_relevant_articles
from source.modules.finalni_rozhodnuti_module import evaluate_claim

def is_long_enough_words(text: str, min_words: int) -> bool:
    words = text.strip().split()
    return len(words) >= min_words

def process_fake_news(prompt: str):
    if is_long_enough_words(prompt, 4):
        first_part = check_and_generate_search_phrase(prompt)
        search_query = first_part["search_query"]
        valid = first_part["valid"]
        keywords = first_part["keywords"]
        
        if not valid:
            return {
                "status": "error",
                "message": "Zadaný text není validní pro ověření..."
            }
            
        google_search_results = google_search(search_query)
        if not google_search_results:
            return {
                "status": "error",
                "message": "Nenašli jsme žádné výsledky pro zadaný dotaz."
            }
            
        filtered_articles = filter_relevant_articles(google_search_results, keywords)
        if not filtered_articles:
            return {
                "status": "error",
                "message": "Nenašli jsme žádné relevantní články pro ověření."
            }
            
        filtered_snippets = [article["snippet"] for article in filtered_articles]
        rozhodnuti = evaluate_claim(prompt, filtered_snippets)
        
        if rozhodnuti:
            return {
                "status": "success",
                "message": "Ověření bylo úspěšné.",
                "result": rozhodnuti,
                "filtered_articles": filtered_articles
            }
        
        return {
            "status": "error",
            "message": "Chyba při ověřování tvrzení.",
            "filtered_articles": filtered_articles
        }
    else:
        first_part = check_and_generate_search_phrase(prompt)
        search_query = first_part["search_query"]
        valid = first_part["valid"]
        keywords = first_part["keywords"]
        #TADY JE CHYBA NEBO PROSTE NECO
        if not valid:
            return {
                "status": "error",
                "message": "Zadaný text není validní pro ověření...............",
                "prompt: " : str(prompt),
                "first_part: " : str(first_part),
                "search_query: " : str(search_query),
                "valid: " : str(valid),
                "keywords: " : str(keywords)
            }
            
        google_search_results = google_search(search_query)
        if not google_search_results:
            return {
                "status": "error",
                "message": "Nenašli jsme žádné výsledky pro zadaný dotaz."
            }
            
        filtered_articles = filter_relevant_articles(google_search_results, keywords)
        if not filtered_articles:
            return {
                "status": "error",
                "message": "Nenašli jsme žádné relevantní články pro ověření."
            }
            
        filtered_snippets = [article["snippet"] for article in filtered_articles]
        rozhodnuti = evaluate_claim(prompt, filtered_snippets)
        
        if rozhodnuti:
            return {
                "status": "success",
                "message": "Ověření bylo úspěšné.",
                "result": rozhodnuti,
                "filtered_articles": filtered_articles
            }
        
        return {
            "status": "error",
            "message": "Chyba při ověřování tvrzení.",
            "filtered_articles": filtered_articles
        }