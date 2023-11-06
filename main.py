from binance_api import binance


account_info = binance.get_account_info()
if account_info:
    print(account_info)

balance = binance.get_asset_balance(asset='BTC')
if balance:
    print(balance)

tickers = binance.get_all_tickers()
if tickers:
    print(tickers)