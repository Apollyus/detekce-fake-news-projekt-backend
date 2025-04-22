import re
from datetime import datetime
from mistralai import Mistral
from source.modules.config import config  # Import the config instance, not the module

api_key = config.MISTRAL_API_KEY  # Use the API key from the config
model = "mistral-small-latest"  # Changed to a valid model name

client = Mistral(api_key=api_key)

def check_and_generate_search_phrase(user_input: str):
    # Get current date in readable format
    current_date = datetime.now().strftime("%d. %m. %Y")
    
    prompt = f"""
Zhodnoť následující tvrzení a rozhodni, zda dává smysl a je dostatečně konkrétní, aby se podle něj dalo hledat na internetu.
Pokud ano, vytvoř z něj ideální krátkou frázi, která by se dala použít ve vyhledávači (např. Google).
Pokud tvrzení nedává smysl, je příliš vágní nebo neobsahuje ověřitelné informace, napiš "INVALID".

Aktuální datum: {current_date}
Tvrzení: "{user_input}"

Při generování hledací fráze:
1. Zohledni aktuální datum - zejména u zpráv, které se týkají aktuálního dění
2. Vynech pomocná slova jako "byl", "bylo", "je" apod., pokud nejsou klíčové pro význam
3. Zaměř se na klíčová fakta a konkrétní informace z tvrzení
4. Optimalizuj frázi pro vyhledávače - používej relevantní klíčová slova

Navíc vytvoř seznam 3-5 klíčových slov nebo krátkých frází, které nejlépe vystihují podstatu tvrzení.
Tyto klíčová slova budou použita pro filtrování relevantních zpravodajských článků k ověření.
Klíčová slova by měla:
1. Obsahovat podstatná jména a vlastní jména z tvrzení
2. Zachytit hlavní aktéry, místa, události nebo témata
3. Být seřazena podle důležitosti (nejdůležitější první)
4. Být dostatečně specifická, ale ne příliš dlouhá
5. Pro každé klíčové slovo uveď 1-3 různé gramatické tvary (např. jednotné/množné číslo, různé pády), pokud je to možné
6. Pro jména osob zahrň jak celé jméno, tak i samostatně příjmení
7. Pro názvy událostí nebo organizací uveď jak plný název, tak i běžně používané zkratky

Odpověz přesně v tomto JSON formátu bez jakýchkoliv dalších komentářů:
{{
  "search_query": "hledací fráze nebo prázdný řetězec",
  "valid": true nebo false,
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
        # Extract the JSON part using regex to handle potential formatting issues
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            # Replace JavaScript booleans with Python booleans
            json_str = json_str.replace('true', 'True').replace('false', 'False')
            # Use eval to handle the Python boolean values
            result = eval(f"dict({json_str})")
        else:
            raise ValueError("No JSON found in response")
            
    except Exception as e:
        print("Chyba při parsování odpovědi:", e)
        result = {
            "search_query": "",
            "valid": False,
            "confidence": 0.0,
            "keywords": []
        }

    return result


# 💡 TEST
if __name__ == "__main__":
    user_text = "Zemřela česká zpěvačka Anna K."
    result = check_and_generate_search_phrase(user_text)
    print("Výsledek:", result)