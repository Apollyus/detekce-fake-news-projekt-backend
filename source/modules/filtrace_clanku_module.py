from typing import List, Dict, Any

def simple_similarity(text: str, keyword: str) -> float:
    """
    Vrací jednoduché skóre podobnosti na základě překryvu slov mezi textem a klíčovým slovem.
    
    Args:
        text: Analyzovaný text.
        keyword: Klíčové slovo nebo fráze pro porovnání.
        
    Returns:
        float: Skóre podobnosti v rozsahu 0.0-1.0.
    """
    # Převedení textu a klíčového slova na množiny slov (malými písmeny)
    text_words = set(text.lower().split())
    keyword_words = set(keyword.lower().split())
    
    # Kontrola prázdného klíčového slova
    if not keyword_words:
        return 0.0
        
    # Výpočet počtu shodných slov
    match_count = sum(1 for word in keyword_words if word in text_words)
    
    # Vrácení poměru shodných slov k celkovému počtu slov v klíčovém slově
    return match_count / len(keyword_words)

def filter_relevant_articles(
    response_json: Dict[str, Any],
    keywords: List[str],
    threshold: float = 0.5
) -> List[Dict[str, str]]:
    """
    Filtruje relevantní články ze vstupního JSON z Google Custom Search API.

    Args:
        response_json: JSON odpověď jako Python slovník nebo seznam.
        keywords: Seznam klíčových slov/frází pro porovnání relevance.
        threshold: Prahová hodnota podobnosti (0–1), výchozí je 0.5.

    Returns:
        Seznam slovníků s relevantními články (title, link, snippet).
    """
    # Zpracování různých formátů odpovědi (seznam nebo slovník)
    if isinstance(response_json, dict):
        articles = response_json.get("items", [])
    else:
        articles = response_json
        
    relevant = []

    # Procházení všech článků a kontrola jejich relevance
    for article in articles:
        title = article.get("title", "")
        snippet = article.get("snippet", "")
        
        # Spojení titulku a snippetu pro analýzu podobnosti
        text = f"{title} {snippet}"

        # Kontrola, zda jakékoliv klíčové slovo překračuje práh podobnosti
        if any(simple_similarity(text, kw) >= threshold for kw in keywords):
            relevant.append({
                "title": title,
                "link": article.get("link", ""),
                "snippet": snippet
            })

    return relevant