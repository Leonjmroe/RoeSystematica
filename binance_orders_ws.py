import websocket
from websocket import WebSocketApp 
import threading
import json
import logging
import time  


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BinanceOrdersWebSocket:
    def __init__(self, listen_key):
        self.listen_key = listen_key
        self.ws = None  
        self.callback = None

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            
            if data['e'] == 'executionReport' and data['X'] == 'FILLED':
                # Handle filled order
                print("Filled Order:", data)
                if self.callback:
                    self.callback(data)
        except KeyError as e:
            # Not all messages will have 'e' and 'X', so handle KeyError.
            pass
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        except Exception as e:
            print(f"Error in on_message: {e}")


    def on_error(self, ws, error):
        logger.error(error)

    def on_close(self, ws, close_status_code, close_msg):
        logger.info("### WebSocket closed on BinanceOrdersWebSocket ###")

    def on_open(self, ws):
        logger.info("Opened connection to BinanceOrdersWebSocket")

    def run_forever(self):
        self.ws = WebSocketApp(f"wss://stream.binancefuture.com/ws/{self.listen_key}",
                                        on_open=self.on_open,
                                        on_message=self.on_message,
                                        on_error=self.on_error,
                                        on_close=self.on_close)
        self.ws.run_forever()


