from maker_modules import PriceHandler, OrderPlacer
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

    def order_listener(self, data):
        if data['o']['X'] == 'NEW':
            self.open_orders.append((data['o']['c'], data))
            print(f'''A {data['o']['s']} {data['o']['S']} {data['o']['o']} order of ${round(float(data['o']['p']) * float(data['o']['q']))} NEW at {data['o']['p']}. Order ID: {data['o']['i']}''')

        if data['o']['X'] == 'FILLED':
            print(f'''A {data['o']['s']} {data['o']['S']} {data['o']['o']} order of ${round(float(data['o']['p']) * float(data['o']['q']))} FILLED at {data['o']['p']}. Order ID: {data['o']['i']}''')
            self.handle_fill(data)

    def order_placed_details(self, order):
        print(f'''A {order.get('symbol')} {order.get('side')} {order.get('type')} order of ${round(float(order.get('origQty')) * float(order.get('price')))} PLACED at {order.get('price')}. Order ID: {order.get('orderId')}''')

    def handle_fill(self, data):
        pass

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

    def start_price_ws(self):
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
        self.order_placer.place_orders(init=False)

    def run(self):
        self.start_price_ws()
        self.start_order_ws()
        self.place_orders()




if __name__ == "__main__":
    market_maker = MarketMakerController(ticker='BTCUSDT',
                                         ws_price_stream="wss://stream.binancefuture.com/ws/btcusdt_perpetual@bookTicker",
                                         api_key=os.getenv('API_KEY_TEST'),
                                         pip_spread=100,
                                         pip_risk=50,
                                         max_positions=5)
    market_maker.run()





















