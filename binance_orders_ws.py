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
            if 'result' in data and 'id' in data:
                logger.info(f"Subscription confirmed: {data}")
            elif 'b' in data and 'B' in data and 'a' in data and 'A' in data:
                if self.callback:
                    self.callback(data)
            else:
                logger.warning(f"Message received without expected keys: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
        except Exception as e:
            logger.error(f"Error in on_message: {e}")

    def on_error(self, ws, error):
        logger.error(error)

    def on_close(self, ws, close_status_code, close_msg):
        logger.info("### WebSocket closed on BinanceOrdersWebSocket ###")

    def on_open(self, ws):
        logger.info("Opened connection to BinanceOrdersWebSocket")

    def run_forever(self):
        self.ws = WebSocketApp(f"wss://stream.binance.com:9443/ws/{self.listen_key}",
                                        on_open=self.on_open,
                                        on_message=self.on_message,
                                        on_error=self.on_error,
                                        on_close=self.on_close)
        self.ws.run_forever()


