import sys
sys.path.append('src/')

import TDA_auth
import TDA_requests
import datetime
import json
import pandas as pd
import urllib
import time
import asyncio
import websocket
import datetime
from dateutil.relativedelta import relativedelta
import requests


TDA_auth.authenticate()
client_id = TDA_auth.client_id,
access_token = TDA_auth.access_token


''' from here.... '''


def get_user_principals(fields):
	resp = requests.get('https://api.tdameritrade.com/v1/userprincipals',
						headers={'Authorization': 'Bearer ' + access_token},
						params={'fields': fields})
	print(resp.status_code)
	return resp.json()


userPrincipalsResponse = get_user_principals('streamerSubscriptionKeys,streamerConnectionInfo')
# print(json.dumps(userPrincipalsResponse, indent = 3))

tokenTimeStamp = userPrincipalsResponse['streamerInfo']['tokenTimestamp']
tokenTimeStamp = int(pd.to_datetime(tokenTimeStamp).timestamp() * 1000)

credentials = {\
	'userid' : userPrincipalsResponse['accounts'][0]['accountId'],
	'token': userPrincipalsResponse['streamerInfo']['token'],
	'company': userPrincipalsResponse['accounts'][0]['company'],
	'segment': userPrincipalsResponse['accounts'][0]['segment'],
	'cddomain': userPrincipalsResponse['accounts'][0]['accountCdDomainId'],
	'usergroup': userPrincipalsResponse['streamerInfo']['userGroup'],
	'accesslevel': userPrincipalsResponse['streamerInfo']['accessLevel'],
	'authorized': 'Y',
	'timestamp': tokenTimeStamp,
	'appid': userPrincipalsResponse['streamerInfo']['appId'],
	'acl': userPrincipalsResponse['streamerInfo']['acl'] 
	}

account = userPrincipalsResponse['accounts'][0]['accountId']
source = userPrincipalsResponse['streamerInfo']['appId']
token = userPrincipalsResponse['streamerInfo']['token']



''' websocket connection '''

uri = 'wss://' + userPrincipalsResponse['streamerInfo']['streamerSocketUrl'] + '/ws'
ws = websocket.WebSocket()

def send_msg(msg):
	ws.send(json.dumps(msg))
	
def recv_msg():
	msg = (json.loads(ws.recv()))
	return msg

def localize_tz(col):
	col = pd.to_datetime(col, unit = 'ms')
	col = col.dt.tz_localize('UTC').dt.tz_convert('US/EASTERN')
	return col



'''	data parser '''

def parse_chart_hist_futs(message):
	message.keys()
	data = pd.DataFrame(message['snapshot'])
	data.timestamp
	data = pd.DataFrame(data.content[0])
	data = pd.DataFrame(data['3'][0])
	data.rename(columns = {	'0' : 'datetime',
							'1' : 'open',
							'2' : 'high',
							'3'	: 'low',
							'4'	: 'close',
							'5'	: 'volume'}, 
				inplace = True)
	data['datetime'] = localize_tz(data['datetime'])
	return data

def timestamp(dt):
	return int(pd.to_datetime(dt).timestamp() * 1000)


endDate = timestamp(datetime.datetime.today().date())
startDate = timestamp(datetime.datetime.today().date() - relativedelta(days = 30))


''' requests '''

LOGIN = {\
	'requests': [
		{
			'service': 'ADMIN',
			'command': 'LOGIN',
			'requestid': 0,
			'account': account,
			'source': source,
			'parameters': {
				'credential': urllib.parse.urlencode(credentials),
				'token': token,
				'version': '1.0'
				}
			}
		]	
	}


def CHART_HISTORY_FUTURES(req_id, symbol, freq, startDate, endDate ):
	return {
	    "requests": [
	        {
	            "service": "CHART_HISTORY_FUTURES",
	            "requestid": req_id,
	            "command": "GET",
	            "account": account,
	            "source": source,
	            "parameters": {
	                "symbol": symbol,
	                "frequency": freq, # "m1"
	                # "Period": "d1"
	                "START_TIME": startDate, 
	                "END_TIME": endDate
	            }
	        }
	    ]
	}


ws.connect(uri)
send_msg(LOGIN)
recv_msg()
send_msg(\
	CHART_HISTORY_FUTURES(req_id = 1,
								symbol = '/ES',
								freq  = 'm5',  # m1: 1 min, d1 : 1 day
								startDate = startDate,
								endDate = endDate))

message = recv_msg()
ws.close()
df = parse_chart_hist_futs(message)
df
