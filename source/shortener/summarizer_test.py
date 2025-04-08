from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lsa import LsaSummarizer
import nltk
import re

# Download required NLTK data
try:
    nltk.download('punkt')
except Exception as e:
    print(f"Warning: Could not download NLTK data: {e}")

class SimpleTokenizer:
    """Simple tokenizer that works for both Czech and English"""
    def __init__(self):
        self.sentence_pattern = re.compile(r'(?<=[.!?])\s+')
        
    def tokenize(self, text):
        # Simple sentence splitting based on punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    # Add these required methods
    def to_sentences(self, paragraph):
        """Required by Sumy: Split paragraphs into sentences"""
        return self.tokenize(paragraph)
    
    def to_words(self, sentence):
        """Required by Sumy: Split sentences into words"""
        return sentence.split()

def summarize_text(text, sentence_count=3):
    # Create a parser with custom tokenizer
    parser = PlaintextParser.from_string(text, SimpleTokenizer())
        
    # Use LSA summarizer
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentence_count)
    return " ".join(str(s) for s in summary)

# Example usage
if __name__ == "__main__":
    text = """
        Zatímco administrativaDonalda Trumpausiluje o snížení obchodního deficitu Spojených států v oblasti zboží, řada sankcionovaných zemí – včetně Evropské unie – čelí opačné situaci v sektoru služeb, kde naopak vykazují schodek ve prospěch USA. Amerika je jejich největším vývozcem na světě, přebytek v této oblasti činil v roce 2024 globálně zhruba 300 miliard dolarů, tedy necelých 7 bilionů korun.
    """
    
    # Use a small test text first to verify it works
    print("Testing with small text first...")
    test_summary = summarize_text(text, sentence_count=1)
    print("Test summary:", test_summary)
    
    # If that works, try with the full text
    print("\nProcessing full article...")
    full_text = """Zatímco administrativaDonalda Trumpausiluje o snížení obchodního deficitu Spojených států v oblasti zboží, řada sankcionovaných zemí – včetně Evropské unie – čelí opačné situaci v sektoru služeb, kde naopak vykazují schodek ve prospěch USA. Amerika je jejich největším vývozcem na světě, přebytek v této oblasti činil v roce 2024 globálně zhruba 300 miliard dolarů, tedy necelých 7 bilionů korun.Velkou část tohoto exportu poskytují americké firmy digitálně. Vždy, když obyvatel některé z evropských zemí vyhledá na Google otevírací dobu restaurace, na Instagram nahraje fotku či si zaplatí více úložného prostoru na cloudech systému Microsoft, posílá peníze přímo, či nepřímo do USA.EU vyvezla v roce 2023 do USA služby v hodnotě 319 miliard eur a dovezla z USA služby v hodnotě 427 miliard eur. Výsledkem byl pro EU deficit obchodu se službami v přepočtu 2,7 bilionu korun."""
    
    # Try with a smaller subset first
    full_summary = summarize_text(full_text, sentence_count=2)
    print("Full summary:", full_summary)