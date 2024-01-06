import json
import time
from websocket import WebSocketApp



class BinanceOrderWebSocket:
    def __init__(self, logger, listen_key):
        self.listen_key = listen_key
        self.ws = None
        self.callback = None
        self.logger = logger

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            self.callback(data)

        except KeyError as e:
            #self.logger.warning(f"KeyError encountered: {e}")
            pass
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON Decoding Error: {e}")
        except Exception as e:
            self.logger.error(f"General Error: {e}")

    def on_error(self, ws, error):
        self.logger.error(f"WebSocket Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        self.logger.info(f"WebSocket Closed: Code: {close_status_code}, Message: {close_msg}")
        time.sleep(10)  # Short delay before attempting to reconnect
        self.logger.info("Attempting to reconnect...")
        self.run_forever()  # Reconnect

    def on_open(self, ws):
        self.logger.info("WebSocket Connection Opened")

    def run_forever(self):
        ws_url = f"wss://stream.binancefuture.com/ws/{self.listen_key}"
        self.ws = WebSocketApp(ws_url,
                               on_open=self.on_open,
                               on_message=self.on_message,
                               on_error=self.on_error,
                               on_close=self.on_close)
        self.ws.run_forever()
