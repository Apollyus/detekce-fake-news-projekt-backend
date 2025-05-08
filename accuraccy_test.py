import sys
import os
import requests # Import the requests library
import json     # Import json for handling potential errors

# ... (imports and other setup remain the same) ...

# --- Test Data ---
# Adjusted expected_verdict to use strings "TRUE"/"FALSE"
test_data = [
    {
        "text": "Prezident Petr Pavel se 8. května 2025 zúčastnil oslav Dne vítězství u Národního památníku na Vítkově. [17]",
        "expected_status": "success",
        "expected_verdict": "TRUE",
        "is_gibberish": False
    },
    {
        "text": "Česká národní banka na svém zasedání 7. května 2025 snížila základní úrokovou sazbu na 3,5 %. [15]",
        "expected_status": "success",
        "expected_verdict": "TRUE",
        "is_gibberish": False
    },
    {
        "text": "Podle květnové prognózy ČNB z roku 2025 se očekává, že celková inflace v České republice v květnu dosáhne 2,3 %. [2]",
        "expected_status": "success",
        "expected_verdict": "TRUE",
        "is_gibberish": False
    },
    {
        "text": "Dne 28. dubna 2025 došlo k masivnímu výpadku dodávek elektřiny, který postihl celé Španělsko a Portugalsko. [7]",
        "expected_status": "success",
        "expected_verdict": "TRUE",
        "is_gibberish": False
    },
    {
        "text": "Organizace Post Bellum odhalila 7. května 2025 venkovní expozici připomínající existenci ženského koncentračního tábora Svatava. [16]",
        "expected_status": "success",
        "expected_verdict": "TRUE",
        "is_gibberish": False
    },
    {
        "text": "Ruský prezident Vladimir Putin navštívil Prahu 8. května 2025, aby se zúčastnil oslav 80. výročí konce druhé světové války. [6]",
        "expected_status": "success",
        "expected_verdict": "FALSE",
        "is_gibberish": False
    },
    {
        "text": "Evropská unie na summitu konaném 5. května 2025 schválila s okamžitou platností úplný zákaz prodeje nových automobilů se spalovacími motory. [8]",
        "expected_status": "success",
        "expected_verdict": "FALSE",
        "is_gibberish": False
    },
    {
        "text": "Vědci z Massachusettského technologického institutu (MIT) oznámili 7. května 2025 objev univerzálního léku na všechny typy rakoviny. [9]",
        "expected_status": "success",
        "expected_verdict": "FALSE",
        "is_gibberish": False
    },
    {
        "text": "Podle studie zveřejněné začátkem května 2025 pravidelná konzumace hořké čokolády prokazatelně prodlužuje průměrnou délku života o pět let. [10]",
        "expected_status": "success",
        "expected_verdict": "FALSE",
        "is_gibberish": False
    },
    {
        "text": "Dne 1. května 2025 bylo definitivně potvrzeno, že na povrchu Marsu existují rozsáhlé oblasti s tekoucí vodou a jednoduchými formami mikrobiálního života. [11]",
        "expected_status": "success",
        "expected_verdict": "FALSE",
        "is_gibberish": False
    },
    {
        "text": "Vláda České republiky na svém zasedání 7. května 2025 zamítla zprávu o adaptaci na změnu klimatu pro rok 2025. [12]", # Opak pravdivé zprávy
        "expected_status": "success",
        "expected_verdict": "FALSE",
        "is_gibberish": False
    },
    {
        "text": "Ve Vatikánu dne 7. května 2025 začalo konkláve pro volbu nového papeže, přičemž první kolo hlasování bylo neúspěšné. [14]",
        "expected_status": "success",
        "expected_verdict": "TRUE",
        "is_gibberish": False
    },
    {
        "text": "Duben 2025 byl nejméně tragickým měsícem na českých silnicích za poslední dekádu, s pouze 5 oběťmi dopravních nehod. [18]", # Opak pravdivé zprávy
        "expected_status": "success",
        "expected_verdict": "FALSE",
        "is_gibberish": False
    },
    {
        "text": "Francouzská vláda přislíbila finanční pomoc ve výši 3 miliard eur na obnovu karibského ostrova Martinik po nedávném hurikánu. [19]", # Změna ostrova oproti pravdivé zprávě
        "expected_status": "success",
        "expected_verdict": "FALSE",
        "is_gibberish": False
    },
    {
        "text": "Experimentální lék úspěšně obnovil sluch u laboratorních myší díky blokaci proteinu Prox1, oznámili vědci 7. května 2025. [20]", # Změna smyslu oproti pravdivé zprávě (zrak vs sluch)
        "expected_status": "success",
        "expected_verdict": "FALSE",
        "is_gibberish": False
    },
    {
        "text": "Papež František, který zemřel v dubnu 2025, osobně zahájil charitativní fotbalový turnaj ve Vatikánu dne 5. května 2025. [22, 24]",
        "expected_status": "success",
        "expected_verdict": "FALSE",
        "is_gibberish": False
    },
    {
        "text": "Mistrovství světa v ledním hokeji 2025, pořádané Švédskem a Dánskem, bylo zahájeno již 1. května 2025.", # Chybný datum zahájení
        "expected_status": "success",
        "expected_verdict": "FALSE",
        "is_gibberish": False
    },
    {
        "text": "Renáta Kellnerová s rodinou byla v květnu 2025 sesazena z pozice nejbohatšího člověka v Česku Danielem Křetínským.", # Opak pravdivé zprávy
        "expected_status": "success",
        "expected_verdict": "FALSE",
        "is_gibberish": False
    },
    {
        "text": "Služba pro internetovou telefonii Skype ukončila svůj provoz celosvětově 5. května 2025. [27]",
        "expected_status": "success",
        "expected_verdict": "TRUE",
        "is_gibberish": False
    },
    {
        "text": "Čínský prezident Si Ťin-pching dne 8. května 2025 jednal v Budapešti s maďarskými představiteli.",
        "expected_status": "success",
        "expected_verdict": "TRUE", # Na základě dřívějších informací o jeho návštěvě
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
             if isinstance(result['result'], str):
                 actual_verdict = result['result']
             # Example if nested: check if result['result'] is a dict and contains the string
             elif isinstance(result.get('result'), dict) and 'verdict' in result['result']:
                 actual_verdict = result['result']['verdict']
             else:
                 print(f"Warning: Could not extract verdict from result: {result.get('result', 'N/A')}")
                 actual_verdict = 'N/A'

             print(f"Actual Verdict: {actual_verdict}")

        elif result.get('status') == 'error':
            print(f"Actual Message: {result.get('message')}")

        is_correct = False
        # Check if the status matches
        if result.get('status') == test_case["expected_status"]:
            if test_case["expected_status"] == "success":
                # If status is success, check the verdict
                # Compare the extracted actual_verdict with the expected verdict
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
             if isinstance(res['result']['result'], str):
                 actual_verdict_display = res['result']['result']
             elif isinstance(res['result'].get('result'), dict) and 'verdict' in res['result']['result']:
                 actual_verdict_display = res['result']['result']['verdict']
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