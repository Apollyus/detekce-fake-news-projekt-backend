import re
from ufal.udpipe import Model, Pipeline

# Načti UDPipe model jen jednou
MODEL_PATH = "/home/vojtech/Documents/aaa_programovani/detekce-fake-news-projekt-backend/source/czech-pdt-ud-2.5-191206.udpipe"
model = Model.load(MODEL_PATH)
pipeline = Pipeline(model, "tokenize", Pipeline.DEFAULT, Pipeline.DEFAULT, "conllu")


def count_named_entities(text):
    processed = pipeline.process(text)
    lines = processed.split('\n')
    entity_count = 0
    for line in lines:
        if line and not line.startswith("#"):
            cols = line.split('\t')
            if len(cols) > 3:
                upos = cols[3]
                if upos in ['PROPN', 'NOUN']:  # Proper nouns or named entities
                    entity_count += 1
    return entity_count


def is_vague(text: str, min_chars=50, min_entities=1):
    reasons = []
    text_clean = text.strip().lower()
    
    # 1. Check délky
    if len(text_clean) < min_chars:
        reasons.append("short_input")
    
    # 2. Vágní fráze
    vague_patterns = [
        r"^je to pravda[\?\.]*$",
        r"^co se stalo[\?\.]*$",
        r"^ověř to[\?\.]*$",
        r"^ověř[\?\.]*$",
        r"^ověř prosím[\?\.]*$",
        r"^je to fakt[\?\.]*$",
        r"^je to pravda nebo ne[\?\.]*$",
        r"^je to tak[\?\.]*$",
    ]
    
    for pattern in vague_patterns:
        if re.match(pattern, text_clean):
            reasons.append("generic_question")
            break

    # 3. Named entity check
    entity_count = count_named_entities(text)
    if entity_count < min_entities:
        reasons.append("not_enough_entities")
    
    return {
        "is_vague": len(reasons) > 0,
        "reasons": reasons,
        "entity_count": entity_count,
        "length": len(text_clean)
    }

print(is_vague("ringo uoungr eoge oeon ouen oun uneon", min_chars=10, min_entities=1))