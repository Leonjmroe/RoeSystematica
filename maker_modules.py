
class OrderPlacer():
    def __init__(self, binance_api, price_handler, ticker, pip_spread, pip_risk):
        self.binance_api = binance_api
        self.price_hander = PriceHandler()
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
        print(prices)
        ask_px = round(self.ask + (self.ask * (self.pip_spread / 10000)), 1)
        bid_px = round(self.bid - (self.bid * (self.pip_spread / 10000)), 1)
        pinrt(ask_px, bid_px)
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



class PriceHandler():
    def __init__(self):
        self.ask = None
        self.bid = None

    def price_feed(self, data):
        self.ask = float(data['a'])
        self.bid = float(data['b'])

    def get_prices(self):
        return self.ask, self.bid 
