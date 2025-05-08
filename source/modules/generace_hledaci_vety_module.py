import re
from datetime import datetime
from mistralai import Mistral
from source.modules.config import config  # Import instance konfigurace, ne modul

api_key = config.MISTRAL_API_KEY  # Použití API klíče z konfigurace
model = "mistral-small-latest"  # Změněno na platný název modelu

client = Mistral(api_key=api_key)

def check_and_generate_search_phrase(user_input: str):
    # Získání aktuálního data v čitelném formátu
    current_date = datetime.now().strftime("%d. %m. %Y")
    
    prompt = f"""
        Zhodnoť následující text a rozhodni, zda jde o tvrzení, které lze ověřit na internetu.
        
        Typy textů:
        1. OVĚŘITELNÉ TVRZENÍ - obsahuje konkrétní fakta, která lze ověřit (např. "Prezident Zeman podepsal zákon")
        2. KONVERZAČNÍ TEXT - běžná konverzace, pozdravy, otázky (např. "Jak se máš?")
        3. NEVALIDNÍ TVRZENÍ - příliš vágní, nesmyslné nebo neobsahuje ověřitelné informace
        
        Pokud jde o ověřitelné tvrzení:
        - Vytvoř z něj ideální krátkou frázi pro vyhledávač
        - Nastav valid=true
        - Vygeneruj klíčová slova
        
        Pokud jde o konverzační text:
        - Nastav valid=true
        - Nastav search_query=""
        - Nastav keywords=[]
        - Nastav is_conversational=true
        
        Pokud jde o nevalidní tvrzení:
        - Nastav valid=false
        - Nastav search_query=""
        - Nastav keywords=[]

        Aktuální datum: {current_date}
        Text: "{user_input}"

        Odpověz přesně v tomto JSON formátu bez jakýchkoliv dalších komentářů:
        {{
        "search_query": "hledací fráze nebo prázdný řetězec",
        "valid": true nebo false,
        "is_conversational": true nebo false,
        "confidence": číslo od 0.0 do 1.0,
        "keywords": ["klíčové slovo 1", "klíčové slovo 2", "klíčové slovo 3", ...]
        }}
"""

    chat_response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt.strip(),
            },
        ]
    )

    content = chat_response.choices[0].message.content.strip()
    print("LLM odpověď:", content)

    try:
        # Extrakce části s JSON pomocí regulárního výrazu pro řešení případných problémů s formátováním
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            # Nahrazení JavaScript boolean hodnot Python boolean hodnotami
            json_str = json_str.replace('true', 'True').replace('false', 'False')
            # Použití eval pro zpracování Python boolean hodnot
            result = eval(f"dict({json_str})")
        else:
            raise ValueError("V odpovědi nebyl nalezen žádný JSON")
            
    except Exception as e:
        print("Chyba při parsování odpovědi:", e)
        result = {
            "search_query": "",
            "valid": False,
            "is_conversational": False,
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