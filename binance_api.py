import os
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import logging


class BinanceAPI:
    def __init__(self, api_key, api_secret):
        self.client = Client(api_key, api_secret, testnet=True)
        self.logger = self._setup_logger()

    def _setup_logger(self):
        logger = logging.getLogger('BinanceFuturesTestnet')
        logger.setLevel(logging.INFO)
        logger.propagate = False  # Disable propagation to the parent logger
        if not logger.handlers:  # Avoid adding multiple handlers
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger


    def get_balance(self):
        try:
            balance = self.client.futures_account_balance()
            return balance
        except BinanceAPIException as e:
            self.logger.error(f"Binance API Exception: {e}")
        except BinanceOrderException as e:
            self.logger.error(f"Binance Order Exception: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")

    def get_open_orders(self, symbol):
        try:
            open_orders = self.client.futures_get_open_orders(symbol=symbol)
            self.logger.info("Fetched open orders successfully.")
            return open_orders
        except BinanceAPIException as e:
            self.logger.error(f"Binance API Exception: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")

    def create_order(self, symbol, side, type, quantity, price=None, timeInForce='GTC'):
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': type,
                'quantity': quantity,
                'timeInForce': timeInForce
            }
            if price:
                params['price'] = price
            order = self.client.futures_create_order(**params)
            self.logger.info("Order created successfully.")
            return order
        except BinanceAPIException as e:
            self.logger.error(f"Binance API Exception: {e}")
        except BinanceOrderException as e:
            self.logger.error(f"Binance Order Exception: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")

    def cancel_order(self, symbol, order_id):
        try:
            result = self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
            self.logger.info("Order cancelled successfully.")
            return result
        except BinanceAPIException as e:
            self.logger.error(f"Binance API Exception: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")

    def get_all_orders(self, symbol):
        try:
            orders = self.client.futures_get_all_orders(symbol=symbol)
            self.logger.info("Fetched all orders successfully.")
            return orders
        except BinanceAPIException as e:
            self.logger.error(f"Binance API Exception: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")


load_dotenv()
api_key = os.getenv('API_KEY_TEST')
api_secret = os.getenv('API_SECRET_TEST')

binance_api = BinanceAPI(api_key, api_secret)

