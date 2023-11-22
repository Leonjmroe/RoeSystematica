from binance_api import BinanceAPI
from binance_price_ws import BinancePriceWebSocket
from binance_order_ws import BinanceOrderWebSocket
import threading
import time
import os
from listen_key import get_listen_key
from dotenv import load_dotenv




class PriceHandler():
    def __init__(self):
        self.ask = None
        self.bid = None

    def price_feed(self, data):
        self.ask = float(data['a'])
        self.bid = float(data['b'])

    def get_prices(self):
        return self.ask, self.bid 



class OrderPlacer():
    def __init__(self, binance_api, price_handler, ticker, pip_spread, pip_risk):
        self.binance_api = binance_api
        self.price_hander = price_handler
        self.ticker = ticker
        self.pip_risk = pip_risk
        self.pip_spread = pip_spread
        self.ask = None
        self.bid = None
        self.tick_size = None

    def get_order_prices(self):
        prices = self.price_hander.get_prices()
        self.ask = prices[0]
        self.bid = prices[1]
        ask_px = round(self.ask + (self.ask * (self.pip_spread / 10000)), 1)
        bid_px = round(self.bid - (self.bid * (self.pip_spread / 10000)), 1)
        return ask_px, bid_px 

    def get_btc_order_size(self):
        dollar_risk = (self.pip_risk / 10000) * ((self.ask + self.bid) / 2)
        btc_order_size = round((dollar_risk / ((self.ask + self.bid) / 2)), 3)
        if btc_order_size < 0.001:
            btc_order_size = 0.001
        return btc_order_size

    def get_tick_count(self, tick_data):
        tick = 0.1 / float(tick_data)
        if tick == 1:
            return 1
        else:
            return str(tick).count('0')

    def place_orders(self, init=False):
        if init == True:
            tick_data = self.binance_api.get_tick_size(self.ticker)
            self.tick_size = self.get_tick_count(tick_data)
            order_prices = self.binance_api.get_last_bid_ask(self.ticker)
            self.ask = float(order_prices[0])
            self.bid = float(order_prices[1])
            order_size = self.get_btc_order_size()
        else:
            order_prices = self.get_order_prices()
            order_size = self.get_btc_order_size()
        ask_price = round(float(order_prices[0]), self.tick_size)
        bid_price = round(float(order_prices[1]), self.tick_size)
        ask_order = self.binance_api.create_order(symbol=self.ticker, side='SELL', type='LIMIT', quantity=order_size, price=ask_price)
        bid_order = self.binance_api.create_order(symbol=self.ticker, side='BUY', type='LIMIT', quantity=order_size, price=bid_price)




class OrderHandler():
    def __init__(self, max_positions, binance_api, order_placer):
        self.binance_api = binance_api
        self.order_placer = order_placer
        self.max_positions = max_positions
        self.open_orders = {'ask': None, 'bid': None}
        self.open_longs = []
        self.open_shorts = []

    def order_listener(self, data):
        if data['o']['X'] == 'NEW':
            self.open_orders.append((data['o']['c'], data))
            print(f'''A {data['o']['s']} {data['o']['S']} {data['o']['o']} order of ${round(float(data['o']['p']) * float(data['o']['q']))} PLACED at {data['o']['p']}''')

        if data['o']['X'] == 'FILLED':
            print(f'''A {data['o']['s']} {data['o']['S']} {data['o']['o']} order of ${round(float(data['o']['p']) * float(data['o']['q']))} FILLED at {data['o']['p']}''')
            self.handle_fill(data)

    def handle_fill(self, data):
        print('Handling fill...')

    def pull_order(self):
        print('Order pulled.')




class MarketMakerController():
    def __init__(self, ticker, ws_price_stream, pip_spread, pip_risk, max_positions, api_key):
        self.binance_api = BinanceAPI()
        self.price_handler = PriceHandler()
        self.order_placer = OrderPlacer(self.binance_api, self.price_handler, ticker, pip_spread, pip_risk)
        self.order_handler = OrderHandler(self.binance_api, self.order_placer, max_positions)
        self.binance_price_ws = BinancePriceWebSocket(ws_price_stream)
        self.api_key = api_key
        self.binance_order_ws = BinanceOrderWebSocket(self.listen_key())

    def run(self):
        self.start_price_ws()
        self.start_order_ws()
        self.place_orders()

    def start_price_ws(self):
        self.binance_price_ws.callback = self.price_handler.price_feed
        price_thread = threading.Thread(target=self.binance_price_ws.run_forever)
        price_thread.start() 

    def start_order_ws(self):
        self.binance_order_ws.callback = self.order_handler.order_listener
        orders_thread = threading.Thread(target=self.binance_order_ws.run_forever)
        orders_thread.start()  

    def listen_key(self):
        listen_key = get_listen_key(self.api_key)
        return listen_key

    def place_orders(self):
        self.order_placer.place_orders(init=True)




if __name__ == "__main__":
    app = MarketMakerController(ticker='BTCUSDT',
                                ws_price_stream="wss://stream.binancefuture.com/ws/btcusdt_perpetual@bookTicker",
                                api_key=os.getenv('API_KEY_TEST'),
                                pip_spread=25,
                                pip_risk=50,
                                max_positions=5)
    app.run()





















