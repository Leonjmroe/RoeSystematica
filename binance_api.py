from dotenv import load_dotenv
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException


class BinanceAPI:
    def __init__(self, api_key, api_secret):
        self.client = Client(api_key, api_secret, testnet=True)  # Ensure to use the testnet parameter

    def get_account_info(self):
        try:
            return self.client.get_account()
        except BinanceAPIException as e:
            print(f"Binance API Exception occurred: {e.status_code} - {e.message}")
        except BinanceRequestException as e:
            print(f"Binance Request Exception occurred: {e.status_code} - {e.message}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def get_asset_balance(self, asset):
        try:
            return self.client.get_asset_balance(asset=asset)
        except BinanceAPIException as e:
            print(f"Binance API Exception occurred: {e.status_code} - {e.message}")
        except BinanceRequestException as e:
            print(f"Binance Request Exception occurred: {e.status_code} - {e.message}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def get_all_tickers(self):
        try:
            return self.client.get_all_tickers()
        except BinanceAPIException as e:
            print(f"Binance API Exception occurred: {e.status_code} - {e.message}")
        except BinanceRequestException as e:
            print(f"Binance Request Exception occurred: {e.status_code} - {e.message}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


load_dotenv()
api_key = os.getenv('API_KEY_TEST')
api_secret = os.getenv('API_SECRET_TEST')
binance = BinanceAPI(api_key, api_secret)

# Get account information
account_info = binance.get_account_info()
if account_info:
    print(account_info)

# Get balance for a specific asset
balance = binance.get_asset_balance(asset='BTC')
if balance:
    print(balance)

# Get all tickers
tickers = binance.get_all_tickers()
if tickers:
    print(tickers[0])

