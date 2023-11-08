from binance_api import binance_api
from binance_price_ws import BinancePriceWebSocket
from binance_orders_ws import BinanceOrdersWebSocket
import os
from listen_key import get_listen_key
from dotenv import load_dotenv
import threading


load_dotenv()
api_key = os.getenv('API_KEY_TEST')
api_secret = os.getenv('API_SECRET_TEST')
listen_key = get_listen_key(api_key, api_secret)


balances = binance_api.get_balance()
for account in balances:
	if account['asset'] == 'USDT':
		print('Balance: $' + "{:,}".format(round(float(account['balance']))))


binance_orders_ws = BinanceOrdersWebSocket(listen_key)
orders_thread = threading.Thread(target=binance_orders_ws.run_forever)
orders_thread.start()  



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

		if len(self.ask_orders) == 0:
			order = binance_api.create_order(symbol='BTCUSDT', side='SELL', type='LIMIT', quantity=btc_order_size, price=ask_px)
			self.ask_orders.append(order)

		if len(self.bid_orders) == 0:
			order = binance_api.create_order(symbol='BTCUSDT', side='BUY', type='LIMIT', quantity=btc_order_size, price=bid_px)
			self.bid_orders.append(order)



market_maker = MarketMaker(100, 5)

binance_price_ws = BinancePriceWebSocket("wss://stream.binancefuture.com/ws/btcusdt_perpetual@bookTicker")
binance_price_ws.callback = market_maker.market_make
price_thread = threading.Thread(target=binance_price_ws.run_forever)
# price_thread.start() 



# open_orders = binance_api.get_open_orders(symbol='BTCUSDT')
# all_orders = binance_api.get_all_orders(symbol='BTCUSDT')
# cancel = binance_api.cancel_order(symbol='BTCUSDT', order_id='order_id_here')
# order = binance_api.create_order(symbol='BTCUSDT', side='BUY', type='LIMIT', quantity=1, price='35034')


