from generace_hledaci_vety_module import generate_search_phrase

# Test text - make sure this contains some Czech text
test_text = "Zemřela ceska zpevacka Anna SLovackova"

# Debug prints
print("Input text:", test_text)
result = generate_search_phrase(test_text)
print("Output keywords:", result)