# Jak začít s touto aplikací

Tento návod vám pomůže začít s aplikací pro detekci falešných zpráv. Postupujte podle následujících kroků:

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