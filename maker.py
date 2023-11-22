from binance_api import BinanceAPI
from binance_price_ws import BinancePriceWebSocket
from binance_orders_ws import BinanceOrdersWebSocket
import threading
import time



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
    def __init__(self, ticker, pip_spread, pip_risk, max_positions):
        self.ticker = ticker
        self.pip_risk = pip_risk
        self.pip_spread = pip_spread
        self.max_positions = max_positions
        self.api = BinanceAPI()
        self.price_hander = PriceHandler()
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
            tick_data = self.api.get_tick_size(self.ticker)
            self.tick_size = self.get_tick_count(tick_data)
            order_prices = self.api.get_last_bid_ask(self.ticker)
            self.ask = float(order_prices[0])
            self.bid = float(order_prices[1])
            order_size = self.get_btc_order_size()
        else:
            order_prices = self.get_order_prices()
            order_size = self.get_btc_order_size()
        ask_price = round(float(order_prices[0]), self.tick_size)
        bid_price = round(float(order_prices[1]), self.tick_size)
        ask_order = self.api.create_order(symbol=self.ticker, side='SELL', type='LIMIT', quantity=order_size, price=ask_price)
        bid_order = self.api.create_order(symbol=self.ticker, side='BUY', type='LIMIT', quantity=order_size, price=bid_price)



# Price WebSocket 
price_hander = PriceHandler()
price_ws = BinancePriceWebSocket("wss://stream.binancefuture.com/ws/btcusdt_perpetual@bookTicker")
price_ws.callback = price_hander.price_feed
price_thread = threading.Thread(target=price_ws.run_forever)
price_thread.start() 

# Order Handling
order_placer = OrderPlacer('BTCUSDT', pip_spread=25, pip_risk=50, max_positions=5)
order_placer.place_orders(init=True)



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
   
















