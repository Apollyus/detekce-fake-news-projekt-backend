from source.modules.generace_hledaci_vety_module import check_and_generate_search_phrase
from source.modules.vyhledavani_googlem_module import google_search
from source.modules.filtrace_clanku_module import filter_relevant_articles
from source.modules.finalni_rozhodnuti_module import evaluate_claim
from source.modules.telemetry_module import log_request_start, log_step_time, log_request_end, log_error, log_processing_data
from source.modules.scraping_module import scrape_article, detect_portal

"""
Servisní modul pro detekci fake news.

Tento modul poskytuje funkce pro:
- kontrolu délky vstupního textu
- asynchronní zpracování detekce fake news zahrnující:
  generování vyhledávací fráze, vyhledávání Googlem,
  filtrování relevantních článků, vyhodnocení tvrzení
  a záznam telemetry dat.
"""

def is_long_enough_words(text: str, min_words: int) -> bool:
    """
    Zkontroluje, zda text obsahuje alespoň minimální počet slov.

    Parametry:
        text: Vstupní text ke kontrole.
        min_words: Minimální požadovaný počet slov.

    Vrací:
        True, pokud text obsahuje alespoň min_words slov, jinak False.
    """
    words = text.strip().split()
    return len(words) >= min_words

def is_too_long_words(text: str, max_words: int) -> bool:
    """
    Zkontroluje, zda text překračuje maximální počet slov.

    Parametry:
        text: Vstupní text ke kontrole.
        max_words: Maximální povolený počet slov.

    Vrací:
        True, pokud text obsahuje více než max_words slov, jinak False.
    """
    words = text.strip().split()
    return len(words) > max_words

async def process_fake_news(prompt: str):
    """
    Asynchronně zpracuje detekci fake news pro zadaný text.

    Kroky:
    1. Spuštění telemetry měření.
    2. Validace délky textu (min. 4 slova, max. 200 slov).
    3. Generování vyhledávací fráze a klíčových slov.
    4. Vyhledávání Googlem.
    5. Filtrování relevantních článků.
    6. Scraping obsahu článků.
    7. Vyhodnocení tvrzení na základě plného obsahu článků.
    8. Zaznamenání výsledků a ukončení telemetry.

    Parametry:
        prompt: Text k ověření.

    Vrací:
        Dict se stavem, zprávou a případně výsledkem nebo filtrovnými články.
    """
    # 1) Start telemetry měření
    request_context = await log_request_start(prompt)
    
    try:
        # 2a) Kontrola, zda je text dostatečně dlouhý
        if not is_long_enough_words(prompt, 4):
            result = {
                "status": "error",
                "message": "Zadaný text je příliš krátký pro ověření."
            }
            await log_request_end(request_context, False, result)
            return result
            
        # 2b) Kontrola, zda text není příliš dlouhý
        if is_too_long_words(prompt, 200):
            result = {
                "status": "error",
                "message": "Zadaný text je příliš dlouhý pro ověření."
            }
            await log_request_end(request_context, False, result)
            return result
        
        # 3) Generování vyhledávací fráze a klíčových slov
        first_part = check_and_generate_search_phrase(prompt)
        log_step_time(request_context, "search_phrase_generation")
        
        search_query = first_part["search_query"]
        valid = first_part["valid"]
        keywords = first_part["keywords"]
        
        # Zaznamenej vyhledávací frázi, klíčová slova a validitu dotazu
        log_processing_data(request_context, "search_query", search_query)
        log_processing_data(request_context, "keywords", keywords)
        log_processing_data(request_context, "is_valid_query", valid)
        
        if not valid:
            result = {
                "status": "error",
                "message": "Zadaný text není validní pro ověření."
            }
            await log_request_end(request_context, False, result)
            return result
            
        # 4) Vyhledávání pomocí Google API
        google_search_results = google_search(search_query)
        log_step_time(request_context, "google_search")
        
        # Zaznamenání počtu výsledků hledání
        log_processing_data(request_context, "search_results_count", len(google_search_results) if google_search_results else 0)
        if google_search_results:
            # Logování URL adres bez ukládání obsahu
            search_urls = [item.get("link", "") for item in google_search_results]
            log_processing_data(request_context, "search_result_urls", search_urls)
        
        if not google_search_results:
            result = {
                "status": "error",
                "message": "Nenašli jsme žádné výsledky pro zadaný dotaz."
            }
            await log_request_end(request_context, False, result)
            return result
            
        '''# 5) Filtrování relevantních článků podle klíčových slov
        filtered_articles = filter_relevant_articles(google_search_results, keywords)
        log_step_time(request_context, "article_filtering")
        
        # Záznam počtu filtrovaných článků
        log_processing_data(request_context, "filtered_articles_count", len(filtered_articles) if filtered_articles else 0)
        if filtered_articles:
            # Logování názvů článků bez ukládání plného obsahu
            filtered_titles = [article.get("title", "") for article in filtered_articles]
            log_processing_data(request_context, "filtered_article_titles", filtered_titles)
        
        if not filtered_articles:
            result = {
                "status": "error",
                "message": "Nenašli jsme žádné relevantní články pro ověření."
            }
            await log_request_end(request_context, False, result)
            return result'''
        
        filtered_articles = google_search_results
        
        # 6) Scraping obsahu článků
        scraped_articles = []
        for article in filtered_articles:
            try:
                portal = detect_portal(article["link"])
                if portal != "unknown":
                    scraped_content = scrape_article(article["link"], portal)
                    if scraped_content and scraped_content.get("content"):
                        article["full_content"] = scraped_content["content"]
                        article["source"] = scraped_content["source"]
                        article["published_date"] = scraped_content["published_date"]
                        article["author"] = scraped_content["author"]
                        scraped_articles.append(article)
            except Exception as e:
                log_processing_data(request_context, "scraping_error", f"Error scraping {article['link']}: {str(e)}")
                continue
        
        log_step_time(request_context, "article_scraping")
        
        if not scraped_articles:
            result = {
                "status": "error",
                "message": "Nepodařilo se získat obsah článků pro ověření.",
                "filtered_articles": filtered_articles
            }
            await log_request_end(request_context, False, result)
            return result
        
        # 7) Připrav obsah článků pro vyhodnocení tvrzení
        article_contents = [article["full_content"] for article in scraped_articles]
        
        # 8) Vyhodnocení tvrzení
        rozhodnuti = evaluate_claim(prompt, article_contents)
        log_step_time(request_context, "claim_evaluation")
        
        # Zaznamenání výsledku vyhodnocení
        log_processing_data(request_context, "evaluation_result", rozhodnuti)
        
        if rozhodnuti:
            result = {
                "status": "success",
                "message": "Ověření bylo úspěšné.",
                "result": rozhodnuti,
                "filtered_articles": scraped_articles
            }
            await log_request_end(request_context, True, result)
            return result
        
        # Chyba při vyhodnocování tvrzení
        result = {
            "status": "error",
            "message": "Chyba při ověřování tvrzení.",
            "filtered_articles": scraped_articles
        }
        await log_request_end(request_context, False, result)
        return result

    except Exception as e:
        # 9) Záznam neočekávaných chyb
        await log_error(request_context, e)
        result = {
            "status": "error",
            "message": f"Neočekávaná chyba: {str(e)}"
        }
        await log_request_end(request_context, False, result)
        return result