"""
Modul pro sumarizaci textu pomocí LLM API (OpenRouter)
"""

from openai import OpenAI
from .config import config

def summarize_text(text: str, original_claim: str = "") -> str:
    """
    Sumarizuje zadaný text pomocí LLM API.
    
    Args:
        text (str): Text k sumarizaci
        original_claim (str): Původní tvrzení uživatele pro kontext
        
    Returns:
        str: Sumarizovaný text
        
    Raises:
        Exception: Pokud dojde k chybě při komunikaci s API
    """
    
    # Získání API klíče z konfigurace
    api_key = config.OPENROUTER_API_KEY
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY není nastavený v environment proměnných")
    
    # Nastavení klienta
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    # Příprava promptu
    prompt = f"""Jsi asistent pro fact-checking. Tvým úkolem je extrahovat nejdůležitější informace z následujícího článku. Soustřeď se POUZE na fakta a argumenty, které přímo souvisí s tvrzením: "{original_claim}".

        Ignoruj veškerou "omáčku", opakující se informace, příklady, které nejsou klíčové, a obecné úvodní či závěrečné fráze.

        Výstup musí být stručné a husté shrnutí klíčových bodů. Nepřidávej žádný vlastní názor. Výstup by neměl přesáhnout 200 slov.

        Text článku:
        \"\"\"
        {text}
        \"\"\"
        """
    
    try:
        # Volání API
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://bezfejku.cz",  # Site URL pro rankings
                "X-Title": "Bezfejku.cz - fake news detection for Czech republic",  # Site title pro rankings
            },
            extra_body={},
            model="google/gemma-3-27b-it",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=500,  # Omezení délky odpovědi
            temperature=0.1  # Nízká temperature pro konzistentní výsledky
        )
        
        # Vrácení sumarizovaného textu
        return completion.choices[0].message.content.strip()
        
    except Exception as e:
        raise Exception(f"Chyba při sumarizaci textu: {str(e)}")


def summarize_text_simple(text: str) -> str:
    """
    Jednoduchá verze sumarizace bez specifikace původního tvrzení.
    
    Args:
        text (str): Text k sumarizaci
        
    Returns:
        str: Sumarizovaný text
    """
    return summarize_text(text, "obecné informace")
