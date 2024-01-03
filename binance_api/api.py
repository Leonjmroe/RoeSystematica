from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import logging
import os
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BinanceAPI:
    def __init__(self):
        self.client = Client(os.getenv('API_KEY_TEST'), os.getenv('API_SECRET_TEST'), testnet=True)
        self.logger = self._setup_logger()
        self.callback = None

    def _setup_logger(self):
        logger = logging.getLogger('BinanceFuturesTestnet')
        logger.setLevel(logging.ERROR)
        logger.propagate = False 
        if not logger.handlers:  
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
            self.callback(order)
            self.logger.info("Order created successfully.")
            return order
        except BinanceAPIException as e:
            self.logger.error(f"Binance API Exception: {e}")
            pass
        except BinanceOrderException as e:
            self.logger.error(f"Binance Order Exception: {e}")
            pass
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")

    def create_stop_market_order(self, symbol, side, quantity, stop_price):
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'STOP_MARKET',
                'quantity': quantity,
                'stopPrice': stop_price
            }
            order = self.client.create_order(**params)
            return order
        except BinanceAPIException as e:
            print(f"Binance API Exception: {e}")
        except BinanceOrderException as e:
            print(f"Binance Order Exception: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def cancel_order(self, symbol, order_id):
    # try:
        result = self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
        # print
        # self.logger.info("Order cancelled successfully.")
        return result
    # except BinanceAPIException as e:
    #     self.logger.error(f"Binance API Exception: {e}")
    # except Exception as e:
    #     self.logger.error(f"An unexpected error occurred: {e}")

    def get_all_orders(self, symbol):
        try:
            orders = self.client.futures_get_all_orders(symbol=symbol)
            self.logger.info("Fetched all orders successfully.")
            return orders
        except BinanceAPIException as e:
            self.logger.error(f"Binance API Exception: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")

    def get_last_bid_ask(self, symbol):
        try:
            order_book = self.client.get_order_book(symbol=symbol, limit=5)  # limit=5 for the top 5 bids/asks
            best_bid = order_book['bids'][0][0]  # First bid's price
            best_ask = order_book['asks'][0][0]  # First ask's price
            return best_bid, best_ask
        except BinanceAPIException as e:
            self.logger.error(f"Binance API Exception: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")

    def get_exchange_info(self):
        try:
            return self.client.futures_exchange_info()
        except BinanceAPIException as e:
            self.logger.error(f"Binance API Exception: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
            

    def get_tick_size(self, symbol):
        exchange_info = self.get_exchange_info()
        if exchange_info:
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol:
                    for f in s['filters']:
                        if f['filterType'] == 'PRICE_FILTER':
                            return f['tickSize']
        else:
            self.logger.error("Failed to fetch exchange info")
            return None

    def get_open_positions(self, symbol):
        try:
            all_positions = self.client.futures_position_information()
            position_for_symbol = [position for position in all_positions if position['symbol'] == symbol]
            return position_for_symbol
        except BinanceAPIException as e:
            print(f"Binance API Exception: {e}")
        except BinanceOrderException as e:
            print(f"Binance Order Exception: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


    def cancel_all_orders(self, symbol):
        self.client.cancel_all_orders(symbol=symbol)


    def close_open_position(self, symbol):
        positions = self.client.get_open_positions(symbol=symbol)
        for position in positions:
            if position['positionAmt'] != '0':
                order_side = 'SELL' if float(position['positionAmt']) > 0 else 'BUY'
                self.client.create_order(symbol=symbol, side=order_side, type='MARKET', quantity=abs(float(position['positionAmt'])))


