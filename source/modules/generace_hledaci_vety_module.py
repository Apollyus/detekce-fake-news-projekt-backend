import re
import json
import sys
import os
from datetime import datetime
from openai import OpenAI

# Přidání root adresáře do sys.path pro import konfigurace
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Import konfigurace
try:
    from source.modules.config import config
except ImportError:
    # Fallback pro přímé spuštění
    sys.path.append(os.path.dirname(__file__))
    from config import config

def check_and_generate_search_phrase(user_input: str):
    # Získání API klíče z konfigurace
    api_key = config.OPENROUTER_API_KEY
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY není nastavený v environment proměnných")
    
    # Nastavení klienta pro OpenRouter
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    # Získání aktuálního data v čitelném formátu
    current_date = datetime.now().strftime("%d. %m. %Y")
    
    prompt = f"""
        Analyzuj text a rozhodni, zda obsahuje KONKRÉTNÍ OVĚŘITELNÉ TVRZENÍ.
        
        VALIDNÍ (valid=true) POUZE pokud obsahuje:
        - Konkrétní události: "Prezident podepsal zákon", "Anna K. zemřela"
        - Faktické informace: "Apple vydalo iPhone", "Nehoda na D1"
        - Konkrétní data: "Inflace je 5%", "Teplota 25°C"
        
        NEVALIDNÍ (valid=false) pokud obsahuje:
        - Pozdravy: "Ahoj", "Dobrý den", "Jak se máš?"
        - Otázky obecné: "Jaké je počasí?", "Kde bydlíš?"
        - Obecné pravdy: "Slunce je žluté", "Lidé potřebují jídlo"
        - Vágní výroky: "Něco se stalo", "Je zajímavé"
        
        PRAVIDLO: Při nejistotě nastav valid=false!

        Text: "{user_input}"
        Aktuální datum: {current_date}

        Odpověz pouze JSON:
        {{
        "search_query": "hledací fráze nebo prázdný řetězec",
        "valid": true nebo false,
        "confidence": číslo od 0.0 do 1.0,
        "keywords": ["klíčové slovo 1", "klíčové slovo 2", "klíčové slovo 3", ...]
        }}
"""

    try:
        chat_response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",  # Používáme Mistral model přes OpenRouter
            messages=[
                {
                    "role": "user",
                    "content": prompt.strip(),
                },
            ],
            temperature=0.3,
            max_tokens=500
        )

        content = chat_response.choices[0].message.content.strip()
        print("LLM odpověď:", content)

        try:
            # Pokus o parsování jako čistý JSON
            result = json.loads(content)
        except json.JSONDecodeError:
            # Fallback: Extrakce části s JSON pomocí regulárního výrazu
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
            else:
                raise ValueError("V odpovědi nebyl nalezen žádný JSON")
                
    except Exception as e:
        print("Chyba při volání API nebo parsování odpovědi:", e)
        result = {
            "search_query": "",
            "valid": False,
            "confidence": 0.0,
            "keywords": []
        }

    return result


# 💡 TEST
if __name__ == "__main__":
    test_cases = [
        "Zemřela česká zpěvačka Anna K.",  # Ověřitelné tvrzení
        "Jak se máš?",  # Konverzační text
        "Slunce je žluté a obloha je modrá",  # Nevalidní tvrzení (obecná pravda)
        "Prezident Pavel podepsal nový zákon o daních",  # Ověřitelné tvrzení
        "Dobrý den, jaké je dnes počasí?"  # Konverzační text
    ]
    
    print("Testování různých typů vstupů:")
    print("-" * 50)
    
    for test_input in test_cases:
        print(f"\nTest vstupu: '{test_input}'")
        result = check_and_generate_search_phrase(test_input)
        print("Výsledek:", result)
        print("-" * 50)