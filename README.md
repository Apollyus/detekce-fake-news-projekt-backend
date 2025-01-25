# Jak začít s touto aplikací

Tento návod vám pomůže začít s aplikací pro detekci falešných zpráv. Postupujte podle následujících kroků:

# Ukoly pro backend (Arsen a Matěj)

## Popis
Vaším úkolem je vytvořit nový endpoint v aplikaci, který bude generovat data fiktivního uživatele a vracet je ve formátu JSON. Pro generování dat použijte knihovnu `Faker`. Úkoly dělejte na Vaší příslušné větvi (branch) s vaším jménem. Co to je a jak se na to přepnout najdete v té příručce. Nezapomňte hlavně potom změny "pushnout" na github ať je vidí i ostatní.

## Požadavky
- Endpoint by měl být dostupný na adrese `/generate-user`.
- Data fiktivního uživatele by měla zahrnovat:
  - **Jméno**
  - **Adresa**
  - **Email**
  - **Uživatelské jméno**
  - **Datum narození**
- Data by měla být vrácena ve formátu JSON.

### Instalace knihovny Faker
```bash
pip install faker
```

## Očekávaný výstup

Příklad JSON odpovědi:
```json
{
  "name": "Jan Novák",
  "address": "123 Hlavní, Praha, Česko",
  "email": "jan.novak@example.com",
  "username": "jan.novak92",
  "birthdate": "1992-05-14"
}
```

## Shrnutí
Tento úkol vám pomůže procvičit si:
- Práci s endpointy ve FastAPI.
- Použití knihovny Faker pro generování testovacích dat.
- Testování API pomocí prohlížeče nebo Postmanu.

# Začínáme
## Požadavky

1. **Nainstalujte Python**: Stáhněte a nainstalujte Python z [oficiálních stránek](https://www.python.org/downloads/). Ujistěte se, že během instalace zaškrtnete možnost "Add Python to PATH".

2. **Nainstalujte Git**: Stáhněte a nainstalujte Git z [oficiálních stránek](https://git-scm.com/downloads).

## Stažení projektu

1. Otevřete příkazový řádek (Command Prompt) nebo PowerShell.
2. Naklonujte repozitář pomocí následujícího příkazu:
    ```sh
    git clone https://github.com/vase-uzivatelske-jmeno/detekce-fake-news-projekt.git
    ```
3. Přejděte do složky projektu:
    ```sh
    cd detekce-fake-news-projekt
    ```

## Instalace závislostí

1. Vytvořte a aktivujte virtuální prostředí:
    ```sh
    python -m venv venv
    .\venv\Scripts\activate
    ```
2. Nainstalujte potřebné balíčky:
    ```sh
    pip install -r requirements.txt
    ```

## Spuštění aplikace

1. Spusťte aplikaci pomocí následujícího příkazu:
    ```sh
    python main.py
    ```