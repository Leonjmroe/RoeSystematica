import os
import logging
from datetime import datetime



class Logger:
	def __init__(self):
		self.log_file_path = os.path.join('logs/', f'market_maker_log_{datetime.now().strftime("%H%M%S")}.log')
		self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - Line: %(lineno)d - %(message)s\n', datefmt='%H:%M:%S')
		self.logger = logging.getLogger('MarketMakerLogger')


	def set_up(self):
		self.logger.setLevel(logging.DEBUG) 
		self.logger.propagate = False  

		fh = logging.FileHandler(self.log_file_path)
		fh.setLevel(logging.DEBUG)
		fh.setFormatter(self.formatter)
		self.logger.addHandler(fh)

		ch = logging.StreamHandler()
		ch.setLevel(logging.DEBUG)  
		ch.setFormatter(self.formatter)
		self.logger.addHandler(ch)


	def get_logger(self):
		return self.logger