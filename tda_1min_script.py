import sys
sys.path.append('TDA API')
import TDA_auth
import pandas as pd
import requests
import os

''' API initialize '''
client_id = TDA_auth.client_id
access_token = TDA_auth.access_token

''' initialize Mongo collection '''

from pymongo import MongoClient
db = MongoClient('mongodb://path_to_mongo:27017/')[DB_name]
collection = db[collection_name]


''' load from API '''

def API_load_historical(symbol):
	resp = requests.get('https://api.tdameritrade.com/v1/marketdata/' + symbol + '/pricehistory',
						headers={'Authorization': 'Bearer ' + access_token},
						params={'apikey': client_id,
								'periodType': 'day',
								'period': 10,
								'frequencyType': 'minute',
								'frequency': 1,
								'needExtendedHoursData': 'true' })
	print(resp.status_code)
	data = pd.DataFrame(resp.json()['candles'])
	data['datetime'] = pd.to_datetime(data['datetime'], unit = 'ms')
	return data


''' select data of specific date from df '''

def select_date(date, df):
	return df[df['datetime'].dt.date == date]


''' entry creation method... MongoDB '''

def create_entry(date, df):
	return dict({	'name' : 'SPY_1_min',
					'date' : pd.to_datetime(date),
					'observations' : df.to_dict('records')})


''' existing entry update method ( in case previous data is incomplete ... MongoDB '''

def update_entry(date, entry):
	collection.update_one(\
				{'date': date},\
				{'$push': {\
					'observations' : {
						'$each' : data.to_dict('records')
						}
					}
				}
			)


API_data = API_load_historical('SPY')
API_data
# --------------------------------------------------------------

API_date_list = API_data['datetime'].dt.date.unique()
API_date_list

''' examples: '''

# select_date(API_date_list[0], API_data)
# select_date(pd.to_datetime('2021-04-20'), API_data)



def new_data_to_Mongo():
	for date in API_date_list:
		print('\n' + str(date))
		date = pd.to_datetime(date)
		api_data_on_date = select_date(date, API_data)
		''' check if this day's data exists in db '''
		db_data_on_date = pd.DataFrame(collection.find({'date' : date}))
		db_data_on_date = pd.DataFrame(db_data_on_date['observations'][0])
		if db_data_on_date.empty:
			''' if it doesn't: create a new entry '''
			print('no such entry')
			print('creating entry...')
			new_entry = create_entry(date, api_data_on_date)
			collection.insert_one(new_entry)
			print('created!')
		else:	
			''' if it does - update observations (if new are available) '''		
			new_data = db_data_on_date.merge(api_data_on_date, 
									on = 'datetime',
									how = 'outer',
									indicator = True)
			x = new_data[new_data['_merge'] == 'right_only']
			if x.empty:
				print('no new observations available')
			else:
				new_index = new_data[new_data['_merge'] == 'right_only'].index
				new_data = data_on_date.iloc[new_index]
				new_data.reset_index(drop = True, inplace = True)
				print('new observations: ')
				print(new_data)
				print('updating entry')
				c.update_entry(date, new_data)
				print('done!')

new_data_to_Mongo()

# --------------------------------------------------------------

''' dates available in database '''

# or set custom :
# date_range = ['2020-12-09', '2021-01-06']
date_range = pd.DataFrame(collection.find())['date']
date_range

''' pull date range data from mongo '''

def data_from_db(date_range):
	read_db = pd.DataFrame(collection.find())
	data = read_db\
			[read_db.date >= date_range[0]]\
			[read_db.date <= date_range[len(date_range) - 1]]
	return data.reset_index(drop = True)

''' combine together '''

def combine(data):
	try:
		combined_df = pd.DataFrame(data['observations'][0])
		for i in range(len(data) - 1):
			df = pd.DataFrame(data['observations'][i + 1])
			combined_df = combined_df.append(df)	
		return combined_df.reset_index(drop = True)
	except KeyError:
		print('empty? dataframe')

''' localize timestamps '''

def localize_tz(data, col):
	data[col] = data[col].dt.tz_localize('UTC').dt.tz_convert('US/EASTERN')
	return data

''' wrapper to do everything quicker '''

def aggregate_full(date_range):
	df = data_from_db(date_range)
	df = combine(df)
	df = localize_tz(df, 'datetime')
	return df

db_data = aggregate_full(date_range)

# ---------------------------------------------------------

''' plotting stuff '''

import matplotlib.pyplot as plt
plt.figure(figsize = (16,8))
plt.scatter(x = db_data['datetime'], y = db_data['close'], s = 1)
plt.grid()
plt.show() 

plt.scatter(x = db_data.index, y = db_data['close'], s = 1)
plt.grid()
plt.show() 


# -------------------------------------------------------

import numpy as np
db_data 
db_data['rets'] = np.log(db_data['close'] / db_data['close'].shift(1))
db_data['cmsm'] = db_data['rets'].cumsum()

db_data

plt.figure(figsize = (16,8))
plt.scatter(x = db_data['datetime'], y = db_data['cmsm'], s = 1)
plt.grid()
plt.show() 



''' pulling each day as a separate df for sampling/backtesting '''
''' query by date, each as a separate df '''

date_range = pd.DataFrame(collection.find())['date']

def get_day_data(date):
	query = pd.DataFrame(collection.find({'date' : pd.to_datetime(date)}))
	query_data = query['observations'][0]
	query_data = pd.DataFrame(query_data)
	return query_data

for date in date_range:
	print('\n' + str(date.date()) + '\n')
	day_df = get_day_data(date)
	print(day_df)
	
