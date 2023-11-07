from binance_api import binance_api
from binance_ws import BinanceWebSocket


balances = binance_api.get_balance()
for account in balances:
	if account['asset'] == 'USDT':
		print('Balance: $' + "{:,}".format(round(float(account['balance']))))


ask_orders = []
bid_orders = []


def market_make(data):

	ask = float(data['a'])
	bid = float(data['b'])
	ask_qty = float(data['A'])
	bid_qty = float(data['B'])
	ask_qty_usdt = round(ask * ask_qty)
	bid_qty_usdt = round(ask * bid_qty)

	pip_palcement = 5
	btc_order_size = 0.1

	ask_px = round(ask + (ask * (pip_palcement / 10000)), 1)
	bid_px = round(bid - (bid * (pip_palcement / 10000)), 1)

	if len(ask_orders) == 0:
		order = binance_api.create_order(symbol='BTCUSDT', side='SELL', type='LIMIT', quantity=btc_order_size, price=ask_px)
		ask_orders.append(order)

	if len(bid_orders) == 0:
		order = binance_api.create_order(symbol='BTCUSDT', side='BUY', type='LIMIT', quantity=btc_order_size, price=bid_px)
		bid_orders.append(order)



stream_url = "wss://stream.binancefuture.com/ws/btcusdt_perpetual@bookTicker"
binance_ws = BinanceWebSocket(stream_url)
binance_ws.callback = market_make
binance_ws.run_forever()

# open_orders = binance_api.get_open_orders(symbol='BTCUSDT')
# all_orders = binance_api.get_all_orders(symbol='BTCUSDT')
# cancel = binance_api.cancel_order(symbol='BTCUSDT', order_id='order_id_here')
# order = binance_api.create_order(symbol='BTCUSDT', side='BUY', type='LIMIT', quantity=1, price='35034')






