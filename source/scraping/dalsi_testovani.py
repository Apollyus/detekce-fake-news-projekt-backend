from ufal.udpipe import Model, Pipeline, ProcessingError
import re

# Načteme model pro češtinu
print("Loading UDPipe model...")
model_path = "czech-pdt-ud-2.5-191206.udpipe"
model = Model.load(model_path)
if not model:
    print(f"ERROR: Cannot load UDPipe model from {model_path}")
    exit(1)
else:
    print("Model loaded successfully")

# Create pipeline with explicit parameters
pipeline = Pipeline(model, "tokenize", Pipeline.DEFAULT, Pipeline.DEFAULT, "conllu")
print("Pipeline created")

def generate_search_phrase(text: str):
    # Process with error handling
    error = ProcessingError()
    processed = pipeline.process(text, error)
    if error.occurred():
        print(f"Error processing text: {error.message}")
        return ""
    
    words = processed.split("\n")
    
    keywords = []
    stop_words = ['v', 've', 'byla', 'bylo', 'je', 'a', 'na', 'o', 'za', 'pro', 's']  # Seznam irrelevantních slov
    date = None  # Proměnná pro uložení datumu
    
    # Regulární výraz pro detekci datumu (např. březen 2025, 10. března 2025)
    date_pattern = r"\b(\d{1,2}\.?\s?[a-zA-Z]+(?:\s?\d{4})?)\b|\b(\d{4})\b"

    # Hledáme datum v textu
    date_match = re.search(date_pattern, text)
    if date_match:
        date = date_match.group(0)  # Získáme datum
    
    for word in words:
        if word:
            cols = word.split("\t")
            if len(cols) >= 4:
                lemma = cols[2]  # Základní tvar slova (lemma)
                pos = cols[3]  # Gramatická kategorie (NOUN, PROPN, VERB, ADJ)
                
                # Filtrace slov, která jsou irrelevantní pro vyhledávání
                if lemma.lower() not in stop_words and pos in ['NOUN', 'PROPN', 'VERB', 'ADJ']:
                    keywords.append(lemma)  # Přidáme lemmu (základní tvar)

    # Přidáme datum, pokud bylo nalezeno
    if date:
        keywords.append(date)
    
    return " ".join(keywords)