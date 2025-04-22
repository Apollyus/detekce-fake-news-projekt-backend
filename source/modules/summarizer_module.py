from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lsa import LsaSummarizer
import nltk
import re

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
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
    
    def to_sentences(self, paragraph):
        """Required by Sumy: Split paragraphs into sentences"""
        return self.tokenize(paragraph)
    
    def to_words(self, sentence):
        """Required by Sumy: Split sentences into words"""
        return sentence.split()

def get_summary(text, sentence_count=3):
    """
    Generate a summary of the provided text.
    
    Args:
        text (str): The text to summarize
        sentence_count (int, optional): Number of sentences in the summary. Default is 3.
        
    Returns:
        str: The summarized text
    """
    # Create a parser with custom tokenizer
    parser = PlaintextParser.from_string(text, SimpleTokenizer())
        
    # Use LSA summarizer
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentence_count)
    return " ".join(str(s) for s in summary)

# Example usage
'''if __name__ == "__main__":
    # Example text for testing
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
    
    # Generate summary with 2 sentences
    summary = get_summary(example_text, sentence_count=2)
    print("Summary:")
    print(summary)'''