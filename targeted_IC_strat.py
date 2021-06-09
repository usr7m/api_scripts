import sys
sys.path.append('src/')
import pandas as pd
import TDA_auth
import requests
import datetime
from dateutil.relativedelta import relativedelta
import numpy as np

TDA_auth.authenticate()
client_id = TDA_auth.client_id
access_token = TDA_auth.access_token


class DATA():
	'''	'''
	def __init__(self, symbol):
		self.symbol = symbol
	'''	'''
	def timestamp(self, dt):
		return int(pd.to_datetime(dt).timestamp() * 1000)
	'''	'''
	def option_chain(self, symbol, strategy = 'SINGLE', optionType = 'ALL'):
		resp = requests.get('https://api.tdameritrade.com/v1/marketdata/chains',
							headers={'Authorization': 'Bearer ' + access_token},
							params={'apikey': client_id,
									'symbol': symbol,
									'contractType': 'ALL',
									'strikeCount': '',
									'includeQuotes': 'True',
									'strategy': strategy,  
									'interval': '',
									'strike': '', 
									'range': 'ALL' ,
									'fromDate': '',
									'toDate': '',
									'volatility': '',
									'underlyingPrice': '',
									'interestRate': '',
									'daysToExpiration': '',
									'expMonth': '', 
									'optionType': optionType})	
		print(resp.status_code)	
		return resp.json()
	'''	'''
	def parse_option_chain(self):
		query = self.option_chain(self.symbol, optionType = 'OTM')
		big_dict = []
		for contr_type in ['callExpDateMap', 'putExpDateMap']:
			contract = query[contr_type]
			expirations = contract.keys()
			for expiry in list(expirations):
				strikes = contract[expiry].keys()
				for st in list(strikes):
					entry = contract[expiry][st][0]
					entry['underlyingPrice'] = query['underlying']['mark']
					entry['underlyingTotalVolume'] = query['underlying']['totalVolume']
					big_dict.append(entry)		
		idx = list(range(len(big_dict)))
		self.opts_df = pd.DataFrame(big_dict, index = idx)
		return self.opts_df
	'''	'''
	def historical(self, symbol, 
				periodType = '',
				period = '',
				frequencyType = '',
				frequency = '',
				startDate = '', 
				endDate = '', 
				ext = 'true'):
		resp = requests.get('https://api.tdameritrade.com/v1/marketdata/' + \
			symbol + '/pricehistory',
						headers={'Authorization': 'Bearer ' + access_token},
						params={'apikey': client_id,
								'periodType': periodType,
								'period': period,
								'frequencyType': frequencyType,
								'frequency': frequency,
								'endDate': self.timestamp(endDate),
								'startDate': self.timestamp(startDate), 
								'needExtendedHoursData': ext })
		print(resp.status_code)
		return resp.json()
	'''	'''
	def parse_historical(self, days = '90'):
		endDate = datetime.datetime.today().date()
		startDate = datetime.datetime.today().date() - relativedelta(days = days)
		query = self.historical(symbol = self.symbol,
								periodType = 'year',
								period = '',
								frequencyType = 'daily',
								frequency = 1,
								endDate = endDate,
								startDate = startDate)
		self.historical = pd.DataFrame(query['candles'])
		self.historical['datetime'] =\
			pd.to_datetime(self.historical['datetime'], unit = 'ms')\
				.dt.tz_localize('UTC')\
				.dt.tz_convert('US/EASTERN')
		return self.historical


data = DATA('SPY')
data.parse_historical(days = 90)
data.parse_option_chain()



class FILTER():
  ''' '''
	def __init__(self, data):
		self.historical = data.historical
  ''' '''
	def calculate_sd(self, dte):
		trade_days = dte - (dte // 7 * 2)
		print(trade_days)
		self.historical['rets'] = np.log(self.historical['close'] / self.historical['close'].shift(trade_days))
		self.historical['mean'] = self.historical['rets'].rolling(trade_days).mean()
		self.historical['sd'] = self.historical['rets'].rolling(trade_days).std()
		self.historical['upper_target'] = (np.exp(self.historical['mean']) + self.historical['sd']) * self.historical['close']
		self.historical['lower_target'] = (np.exp(self.historical['mean']) - self.historical['sd']) * self.historical['close']


filter = FILTER(data)
filter.calculate_sd(7)
filter.historical
