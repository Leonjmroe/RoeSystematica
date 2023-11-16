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
            logger.info(f"WebSocket Message Received: {data}")

            # Check if the message is an execution report for a filled order
            if data.get('e') == 'executionReport' and data.get('X') == 'FILLED':
                logger.info("Filled Order Detected")
                if self.callback:
                    self.callback(data)
            else:
                logger.info("Non-fill message or different event received")
        except KeyError as e:
            # Not all messages will have 'e' and 'X', so handle KeyError.
            logger.warning(f"KeyError in on_message: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
        except Exception as e:
            logger.error(f"Error in on_message: {e}")


    def on_error(self, ws, error):
        logger.error(f"WebSocket Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        logger.info(f"WebSocket Closed: Code: {close_status_code}, Message: {close_msg}")
        time.sleep(10) 
        self.run_forever() 

    def on_open(self, ws):
        logger.info("Opened connection to BinanceOrdersWebSocket")

    def run_forever(self):
        self.ws = WebSocketApp(f"wss://stream.binancefuture.com/ws/{self.listen_key}",
                                        on_open=self.on_open,
                                        on_message=self.on_message,
                                        on_error=self.on_error,
                                        on_close=self.on_close)
        self.ws.run_forever()


