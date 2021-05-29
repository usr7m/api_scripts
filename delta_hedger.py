import sys
sys.path.append('src/')
import TDA_auth
import TDA_requests
import json
import pandas as pd
import numpy as np

TDA_auth.authenticate()
TDA_requests.import_credentials(TDA_auth.client_id, TDA_auth.access_token)

userPrincipalsResponse = TDA_requests.get_user_principals(
				'streamerSubscriptionKeys,streamerConnectionInfo')
account_id = userPrincipalsResponse['primaryAccountId']
print(account_id)

positions = TDA_requests.get_accounts(account_id = account_id,
										fields = 'positions')

print(
	json.dumps(
		positions['securitiesAccount']['positions']
		, indent = 4)
	)


pos_df = pd.DataFrame(positions['securitiesAccount']['positions'])
# pos_df['instrument'][0]['underlyingSymbol']
# pos_df[['shortQuantity', 'longQuantity']]


def create_df():
	df = pd.DataFrame(columns = pos_df['instrument'][0].keys())
	for i in range(len(pos_df['instrument'])):
		df = df.append(pos_df['instrument'][i], ignore_index = True)
	df = df.merge(pos_df[['shortQuantity', 'longQuantity']], 
					left_index = True,
					right_index = True)
	return df

df = create_df()
df


def df_lookup_by_symb(df, symbol):
	agg_df = pd.DataFrame(columns = pos_df['instrument'][0].keys())
	agg_df = agg_df.append(df[df['symbol'] == symbol], ignore_index = True) 
	agg_df = agg_df.append(df[df['underlyingSymbol'] == symbol], ignore_index = True)
	return agg_df

df_symb = df_lookup_by_symb(df, 'MO')
df_symb[['symbol', 'underlyingSymbol']]

# print(json.dumps(TDA_requests.quotes(df_symb['symbol'][0]), indent = 4))
# print(json.dumps(TDA_requests.quotes(df_symb['symbol'][1]), indent = 4))


def delta_from_quotes(symbol):
	delta = TDA_requests.quotes(symbol)[symbol]['delta']
	multiplier = TDA_requests.quotes(symbol)[symbol]['multiplier']
	return delta * multiplier

df_symb['delta'] = np.nan   # initialize the delta column


for i in range(len(df_symb)):
	if df_symb['assetType'][i] == 'EQUITY':
		print('equity')
		total_qty = df_symb['longQuantity'][i] - df_symb['shortQuantity'][i]
		delta_multiplier = 1
		df_symb['delta'][i] = total_qty * delta_multiplier
	elif df_symb['assetType'][i] == 'OPTION':
		print('optchain')
		total_qty = df_symb['longQuantity'][i] - df_symb['shortQuantity'][i]
		df_symb['delta'][i] = total_qty * delta_from_quotes(df_symb['symbol'][i])

df_symb


total_delta = df_symb['delta'].sum()
total_delta
