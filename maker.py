from binance_api import binance_api
from binance_price_ws import BinancePriceWebSocket
from binance_orders_ws import BinanceOrdersWebSocket
import os
from listen_key import get_listen_key, keep_alive
from dotenv import load_dotenv
import threading



class PriceHandler():
    def __init__(self);
        self.ask = None
        self.bid = None

    def price_feed(self, data):
        self.ask = float(data['a'])
        self.bid = float(data['b'])

    def get_prices(self):
        return self.ask, self.bid 




class OrderHandler():
    def __init__(self, dollar_risk, pip_spread):
        self.api = API()
        self.price_hander = PriceHandler()
        self.dollar_risk = dollar_risk
        self.pip_spread = pip_spread
        self.ask = None
        self.bid = None

    def get_order_prices(self):
        prices = self.price_hander.get_prices()
        self.ask = prices[0]
        self.bid = prices[1]
        ask_px = round(self.ask + (self.ask * (self.pip_spread / 10000)), 1)
        bid_px = round(self.bid - (self.bid * (self.pip_spread / 10000)), 1)
        return ask_px, bid_px 

    def get_btc_order_size(self):
        btc_order_size = round((self.dollar_risk / ((self.ask + self.bid) / 2)), 3)
        if btc_order_size < 0.001:
            btc_order_size = 0.001
        return btc_order_size

    def handle_initial_orders(self):
        order_prices = self.get_order_prices()
        order_size = self.get_btc_order_size()
        self.send_orders(order_prices, order_size)

    def send_orders(self, order_prices, order_size):
        self.api.send_order(order_prices[0], order_size)
        self.api.send_order(order_prices[1], order_size)

    



class Controller():
    def __init__(self, api, dollar_balance, dollar_risk, pip_spread):
        self.api = api
        self.longs = []
        self.shorts = []
        self.open_long = None
        self.open_short = None
        self.dollar_balance = dollar_balance
        self.trade_id = 0
        
    def fill_check(self, price):
        if self.open_long != None:
            if price <= self.open_long.get('price'):
                print(f'''Long Fill at {self.open_long.get('price')} ID: {self.open_long.get('id')}''')
                self.open_long = None
                self.longs.append(self.open_long)
                self.pull_order('SELL')
                self.place_order(price, 'BUY')
                self.place_order(price, 'SELL')
        if self.open_short != None:
            if price >= self.open_short.get('price'):
                print(f'''Short Fill at {self.open_short.get('price')} ID: {self.open_short.get('id')}''')
                self.open_short = None
                self.shorts.append(self.open_short)
                self.pull_order('BUY')
                self.place_order(price, 'BUY')
                self.place_order(price, 'SELL')
            
            
    def place_order(self, price, side):
        if side == 'BUY':
            price = price - self.spread
        else:
            price = price + self.spread
        order = {'side': side,
                 'size': self.balance * self.risk,
                 'price': price,
                 'id': self.trade_id}
        if side == 'BUY':
            self.open_long = order 
        else:
            self.open_short = order 
        self.trade_id += 1
        self.api.send_order(order)
    
    
    def api_order_send(order):
        print(f'''Order sent to API with order ID: {order.get('id')}''')
        if order.get('side') == 'BUY':
            self.open_long = order
        else: 
            self.open_short = order 
            
            
    def pull_order(self, side):
        if side == 'BUY':
            self.api.pull_order(self.open_long.get('id'))
        else: 
            self.api.pull_order(self.open_short.get('id'))
        
        
            
class API():
    def __init__(self):
        pass
    
    def send_order(self, order):
        print(f'''API sent {order.get('side')} order at {order.get('price')} ID: {order.get('id')}''')
    
    def pull_order(self, id):
        print(f'''API pulled order. ID: {id}''')
   
   
            
# def run(prices, controller):
#     controller.place_order(prices[0], 'BUY')
#     controller.place_order(prices[0], 'SELL')
#     for price in prices:
#         controller.fill_check(price)

        
dollar_balance = 10000
pct_risk = 0.5
pip_spread = 10

price_hander = PriceHandler()
controller = Controller(API(), dollar_balance, pct_risk, pip_spread)
price_ws = BinancePriceWebSocket("wss://stream.binancefuture.com/ws/btcusdt_perpetual@bookTicker")
price_ws.callback = price_hander.price_feed
price_thread = threading.Thread(target=price_ws.run_forever)
price_thread.start() 

















