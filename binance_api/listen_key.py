import requests
import threading
import time


def refresh_listen_key(api_key, listen_key):
    
    base_url = 'https://testnet.binancefuture.com'
    path = f'/fapi/v1/listenKey?listenKey={listen_key}'
    url = base_url + path

    headers = {'X-MBX-APIKEY': api_key}
    response = requests.put(url, headers=headers)
    response.raise_for_status()

    # print(f"Listen key refreshed, response status code: {response.status_code}")
    # print(f"Current listen key (still valid): {listen_key}")


def get_listen_key(api_key):
    base_url = 'https://testnet.binancefuture.com'
    path = '/fapi/v1/listenKey'
    url = base_url + path

    headers = {'X-MBX-APIKEY': api_key}
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    listen_key = data.get('listenKey')
    
    return listen_key


def keep_alive(api_key, listen_key, interval=1800):
    while True:
        try:
            refresh_listen_key(api_key, listen_key)
            # print("Successfully refreshed the listen key.")
        except Exception as e:
            # print(f"Failed to refresh listen key: {e}")
            listen_key = get_listen_key(api_key)  # Get a new listen key
            # Logic to restart WebSocket connection with new listen key
        time.sleep(interval)
