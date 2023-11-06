from binance_api import binance_api


balances = binance_api.get_balance()
for account in balances:
	if account['asset'] == 'USDT':
		print('Balance: $' + "{:,}".format(round(float(account['balance']))))


# open_orders = binance_api.get_open_orders(symbol='BTCUSDT')
# all_orders = binance_api.get_all_orders(symbol='BTCUSDT')
# cancel = binance_api.cancel_order(symbol='BTCUSDT', order_id='order_id_here')

# order = binance_api.create_order(symbol='BTCUSDT', side='BUY', type='LIMIT', quantity=1, price='35034')
