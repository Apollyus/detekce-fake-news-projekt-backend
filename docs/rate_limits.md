# Rate Limity v API Bezfejku

API Bezfejku implementuje rate limiting pro ochranu před přetížením systému. Tato dokumentace popisuje nastavené limity pro vývojáře integrující naši API.

## Nastavené limity

### Per-IP limity
- **Limit:** 5 požadavků za minutu
- **Platí pro:** Každou unikátní IP adresu
- **Endpointy:** Všechny endpointy pro detekci fake news (`/api/v2/fake_news_check`)
- **Chybová zpráva:** "Překročen limit 5 požadavků za minutu. Zkuste to znovu později."
- **Status kód:** 429 Too Many Requests

### Globální limity
- **Limit:** 20 požadavků za minutu
- **Platí pro:** Všechny požadavky bez ohledu na IP adresu
- **Endpointy:** Všechny endpointy pro detekci fake news (`/api/v2/fake_news_check`)
- **Chybová zpráva:** "Aplikace je momentálně přetížena. Zkuste to znovu později."
- **Status kód:** 429 Too Many Requests

## Doporučení pro vývojáře

Pro správnou integraci s naším API doporučujeme:

1. **Implementovat exponenciální backoff** - Při obdržení 429 status kódu počkejte před opakováním požadavku a zvyšujte čas čekání s každým neúspěšným pokusem.

2. **Dávkování požadavků** - Pokud potřebujete zpracovat více textů, rozložte požadavky v čase.

3. **Cachování výsledků** - Ukládejte si výsledky pro často kontrolované texty.

4. **Monitorování zamítnutých požadavků** - Sledujte, zda vaše aplikace nedostává často 429 odpovědi, což by mohlo indikovat potřebu úpravy implementace.

## Příklad zpracování chyb rate limitingu v kódu

```python
import requests
import time

def check_fake_news(text, max_retries=3):
    base_url = "https://api.bezfejku.cz/api/v2/fake_news_check"
    retry_count = 0
    retry_delay = 1  # Počáteční prodleva 1 sekunda

    while retry_count < max_retries:
        response = requests.get(base_url, params={"prompt": text})
        
        if response.status_code == 200:
            return response.json()
        
        elif response.status_code == 429:
            print(f"Rate limit překročen: {response.json().get('error')}")
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponenciální zvýšení prodlevy
            retry_count += 1
        
        else:
            # Jiná chyba, kterou zpracujeme jinak
            response.raise_for_status()
    
    raise Exception("Překročen maximální počet pokusů kvůli rate limitingu")
```