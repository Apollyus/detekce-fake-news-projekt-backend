"""
Test soubor pro text_summarizer_module
"""

import sys
import os

# Přidání parent directory do sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from source.modules.text_summarizer_module import summarize_text, summarize_text_simple

def test_summarizer():
    """Test funkce sumarizace"""
    
    # Testovací text
    test_text = """
    Klimatické změny jsou jedním z nejzávažnějších problémů současnosti. 
    Podle vědeckých studií se globální teplota zvyšuje rychleji než kdykoli předtím v historii lidstva.
    Hlavní příčinou je zvýšení koncentrace skleníkových plynů v atmosféře, zejména oxidu uhličitého.
    Tento trend má závažné důsledky pro životní prostředí, včetně tání ledovců, zvyšování hladiny moří,
    a častějších extrémních povětrnostních jevů. Mnoho vědců se shoduje na tom, že je nutné okamžitě
    jednat a snížit emise skleníkových plynů, aby se zabránilo katastrofickým důsledkům.
    """
    
    original_claim = "klimatické změny jsou největší hrozbou pro lidstvo"
    
    try:
        # Test s původním tvrzením
        result1 = summarize_text(test_text, original_claim)
        print("Sumarizace s původním tvrzením:")
        print(result1)
        print("\n" + "="*50 + "\n")
        
        # Test bez původního tvrzení
        result2 = summarize_text_simple(test_text)
        print("Jednoduchá sumarizace:")
        print(result2)
        
    except Exception as e:
        print(f"Chyba při testování: {e}")

if __name__ == "__main__":
    test_summarizer()
