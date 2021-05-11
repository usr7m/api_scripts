import sys
sys.path.append('src/')
import TDA_auth
import TDA_requests
import pandas as pd
import time

TDA_auth.authenticate()
TDA_requests.import_credentials(TDA_auth.client_id, TDA_auth.access_token)



search = TDA_requests.search_instruments('[A-Z].*', 'symbol-regex')
df = pd.DataFrame(search.values())

df = df[(df['exchange'] == 'NASDAQ') | (df['exchange'] == 'NYSE')]
df = df[df['symbol'].str.contains('^[a-zA-Z]+$', regex = True, na = False)]
df = df[~(df['symbol'].str.len() > 4)]
df.reset_index(drop = True, inplace = True)
df


''' comprehensive fundamentals fetch to screen '''

def get_data_for_symb(symbol):
	fund = TDA_requests.search_instruments(symbol, 'fundamental')
	fund = pd.DataFrame(fund[symbol])
	fund = fund.T
	fund = fund[fund.index == 'fundamental']
	fund.reset_index(drop = True, inplace = True)
	return fund

def create_base_df(symbol):
	df = pd.DataFrame()
	cols = get_data_for_symb(symbol).columns
	df = pd.DataFrame(columns = cols)
	return df

symbol = df['symbol'][0]
df_composite = pd.DataFrame()
df_composite = create_base_df(symbol)

''' sample size and timer to prevent API throttle kick-out '''
sample_size = 20
iter = len(df) // sample_size + 1

for i in range(iter):
	for symbol in df['symbol'][sample_size * i : sample_size * (i + 1)]:
		print(symbol)
		df_composite = df_composite.append(get_data_for_symb(symbol))
	time.sleep(5)            


df_composite




''' basic quotes-based fetch to screen '''


def get_data_for_symb(symbol):
	quotes = TDA_requests.quotes(symbol)
	quotes = pd.DataFrame(quotes).T
	return quotes

def create_base_df(symbol):
	df = pd.DataFrame()
	cols = get_data_for_symb(symbol).columns
	df = pd.DataFrame(columns = cols)
	return df

symbol = df['symbol'][0]
symbol
df_composite = pd.DataFrame()
df_composite = create_base_df(symbol)
df_composite

''' TDA.quotes seems to have a limit of around 500 per request '''
sample_size = 500 
iter = len(df) // sample_size + 1
iter

for i in range(iter):
	symbol_list = list(df['symbol'][sample_size * i : sample_size * (i + 1)].values)
	symbol_list = ','.join([str(s) for s in symbol_list])
	df_composite = df_composite.append(get_data_for_symb(symbol_list))


df_composite
