# real time option chain retriever, straddle price calculator
# calculates all and ATM straddle prices specifically, 
# with ability to estimate n_day DTE straddle price via polynomial regression 

import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt



def option_chain(symbol):
	resp = requests.get('https://api.tdameritrade.com/v1/marketdata/chains',
						params={'apikey': 'you_api_key_here',
								'symbol': symbol,
								'contractType': 'ALL',
								'strikeCount': 100,
								'includeQuotes': 'True',
								'strategy': 'SINGLE',  
								'interval': '',
								'strike': '', 
								'range': 'ALL' ,
								'fromDate': '',
								'toDate': '',
								'volatility': '',
								'underlyingPrice': '',
								'interestRate': '',
								'daysToExpiration': '',
								'expMonth': 'ALL', 
								'optionType': 'ALL'})		
	print(resp.status_code)
	return resp.json()


def parse_datetime(df):
	for col in ['datetime', 'expirationDate', 'quoteTimeInLong']:
		try:	
			df[col] = pd.to_datetime(df[col], unit = 'ms').dt.date
		except KeyError:
			pass


def get_opts_from_API(symbol):
	query = option_chain(symbol).copy()
	query.keys()
	opts_dict_list = []
	for contr_type in ['callExpDateMap', 'putExpDateMap']:
		contract = query[contr_type]
		expirations = contract.keys()
		for expiry in list(expirations):
			strikes = contract[expiry].keys()
			for st in list(strikes):
				entry = contract[expiry][st][0]
				opts_dict_list.append(entry)		
	idx = list(range(len(opts_dict_list)))
	opts_df = pd.DataFrame(opts_dict_list, index = idx)
	opts_df['underlyingSymbol'] = query['underlying']['symbol']
	opts_df['underlyingMark'] = query['underlying']['mark']
	opts_df['log_diff'] = np.log(opts_df['strikePrice']/opts_df['underlyingMark'])
	return opts_df


def find_n_closest(data, target, n):
	d = data.copy()
	v = [] 
	abs_diff = lambda d : abs(d - target)
	for i in range(n * 2 + 1):
		abs_diff_series = abs_diff(d)
		try:
			idx = abs_diff_series[abs_diff_series == min(abs_diff(d))].index
			v.append(d[idx].values)
			d.drop(idx, inplace = True)
		except ValueError:
			print('request out of bounds')
	return np.concatenate(v)


def get_straddle_df(opts_df):
	df = opts_df.copy()
	l = []
	for e in df['daysToExpiration'].unique():
		df_e = df[df['daysToExpiration'] == e].copy()
		df_e.reset_index(drop = True, inplace = True)
		dte = df_e['daysToExpiration'].values[0]
		underlyingSymbol = df['underlyingSymbol'].values[0]
		underlyingMark = df['underlyingMark'].values[0]
		call_strikes = df_e.loc[df_e['putCall'] == 'CALL']['strikePrice'].values
		put_strikes = df_e.loc[df_e['putCall'] == 'PUT']['strikePrice'].values
		common_strikes = [x for x in call_strikes if x in put_strikes]
		for x in common_strikes:
			df_s = df_e.loc[df_e['strikePrice'] == x].copy()
			df_s_CALL = df_s.loc[df_s['putCall'] == 'CALL'].copy()
			callPrice = df_s_CALL['closePrice'].values[0]
			df_s_PUT = df_s.loc[df_s['putCall'] == 'PUT'].copy()
			putPrice = df_s_PUT['closePrice'].values[0]
			straddlePrice = callPrice + putPrice
			frame = {\
				'dte': e,
				'underlyingSymbol' : underlyingSymbol,
				'daysToExpiration': dte,
				'strikePrice': x,
				'callPrice': callPrice,
				'putPrice': putPrice,
				'straddlePrice': straddlePrice,
				'underlyingMark': underlyingMark
				}
			l.append(frame)
	straddle_df = pd.DataFrame(l)
	return straddle_df


def find_n_closest(data, target, n):
	d = data.copy()
	v = [] 
	abs_diff = lambda d : abs(d - target)
	for i in range(n * 2 + 1):
		abs_diff_series = abs_diff(d)
		try:
			idx = abs_diff_series[abs_diff_series == min(abs_diff(d))].index
			v.append(d[idx].values)
			d.drop(idx, inplace = True)
		except ValueError:
			print('request out of bounds')
	return np.concatenate(v)



def get_ATM_straddle_df(straddle_df):
	df_atm = pd.DataFrame()
	df = straddle_df.copy()
	for dte in df['daysToExpiration'].unique():
		df_sample = df.loc[df['daysToExpiration'] == dte]
		atm = find_n_closest(	df_sample['strikePrice'],
								df_sample['underlyingMark'],
								0)[0]
		df_sample = df_sample.loc[df_sample['strikePrice'] == atm]
		df_atm = df_atm.append(df_sample)
	return df_atm


def run_ATM_straddle(symbol):
	opts_df = get_opts_from_API(symbol)
	parse_datetime(opts_df)
	straddle_df = get_straddle_df(opts_df)
	straddle_df_ATM = get_ATM_straddle_df(straddle_df)
	straddle_df_ATM = straddle_df_ATM.loc[straddle_df_ATM['straddlePrice'] > 0]
	straddle_df_ATM
	return opts_df, straddle_df, straddle_df_ATM

def plot_dte_straddle(df):
	plt.scatter(df['daysToExpiration'], df['straddlePrice'])
	plt.yscale('log')
	plt.grid()
	plt.show()

symbol = 'SPY'
opts_df, straddle_df, straddle_df_ATM = run_ATM_straddle(symbol)

plot_dte_straddle(straddle_df_ATM)





''' poly fit and prediction '''

from sklearn.preprocessing import PolynomialFeatures
from sklearn import linear_model


def poly_reg(regr, col_1, col_2, deg): 
	x = col_1.values
	x = x.reshape(-1,1)
	y = col_2.values
	y = y.reshape(-1,1)
	X = x
	vector = y
	predict = x
	poly = PolynomialFeatures(degree = deg)
	X_ = poly.fit_transform(X)
	predict_ = poly.fit_transform(predict)
	poly_fit = regr.fit(X_, vector)
	predictions = poly_fit.predict(predict_)
	return poly, poly_fit, predictions

def predict_n_day_price(poly, fit, n_day):
	x = np.array(n_day).reshape(-1,1)
	x = poly.fit_transform(x)
	z = fit.predict(x)
	return z[0][0]

def run_regression_pred(n_day, dte_lim = 1000):
	if n_day > dte_lim:
		print('no')
		return 0,0,0
	else:
		df = straddle_df_ATM.loc[straddle_df_ATM['daysToExpiration'] < dte_lim].copy()
		regr = linear_model.LinearRegression()
		poly_fit = poly_reg(\
				regr,
				df['daysToExpiration'],
				df['straddlePrice'],
				deg = 3)
		poly = poly_fit[0]
		fit = poly_fit[1]
		df['predictions'] = poly_fit[2]
		pred_n_day = predict_n_day_price(poly, fit, n_day)
		return df, n_day, pred_n_day


def plot_n_day_regression(df, n_day, pred_n_day):
	plt.scatter(df['daysToExpiration'], df['straddlePrice'])
	plt.plot(df['daysToExpiration'], df['straddlePrice'])
	plt.plot(df['daysToExpiration'], df['predictions'], c = 'orange')
	plt.scatter(n_day, pred_n_day, c = 'red')
	plt.annotate(\
		str(n_day) + ' days', 
		xy=(n_day, pred_n_day), 
		xytext=(n_day + 20, pred_n_day),
		arrowprops=dict(facecolor='black', shrink=0.05)
		)
	plt.yscale('log')
	plt.grid()
	plt.show()


n_day = 10
df, n_day, pred_n_day = run_regression_pred(n_day, dte_lim = 100)

plot_n_day_regression(df, n_day, pred_n_day)

