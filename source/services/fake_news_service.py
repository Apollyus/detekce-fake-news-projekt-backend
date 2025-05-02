from source.modules.generace_hledaci_vety_module import check_and_generate_search_phrase
from source.modules.vyhledavani_googlem_module import google_search
from source.modules.filtrace_clanku_module import filter_relevant_articles
from source.modules.finalni_rozhodnuti_module import evaluate_claim
from source.modules.telemetry_module import log_request_start, log_step_time, log_request_end, log_error, log_processing_data

def is_long_enough_words(text: str, min_words: int) -> bool:
    words = text.strip().split()
    return len(words) >= min_words

def is_too_long_words(text: str, max_words: int) -> bool:
    words = text.strip().split()
    return len(words) > max_words

def process_fake_news(prompt: str):
    # Start telemetry tracking
    request_context = log_request_start(prompt)
    
    try:
        # Check if text is too short
        if not is_long_enough_words(prompt, 4):
            result = {
                "status": "error",
                "message": "Zadaný text je příliš krátký pro ověření."
            }
            log_request_end(request_context, False, result)
            return result
            
        # Check if text is too long
        if is_too_long_words(prompt, 200):  # Setting 200 words as the maximum limit
            result = {
                "status": "error",
                "message": "Zadaný text je příliš dlouhý pro ověření."
            }
            log_request_end(request_context, False, result)
            return result
        
        first_part = check_and_generate_search_phrase(prompt)
        log_step_time(request_context, "search_phrase_generation")
        
        search_query = first_part["search_query"]
        valid = first_part["valid"]
        keywords = first_part["keywords"]
        
        # Log the search query and keywords
        log_processing_data(request_context, "search_query", search_query)
        log_processing_data(request_context, "keywords", keywords)
        log_processing_data(request_context, "is_valid_query", valid)
        
        if not valid:
            result = {
                "status": "error",
                "message": "Zadaný text není validní pro ověření..."
            }
            log_request_end(request_context, False, result)
            return result
            
        # Track Google search
        google_search_results = google_search(search_query)
        log_step_time(request_context, "google_search")
        
        # Log search results summary
        log_processing_data(request_context, "search_results_count", len(google_search_results) if google_search_results else 0)
        if google_search_results:
            # Log URLs without storing entire content
            search_urls = [result.get("link", "") for result in google_search_results]
            log_processing_data(request_context, "search_result_urls", search_urls)
        
        if not google_search_results:
            result = {
                "status": "error",
                "message": "Nenašli jsme žádné výsledky pro zadaný dotaz."
            }
            log_request_end(request_context, False, result)
            return result
            
        # Track article filtering
        filtered_articles = filter_relevant_articles(google_search_results, keywords)
        log_step_time(request_context, "article_filtering")
        
        # Log filtered articles summary
        log_processing_data(request_context, "filtered_articles_count", len(filtered_articles) if filtered_articles else 0)
        if filtered_articles:
            # Log titles/URLs without storing entire content
            filtered_titles = [article.get("title", "") for article in filtered_articles]
            log_processing_data(request_context, "filtered_article_titles", filtered_titles)
        
        if not filtered_articles:
            result = {
                "status": "error",
                "message": "Nenašli jsme žádné relevantní články pro ověření."
            }
            log_request_end(request_context, False, result)
            return result
            
        filtered_snippets = [article["snippet"] for article in filtered_articles]
        
        # Track claim evaluation
        rozhodnuti = evaluate_claim(prompt, filtered_snippets)
        log_step_time(request_context, "claim_evaluation")
        
        # Log the evaluation decision
        log_processing_data(request_context, "evaluation_result", rozhodnuti)
        
        if rozhodnuti:
            result = {
                "status": "success",
                "message": "Ověření bylo úspěšné.",
                "result": rozhodnuti,
                "filtered_articles": filtered_articles
            }
            log_request_end(request_context, True, result)
            return result
        
        result = {
            "status": "error",
            "message": "Chyba při ověřování tvrzení.",
            "filtered_articles": filtered_articles
        }
        log_request_end(request_context, False, result)
        return result

    except Exception as e:
        # Log any unexpected errors
        log_error(request_context, e)
        result = {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }
        log_request_end(request_context, False, result)
        return result