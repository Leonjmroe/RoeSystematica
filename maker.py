from binance_api import BinanceAPI
from binance_price_ws import BinancePriceWebSocket
from binance_order_ws import BinanceOrderWebSocket
from listen_key import get_listen_key
from dotenv import load_dotenv
import threading
import time
import os




class OrderHandler():
    def __init__(self, max_positions, binance_api, order_placer):
        self.binance_api = binance_api
        self.order_placer = order_placer
        self.max_positions = max_positions
        self.open_orders = {'ask': None, 'bid': None}
        self.open_longs = []
        self.open_shorts = []
        self.trades = []

    def order_listener(self, order):
        if order['o']['X'] == 'FILLED':
            print(f'''A {order['o']['s']} {order['o']['S']} {order['o']['o']} order of ${round(float(order['o']['p']) * float(order['o']['q']))} FILLED at {order['o']['p']}. Order ID: {order['o']['i']}''')
            self.handle_fill(order)

    def order_placed_details(self, order):
        print(f'''A {order.get('symbol')} {order.get('side')} {order.get('type')} order of ${round(float(order.get('origQty')) * float(order.get('price')))} PLACED at {order.get('price')}. Order ID: {order.get('orderId')}''')
        self.handle_orders(order, status='PLACED')

    def handle_orders(self, order, status):
        if status == 'FILLED':
            self.open_orders['ask'] = None
            self.open_orders['bid'] = None

        if order.get('side') == 'BUY':
            if status == 'FILLED':
                if len(open_shorts) == 0:
                    self.open_longs.append(order)
                else:
                    self.trades = (order, self.open_shorts[0])
                    self.open_shorts.pop(0)
            if status == 'PLACED':
                self.open_orders['bid'] = order
        if order.get('side') == 'SELL':
            if status == 'FILLED':
                if len(open_longs) == 0:
                    self.open_shorts.append(order)
                else:
                    self.trades = (self.open_longs[0], order)
                    self.open_longs.pop(0)
            if status == 'PLACED':
                self.open_orders['ask'] = order

    def handle_fill(self, order):
        self.handle_orders(order, status='FILLED')
        self.pull_open_order(order)
        
    def pull_open_order(self, order):
        try:
            print(order.get('side'), self.order_placer.ticker)
        except Exception as e:
            print(e)
        if order.get('side') == 'BUY':
            try:
                self.binance_api.cancel_order(symbol=self.order_placer.ticker, order_id=self.open_orders['ask'].get('orderId'))
            except Exception as e:
                print(e)
        if order.get('side') == 'SELL':
            try:
                self.binance_api.cancel_order(symbol=self.order_placer.ticker, order_id=self.open_orders['bid'].get('orderId'))
            except Exception as e:
                print(e)
        print('Order pulled.')





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
        self.ask = round(float(prices[0]) + (float(prices[0]) * (self.pip_spread / 10000)), self.tick_size)
        self.bid = round(float(prices[1]) - (float(prices[1]) * (self.pip_spread / 10000)), self.tick_size)

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
        if init:
            self.tick_size = self.get_tick_count(self.binance_api.get_tick_size(self.ticker))
        self.get_order_prices()
        order_size = self.get_btc_order_size()
        ask_order = self.binance_api.create_order(symbol=self.ticker, side='SELL', type='LIMIT', quantity=order_size, price=self.ask)
        bid_order = self.binance_api.create_order(symbol=self.ticker, side='BUY', type='LIMIT', quantity=order_size, price=self.bid)





class PriceHandler():
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




class MarketMakerController():
    def __init__(self, ticker, ws_price_stream, pip_spread, pip_risk, max_positions, api_key):
        self.binance_api = BinanceAPI()
        self.price_handler = PriceHandler()
        self.order_placer = OrderPlacer(self.binance_api, self.price_handler, ticker, pip_spread, pip_risk)
        self.order_handler = OrderHandler(self.binance_api, self.order_placer, max_positions)
        self.binance_price_ws = BinancePriceWebSocket(ws_price_stream)
        self.api_key = api_key
        self.binance_order_ws = BinanceOrderWebSocket(self.listen_key())

    def start_price_ws(self):
        self.price_handler.callback = self.place_orders
        self.binance_price_ws.callback = self.price_handler.price_feed
        price_thread = threading.Thread(target=self.binance_price_ws.run_forever)
        price_thread.start() 

    def start_order_ws(self):
        self.binance_order_ws.callback = self.order_handler.order_listener
        self.binance_api.callback = self.order_handler.order_placed_details
        orders_thread = threading.Thread(target=self.binance_order_ws.run_forever)
        orders_thread.start()  

    def listen_key(self):
        listen_key = get_listen_key(self.api_key)
        return listen_key

    def place_orders(self):
        self.order_placer.place_orders(init=True)

    def run(self):
        self.start_price_ws()
        self.start_order_ws()




if __name__ == "__main__":
    market_maker = MarketMakerController(ticker='BTCUSDT',
                                         ws_price_stream="wss://stream.binancefuture.com/ws/btcusdt_perpetual@bookTicker",
                                         api_key=os.getenv('API_KEY_TEST'),
                                         pip_spread=1,
                                         pip_risk=50,
                                         max_positions=5)
    market_maker.run()





















