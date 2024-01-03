from binance_api.api import BinanceAPI
from binance_api.price_ws import BinancePriceWebSocket
from binance_api.order_ws import BinanceOrderWebSocket
from binance_api.listen_key import get_listen_key
import threading
import os
import logging
from datetime import datetime



# Setup file logging
log_file_path = os.path.join('logs/', f'market_maker_log_{datetime.now().strftime("%H%M%S")}.log')
logger = logging.getLogger('MarketMakerLogger')
logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all levels of logs
logger.propagate = False  # Prevents log messages from being propagated to the root logger

# Formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - Line: %(lineno)d - %(message)s', datefmt='%H:%M:%S')

# File Handler
fh = logging.FileHandler(log_file_path)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

# Stream Handler for console output
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)  # Adjust as needed
ch.setFormatter(formatter)
logger.addHandler(ch)




class OrderHandler:
    def __init__(self, binance_api, order_placer, max_positions):
        self.binance_api = binance_api
        self.order_placer = order_placer
        self.max_positions = max_positions
        self.open_orders = {'ask': None, 'bid': None}
        self.open_longs = []
        self.open_shorts = []
        self.trades = []


    def order_listener(self, order):
        if order['o']['X'] == 'FILLED':
            logger.info(f'''{order['o']['s']} {order['o']['S']} {order['o']['o']} order for ${round(float(order['o']['p']) * float(order['o']['q']))} FILLED at {order['o']['p']}. OrderID: {str(order['o']['i'])[-3:]}''')
            self.pull_open_order(order['o']['S'])
            self.handle_orders(order, status='FILLED', side=order['o']['S'])
        if len(self.open_longs) == self.max_positions or len(self.open_longs) == self.max_positions:
            # logger.info(order)
            pass


    def order_placed_details(self, order):
        logger.info(f'''{order.get('symbol')} {order.get('side')} {order.get('type')} order for ${round(float(order.get('origQty')) * float(order.get('price')))} PLACED at {order.get('price')}. OrderID: {str(order.get('orderId'))[-3:]}''')
        self.handle_orders(order, status='PLACED', side=order.get('side'))


    def handle_orders(self, order, status, side):
        if side == 'BUY':
            if status == 'FILLED':
                if len(self.open_shorts) == 0:
                    self.open_longs.append(order)
                    self.get_inventory()
                    if len(self.open_longs) == self.max_positions:
                        self.set_stop_loss('SELL')
                else:
                    self.trades.append((order, self.open_shorts[0]))
                    self.open_shorts.pop(0)
                    logger.info('Trade Complete. Count: ' + str(len(self.trades)))
                    self.get_inventory()
            if status == 'PLACED':
                self.open_orders['bid'] = order
        if side == 'SELL':
            if status == 'FILLED':
                if len(self.open_longs) == 0:
                    self.open_shorts.append(order)
                    self.get_inventory()
                    if len(self.open_shorts) == self.max_positions:
                        self.set_stop_loss('BUY')
                else:
                    self.trades.append((self.open_longs[0], order))
                    self.open_longs.pop(0)
                    logger.info('Trade Complete. Count: ' + str(len(self.trades)))
                    self.get_inventory()
            if status == 'PLACED':
                self.open_orders['ask'] = order

    def get_inventory(self):
        logger.info('Short Inventory: ' + str(len(self.open_shorts)))
        logger.info('Long Inventory: ' + str(len(self.open_longs)))


    def pull_open_order(self, side):
        if side == 'BUY':
            pulled_order = self.api_pull_order('ask')
            logger.info('Offer pulled. OrderID: ' + str(pulled_order.get('orderId'))[-3:])
        if side == 'SELL':
            pulled_order = self.api_pull_order('bid')
            logger.info('Bid pulled. OrderID: ' + str(pulled_order.get('orderId'))[-3:])
        self.open_orders = {'ask': None, 'bid': None}
        self.order_placer.place_orders()


    def api_pull_order(self, side):
        try:    
            pulled_order = self.binance_api.cancel_order(symbol=self.order_placer.ticker, order_id=self.open_orders[side].get('orderId'))
            return pulled_order
        except Exception as e:
            logger.error(e)


    def set_stop_loss(self, side):
        try:
            order_size = abs(float(self.binance_api.get_open_positions(self.order_placer.ticker)[0].get('positionAmt')))
            self.order_placer.get_order_prices()
            if side == 'SELL':
                price = self.order_placer.bid
            else:
                price = self.order_placer.ask
            self.binance_api.create_stop_market_order(symbol=self.order_placer.ticker, side=side, quantity=order_size, stop_price=price)
            logger.info('Stop loss order placed.')
        except Exception as e:
            logger.error(e)






class OrderPlacer:
    def __init__(self, binance_api, price_handler, ticker, pip_spread, pip_risk):
        self.binance_api = binance_api
        self.price_handler = price_handler
        self.ticker = ticker
        self.pip_risk = pip_risk
        self.pip_spread = pip_spread
        self.ask = None
        self.bid = None
        self.tick_size = None

    def get_order_prices(self):
        prices = self.price_handler.get_prices()
        self.ask = round(float(prices[0]) + (float(prices[0]) * (self.pip_spread / 10000)), self.tick_size)
        self.bid = round(float(prices[1]) - (float(prices[1]) * (self.pip_spread / 10000)), self.tick_size)

    def get_btc_order_size(self):
        dollar_risk = (self.pip_risk / 10000) * ((self.ask + self.bid) / 2)
        btc_order_size = round((dollar_risk / ((self.ask + self.bid) / 2)), 3)
        if btc_order_size < 0.001:
            btc_order_size = 0.001
        return btc_order_size

    @staticmethod
    def get_tick_count(tick_data):
        tick = 0.1 / float(tick_data)
        if tick == 1:
            return 1
        else:
            return str(tick).count('0')

    def place_orders(self, init=False):
        if init:
            self.tick_size = self.get_tick_count(self.binance_api.get_tick_size(self.ticker))
        self.get_order_prices()
        order_size = self.get_btc_order_size()
        self.binance_api.create_order(symbol=self.ticker, side='SELL', type='LIMIT', quantity=order_size, price=self.ask)
        self.binance_api.create_order(symbol=self.ticker, side='BUY', type='LIMIT', quantity=order_size, price=self.bid)




class PriceHandler:
    def __init__(self):
        self.ask = None
        self.bid = None
        self.activated = None
        self.callback = None

    def price_feed(self, data):
        self.ask = float(data['a'])
        self.bid = float(data['b'])
        if not self.activated:
            self.activated = True
            if self.callback:
                self.callback()

    def get_prices(self):
        return self.ask, self.bid



class MarketMakerController:
    def __init__(self, ticker, ws_price_stream, pip_spread, pip_risk, max_positions, api_key):
        self.binance_api = BinanceAPI()
        self.price_handler = PriceHandler()
        self.order_placer = OrderPlacer(self.binance_api, self.price_handler, ticker, pip_spread, pip_risk)
        self.order_handler = OrderHandler(self.binance_api, self.order_placer, max_positions)
        self.binance_price_ws = BinancePriceWebSocket(ws_price_stream)
        self.api_key = api_key
        self.binance_order_ws = BinanceOrderWebSocket(self.listen_key())
        self.ticker = ticker

    def start_price_ws(self):
        self.price_handler.callback = self.place_orders
        self.binance_price_ws.callback = self.price_handler.price_feed
        price_thread = threading.Thread(target=self.binance_price_ws.run_forever)
        price_thread.start()

    def start_order_ws(self):
        self.binance_api.callback = self.order_handler.order_placed_details
        self.binance_order_ws.callback = self.order_handler.order_listener
        orders_thread = threading.Thread(target=self.binance_order_ws.run_forever)
        orders_thread.start()

    def listen_key(self):
        listen_key = get_listen_key(self.api_key)
        return listen_key

    def place_orders(self):
        # try:
        #     self.binance_api.cancel_all_orders(self.ticker)
        # except Exception as e:
        #     logger.error(e)
        # try:
        #     self.binance_api.close_open_position(self.ticker)
        # except Exception as e:
        #     logger.error(e)
        self.order_placer.place_orders(init=True)

    def run(self):
        self.start_price_ws()
        self.start_order_ws()



if __name__ == "__main__":
    market_maker = MarketMakerController(ticker='BTCUSDT',
                                         ws_price_stream="wss://stream.binancefuture.com/ws/btcusdt_perpetual@bookTicker",
                                         api_key=os.getenv('API_KEY_TEST'),
                                         pip_spread=2,
                                         pip_risk=50,
                                         max_positions=3)    
    market_maker.run()


