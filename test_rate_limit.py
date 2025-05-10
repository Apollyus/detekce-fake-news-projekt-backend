import requests
import time
import threading
import concurrent.futures

base_url = "http://localhost:8000/api/v2/fake_news_check"
params = {"prompt": "Test news article"}

def test_per_ip_limit():
    print("Testing per-IP rate limit (5 requests/minute)...")
    for i in range(7):  # Try 7 requests (2 more than the limit)
        response = requests.get(base_url, params=params)
        print(f"Request {i+1}: Status code: {response.status_code}")
        if response.status_code == 429:
            print(f"Rate limit message: {response.text}")
        time.sleep(0.5)  # Small delay between requests

    # Add a delay and then try again to verify the rate limit resets
    print("\nWaiting 60 seconds for rate limit to reset...")
    time.sleep(60)
    print("Testing after rate limit reset...")
    response = requests.get(base_url, params=params)
    print(f"Request after waiting: Status code: {response.status_code}")

def send_request(thread_id, request_num):
    """Funkce pro odeslání jednoho požadavku s unikátním textem"""
    test_params = {"prompt": f"Test article from thread {thread_id}, request {request_num}"}
    response = requests.get(base_url, params=test_params)
    return response.status_code, response.text if response.status_code == 429 else ""

def test_global_limit():
    print("\n\nTesting global rate limit (20 requests/minute)...")
    results = []
    
    # Použití ThreadPoolExecutor pro paralelní odeslání požadavků
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Vytvoření 25 požadavků (přesahuje globální limit 20/minutu)
        futures = []
        for i in range(25):
            futures.append(executor.submit(send_request, i % 10, i))
            
        # Sbírání výsledků
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            status_code, message = future.result()
            results.append(status_code)
            print(f"Global test - Request {i+1}: Status code: {status_code}")
            if status_code == 429 and "přetížena" in message:
                print(f"Global limit message: {message}")
    
    # Ověření, že globální limit byl skutečně dosažen
    if 429 in results:
        print("\nGlobální limit byl úspěšně detekován! ✅")
        print(f"Počet úspěšných požadavků: {results.count(200)}")
        print(f"Počet požadavků s překročeným limitem: {results.count(429)}")
    else:
        print("\nGlobální limit nebyl dosažen nebo detekován ❌")

# Spustit test per-IP limitu
print("=== TEST PER-IP LIMITU ===")
test_per_ip_limit()

# Spustit test globálního limitu
print("\n=== TEST GLOBÁLNÍHO LIMITU ===")
test_global_limit()