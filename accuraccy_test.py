import sys
import os
import requests # Import the requests library
import json     # Import json for handling potential errors

# ... (imports and other setup remain the same) ...

# --- Test Data ---
# Adjusted expected_verdict to use strings "TRUE"/"FALSE"
test_data = [
    {
        "text": "Dne 28. dubna 2025 došlo k masivnímu výpadku napájení na Pyrenejském poloostrově, který postihl Španělsko i Portugalsko.",
        "expected_status": "success",
        "expected_verdict": "TRUE",
        "is_gibberish": False
    },
    {
        "text": "27. dubna 2025 Aaron Gordon zaznamenal vítězný dunk v poslední vteřině, když Denver Nuggets porazili Los Angeles Clippers 101–99 a vyrovnali sérii na 2–2.",
        "expected_status": "success",
        "expected_verdict": "TRUE",
        "is_gibberish": False
    },
    {
        "text": "Němečtí konzervativci pod vedením Friedricha Merze uzavřeli 9. dubna 2025 koaliční dohodu se SPD.",
        "expected_status": "success",
        "expected_verdict": "TRUE",
        "is_gibberish": False
    },
    {
        "text": "Americký Nejvyšší soud 29. dubna 2025 projednává spor o pravomoci prezidenta Trumpa odvolávat předsedu Federálního rezervního systému.",
        "expected_status": "success",
        "expected_verdict": "TRUE",
        "is_gibberish": False
    },
    {
        "text": "Bílý dům 7. dubna 2025 nařídil federálním agenturám jmenovat hlavní oficiály pro umělou inteligenci a vytvořit strategické rámce pro AI.",
        "expected_status": "success",
        "expected_verdict": "TRUE",
        "is_gibberish": False
    },
    {
        "text": "Index spotřebitelské důvěry GfK v Německu se v květnu 2025 zlepšil na -20,6 bodu z -24,3 bodu.",
        "expected_status": "success",
        "expected_verdict": "TRUE",
        "is_gibberish": False
    },
    {
        "text": "Evropská komise 1. dubna 2025 navrhla prodloužení plnění emisních cílů CO₂ pro automobilový průmysl na období 2025–2027.",
        "expected_status": "success",
        "expected_verdict": "TRUE",
        "is_gibberish": False
    },
    {
        "text": "Finsko 29. dubna 2025 podpořilo návrh EU snížit čisté skleníkové emise o 90 % do roku 2040.",
        "expected_status": "success",
        "expected_verdict": "TRUE",
        "is_gibberish": False
    },
    {
        "text": "Biden během summitu NATO v dubnu 2025 zrušil všechny sankce proti Rusku.",
        "expected_status": "success",
        "expected_verdict": "FALSE",
        "is_gibberish": False
    },
    {
        "text": "Banány obsahují radioaktivní látky.",
        "expected_status": "success",
        "expected_verdict": "TRUE", # Changed to string "TRUE"
        "is_gibberish": False
    },
    {
        "text": "Země je placatá a důkazy jsou skryté.",
        "expected_status": "success",
        "expected_verdict": "FALSE", # Changed to string "FALSE"
        "is_gibberish": False
    },
    {
        "text": "V roce 2022 začala válka na Ukrajině kvůli rozšíření NATO.",
        "expected_status": "success",
        "expected_verdict": "FALSE", # Changed to string "FALSE"
        "is_gibberish": False
    },
    {
        "text": "Zelený čaj zvyšuje inteligenci o 20 bodů IQ.",
        "expected_status": "success",
        "expected_verdict": "FALSE", # Changed to string "FALSE"
        "is_gibberish": False
    },
    {
        "text": "a",
        "expected_status": "error",
        "expected_verdict": None,
        "is_gibberish": True
    },
    {
        "text": "Mars má dvě přirozené družice: Phobos a Deimos.",
        "expected_status": "success",
        "expected_verdict": "TRUE", # Changed to string "TRUE"
        "is_gibberish": False
    }
]


# --- API Configuration ---
# !!! IMPORTANT: Update this URL to your actual FastAPI endpoint !!!
API_ENDPOINT = "http://localhost:8000/api/v2/fake_news_check/" # Adjust path as needed

# --- Test Execution ---
results = []
correct_predictions = 0
incorrect_predictions = 0
processing_errors = 0

print(f"Starting accuracy test with {len(test_data)} cases against API: {API_ENDPOINT}\n")

for i, test_case in enumerate(test_data):
    print(f"--- Test Case {i+1} ---")
    print(f"Input Text: {test_case['text']}")
    print(f"Expected Status: {test_case['expected_status']}")
    if test_case['expected_status'] == 'success':
        # Print expected string verdict
        print(f"Expected Verdict: {test_case['expected_verdict']}")

    try:
        api_url = API_ENDPOINT.rstrip('/') # Ensure no trailing slash for query params
        response = requests.get(api_url, params={"prompt": test_case["text"]}, timeout=60)
        response.raise_for_status()

        result = response.json()

        print(f"Actual Status: {result.get('status')}")
        actual_verdict = None # Initialize actual_verdict

        # !!! IMPORTANT: Verify this access pattern matches your API response !!!
        # Assuming the string verdict ("TRUE"/"FALSE") is directly under the 'result' key
        if result.get('status') == 'success' and 'result' in result:
             # Check if the result itself is the string OR if it's nested further
             if isinstance(result['result'], str) and result['result'] in ["TRUE", "FALSE"]:
                 actual_verdict = result['result']
             # Example if nested: check if result['result'] is a dict and contains the string
             elif isinstance(result.get('result'), dict) and 'verdict' in result['result'] and isinstance(result['result']['verdict'], str) and result['result']['verdict'] in ["TRUE", "FALSE"]:
                 actual_verdict = result['result']['verdict'] # Adjust 'verdict' key if needed
             else:
                 print(f"Warning: Could not extract string verdict ('TRUE'/'FALSE') from result: {result.get('result', 'N/A')}")
                 actual_verdict = 'N/A' # Mark as not available if structure is unexpected

             print(f"Actual Verdict: {actual_verdict}")

        elif result.get('status') == 'error':
            print(f"Actual Message: {result.get('message')}")

        is_correct = False
        # Check if the status matches
        if result.get('status') == test_case["expected_status"]:
            if test_case["expected_status"] == "success":
                # If status is success, check the STRING verdict
                # Compare the extracted actual_verdict string with the expected string
                if actual_verdict == test_case["expected_verdict"]:
                    is_correct = True
            else: # expected_status is 'error'
                # If status is error and was expected, it's correct
                is_correct = True

        if is_correct:
            print("Result: CORRECT")
            correct_predictions += 1
        else:
            print("Result: INCORRECT")
            incorrect_predictions += 1
        results.append({"case": test_case, "result": result, "correct": is_correct})

    except requests.exceptions.RequestException as e:
        print(f"Result: API REQUEST ERROR - {e}")
        processing_errors += 1
        results.append({"case": test_case, "result": f"Request Error: {e}", "correct": False})
    except json.JSONDecodeError as e:
         print(f"Result: JSON DECODE ERROR - Could not parse API response: {e}")
         processing_errors += 1
         results.append({"case": test_case, "result": f"JSON Error: {e}", "correct": False})
    except Exception as e:
        print(f"Result: UNEXPECTED PROCESSING ERROR - {e}")
        processing_errors += 1
        results.append({"case": test_case, "result": f"Error: {e}", "correct": False})
    print("-" * 20)


# --- Summary ---
# ... (summary code remains the same) ...
print("\n--- Test Summary ---")
total_processed = len(test_data) - processing_errors
print(f"Total Test Cases: {len(test_data)}")
print(f"Successfully Processed: {total_processed}")
print(f"Correct Predictions: {correct_predictions}")
print(f"Incorrect Predictions: {incorrect_predictions}")
print(f"Processing Errors (API/JSON/Other): {processing_errors}")

if total_processed > 0:
    accuracy = (correct_predictions / total_processed) * 100
    print(f"\nAccuracy (Correct / Processed): {accuracy:.2f}%")
else:
    print("\nAccuracy: N/A (No cases were successfully processed or all resulted in errors)")

# Optional: Print details of incorrect predictions
print("\n--- Incorrect Predictions Details ---")
for res in results:
    if not res["correct"] and isinstance(res["result"], dict): # Check if result is a dict (API call succeeded)
        print(f"Input: {res['case']['text']}")
        print(f"Expected: Status={res['case']['expected_status']}, Verdict={res['case']['expected_verdict']}")
        actual_status = res['result'].get('status', 'N/A')
        actual_verdict_display = 'N/A' # For display purposes

        # Extract actual verdict string for display, handling potential nesting and non-string types
        if actual_status == 'success' and 'result' in res['result']:
             if isinstance(res['result']['result'], str) and res['result']['result'] in ["TRUE", "FALSE"]:
                 actual_verdict_display = res['result']['result']
             elif isinstance(res['result'].get('result'), dict) and 'verdict' in res['result']['result'] and isinstance(res['result']['result']['verdict'], str) and res['result']['result']['verdict'] in ["TRUE", "FALSE"]:
                 actual_verdict_display = res['result']['result']['verdict'] # Adjust 'verdict' key if needed
             else:
                 # Display the raw result if it's not the expected string structure
                 actual_verdict_display = f"(Unexpected format: {res['result'].get('result', 'N/A')})"

        print(f"Actual:   Status={actual_status}, Verdict={actual_verdict_display}")
        print(f"Message:  {res['result'].get('message', 'N/A')}")
        print("-" * 10)
    elif not res["correct"] and isinstance(res["result"], str): # Print API/JSON/Other errors
         print(f"Input: {res['case']['text']}")
         print(f"Expected: Status={res['case']['expected_status']}, Verdict={res['case']['expected_verdict']}")
         print(f"Actual:   {res['result']}") # Contains the error message
         print("-" * 10)