from typing import List, Dict, Any

def simple_similarity(text: str, keyword: str) -> float:
    """
    Vrací jednoduché skóre podobnosti na základě překryvu slov.
    """
    text_words = set(text.lower().split())
    keyword_words = set(keyword.lower().split())
    if not keyword_words:
        return 0.0
    match_count = sum(1 for word in keyword_words if word in text_words)
    return match_count / len(keyword_words)

def filter_relevant_articles(
    response_json: Dict[str, Any],
    keywords: List[str],
    threshold: float = 0.5
) -> List[Dict[str, str]]:
    """
    Filtruje relevantní články ze vstupního JSON z Google Custom Search API.

    Args:
        response_json: JSON odpověď jako Python slovník.
        keywords: Seznam klíčových slov/frází pro porovnání relevance.
        threshold: Prahová hodnota podobnosti (0–1), výchozí je 0.5.

    Returns:
        Seznam slovníků s relevantními články (title, link, snippet).
    """
    articles = response_json.get("items", [])
    relevant = []

    for article in articles:
        title = article.get("title", "")
        snippet = article.get("snippet", "")
        text = f"{title} {snippet}"

        if any(simple_similarity(text, kw) >= threshold for kw in keywords):
            relevant.append({
                "title": title,
                "link": article.get("link", ""),
                "snippet": snippet
            })

    return relevant
