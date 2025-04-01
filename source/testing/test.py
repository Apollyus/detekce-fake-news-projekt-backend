from transformers import pipeline, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("microsoft/deberta-v3-large", use_fast=False)
classifier = pipeline("text-classification", model="mrm8488/bert-mini-finetuned-fake-news")

# Testovací článek
text = "Scientists found life on Mars. They discovered a new speciesof aliens."

# Klasifikace textu
result = classifier(text)

print(result)
