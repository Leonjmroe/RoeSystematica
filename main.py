from binance_api import BinanceAPI
from binance_price_ws import BinancePriceWebSocket
from binance_orders_ws import BinanceOrdersWebSocket
import os
from listen_key import get_listen_key, keep_alive
from dotenv import load_dotenv
import threading


load_dotenv()
api_key = os.getenv('API_KEY_TEST')
api_secret = os.getenv('API_SECRET_TEST')


listen_key = get_listen_key(api_key)
keep_alive_thread = threading.Thread(target=keep_alive, args=(api_key, listen_key))
keep_alive_thread.start()

binance_api = BinanceAPI()
balances = binance_api.get_balance()
for account in balances:
	if account['asset'] == 'USDT':
		print('Balance: $' + "{:,}".format(round(float(account['balance']))))




class MarketMaker:
	def __init__(self, dollar_order_size, pip_width):
		self.ask_orders = []
		self.bid_orders = []
		self.dollar_order_size = dollar_order_size
		self.pip_width = pip_width


	def market_make(self, data):
		ask = float(data['a'])
		bid = float(data['b'])
		ask_qty = round(ask * float(data['A']))
		bid_qty = round( bid * float(data['B']))
		ask_px = round(ask + (ask * (self.pip_width / 10000)), 1)
		bid_px = round(bid - (bid * (self.pip_width / 10000)), 1)
		btc_order_size = round((self.dollar_order_size / ((ask + bid) / 2)), 3)
		if btc_order_size < 0.001:
			btc_order_size = 0.001
		self.get_btc_order_size(ask, bid)
		self.place_orders(ask_px, bid_px, btc_order_size)


	def get_btc_order_size(self, ask, bid):
		btc_order_size = round((self.dollar_order_size / ((ask + bid) / 2)), 3)
		if btc_order_size < 0.001:
			btc_order_size = 0.001
		return btc_order_size


	def place_orders(self, ask_px, bid_px, btc_order_size):
		if len(self.ask_orders) == 0:
			order = binance_api.create_order(symbol='BTCUSDT', side='SELL', type='LIMIT', quantity=btc_order_size, price=ask_px)
			self.ask_orders.append(order)

		if len(self.bid_orders) == 0:
			order = binance_api.create_order(symbol='BTCUSDT', side='BUY', type='LIMIT', quantity=btc_order_size, price=bid_px)
			self.bid_orders.append(order)




class OrderHandler:
	def __init__(self):
		self.market_maker = MarketMaker(100, 1)
		self.orders_out = []
		self.long_positiions = []
		self.short_positiions = []

	def order_listener(self, data):

		if data['o']['X'] == 'NEW':
			self.orders_out.append((data['o']['c'], data))
			print(f'''A {data['o']['s']} {data['o']['S']} {data['o']['o']} order of ${round(float(data['o']['p']) * float(data['o']['q']))} PLACED at {data['o']['p']}''')

		if data['o']['X'] == 'FILLED':
			print(f'''A {data['o']['s']} {data['o']['S']} {data['o']['o']} order of ${round(float(data['o']['p']) * float(data['o']['q']))} FILLED at {data['o']['p']}''')
			self.handle_fill(data)


	def handle_fill(self, data):
		order_id = data['o']['c']
		if data['o']['S'] == 'BUY':
			if len(self.short_positiions) == 0:
				self.long_positiions.append((order_id, data))
			else:
				self.short_positiion_close(order_id)
		else:
			if len(self.long_positiions) == 0:
				self.short_positiions.append((order_id, data))
			else:
				self.long_positiion_close(order_id)

	def short_positiion_close(self, order_id):
		for order in orders_out:
			if order[0] == order_id:
				print('Found open order: ', order_id)

	def long_positiion_close(self, order_id):
		for order in orders_out:
			if order[0] == order_id:
				print('Found open order: ', order_id)





order_handler = OrderHandler()
binance_orders_ws = BinanceOrdersWebSocket(listen_key)
binance_orders_ws.callback = order_handler.order_listener
orders_thread = threading.Thread(target=binance_orders_ws.run_forever)
orders_thread.start()  


market_maker = MarketMaker(100, 1)
binance_price_ws = BinancePriceWebSocket("wss://stream.binancefuture.com/ws/btcusdt_perpetual@bookTicker")
binance_price_ws.callback = market_maker.market_make
price_thread = threading.Thread(target=binance_price_ws.run_forever)
price_thread.start() 



# open_orders = binance_api.get_open_orders(symbol='BTCUSDT')
# all_orders = binance_api.get_all_orders(symbol='BTCUSDT')
# cancel = binance_api.cancel_order(symbol='BTCUSDT', order_id='order_id_here')
# order = binance_api.create_order(symbol='BTCUSDT', side='BUY', type='LIMIT', quantity=1, price='35034')






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
   

