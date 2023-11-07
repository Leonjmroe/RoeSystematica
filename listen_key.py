import requests


def get_listen_key(api_key, api_secret):

	base_url = 'https://testnet.binancefuture.com'
	path = '/fapi/v1/listenKey'
	url = base_url + path

	headers = {'X-MBX-APIKEY': api_key}
	response = requests.post(url, headers=headers)

	response.raise_for_status()

	data = response.json()
	listen_key = data.get('listenKey')

	return listen_key

