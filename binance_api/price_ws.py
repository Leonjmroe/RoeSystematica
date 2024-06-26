import websocket
import threading
import json




class BinancePriceWebSocket:
    def __init__(self, logger, stream_url):
        self.stream_url = stream_url
        self.ws = None  
        self.callback = None
        self.logger = logger

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if 'result' in data and 'id' in data:
                self.logger.info(f"Subscription confirmed: {data}")
            elif 'b' in data and 'B' in data and 'a' in data and 'A' in data:
                if self.callback:
                    self.callback(data)
            else:
                self.logger.warning(f"Message received without expected keys: {data}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON: {e}")
        except Exception as e:
            self.logger.error(f"Error in on_message: {e}")

    def on_error(self, ws, error):
        self.logger.error(error)

    def on_close(self, ws, close_status_code, close_msg):
        self.logger.info("### WebSocket closed ###")

    def on_open(self, ws):
        def run(*args):
            ws.send(json.dumps({
                "method": "SUBSCRIBE",
                "params": [
                    "btcusdt@bookTicker"
                ],
                "id": 1
            }))
            self.logger.info("BinancePriceWebSocket connection opened and subscribed to streams")
        threading.Thread(target=run).start()

    def run_forever(self):
        self.ws = websocket.WebSocketApp(self.stream_url,
                                        on_open=self.on_open,
                                        on_message=self.on_message,
                                        on_error=self.on_error,
                                        on_close=self.on_close)
        try:
            self.ws.run_forever()
        except Exception as e:
            logger.error(e)


