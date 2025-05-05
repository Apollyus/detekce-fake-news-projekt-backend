from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lsa import LsaSummarizer
import nltk
import re

# Stažení požadovaných NLTK dat
try:
    nltk.download('punkt', quiet=True)
except Exception as e:
    print(f"Warning: Could not download NLTK data: {e}")

class SimpleTokenizer:
    """Jednoduchý tokenizátor, který funguje pro češtinu i angličtinu"""
    def __init__(self):
        self.sentence_pattern = re.compile(r'(?<=[.!?])\s+')
        
    def tokenize(self, text):
        # Jednoduché rozdělení vět na základě interpunkce
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def to_sentences(self, paragraph):
        """Vyžadováno knihovnou Sumy: Rozdělení odstavců na věty"""
        return self.tokenize(paragraph)
    
    def to_words(self, sentence):
        """Vyžadováno knihovnou Sumy: Rozdělení vět na slova"""
        return sentence.split()

def get_summary(text, sentence_count=3):
    """
    Vygeneruje souhrn poskytnutého textu.
    
    Argumenty:
        text (str): Text k sumarizaci
        sentence_count (int, volitelný): Počet vět v souhrnu. Výchozí hodnota je 3.
        
    Vrací:
        str: Sumarizovaný text
    """
    # Vytvoření parseru s vlastním tokenizátorem
    parser = PlaintextParser.from_string(text, SimpleTokenizer())
        
    # Použití LSA sumarizátoru
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentence_count)
    return " ".join(str(s) for s in summary)

# Příklad použití
'''if __name__ == "__main__":
    # Ukázkový text pro testování
    example_text = """
    Zatímco administrativaDonalda Trumpausiluje o snížení obchodního deficitu Spojených států v oblasti zboží, 
    řada sankcionovaných zemí – včetně Evropské unie – čelí opačné situaci v sektoru služeb, kde naopak vykazují 
    schodek ve prospěch USA. Amerika je jejich největším vývozcem na světě, přebytek v této oblasti činil v roce 
    2024 globálně zhruba 300 miliard dolarů, tedy necelých 7 bilionů korun.
    
    Velkou část tohoto exportu poskytují americké firmy digitálně. Vždy, když obyvatel některé z evropských zemí 
    vyhledá na Google otevírací dobu restaurace, na Instagram nahraje fotku či si zaplatí více úložného prostoru 
    na cloudech systému Microsoft, posílá peníze přímo, či nepřímo do USA.
    
    EU vyvezla v roce 2023 do USA služby v hodnotě 319 miliard eur a dovezla z USA služby v hodnotě 427 miliard eur. 
    Výsledkem byl pro EU deficit obchodu se službami v přepočtu 2,7 bilionu korun.
    """
    
    # Vygenerování souhrnu se 2 větami
    summary = get_summary(example_text, sentence_count=2)
    print("Summary:")
    print(summary)'''