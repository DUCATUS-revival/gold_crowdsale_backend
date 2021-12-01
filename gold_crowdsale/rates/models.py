from django.db import models
import json
import requests
from gold_crowdsale.settings import RATES_SETTINGS


class UsdRate(models.Model):
    BTC = models.FloatField()
    ETH = models.FloatField()
    USDC = models.FloatField()
    USDT = models.FloatField()
    GOLD = models.FloatField()
    # DUC = models.FloatField()
    # DUCX = models.FloatField()
    last_update_datetime = models.DateTimeField(auto_now=True)

    def update_rates(self):
        payload = {
            'fsym': 'USD',
            'tsyms': ['BTC', 'ETH', 'USDC', 'USDT'],
            'api_key': RATES_SETTINGS.get('cryptocompare_apikey'),
        }
        response = requests.get(RATES_SETTINGS.get('cryptocompare_url'), params=payload)
        if response.status_code != 200:
            raise Exception(f'Cannot get exchange rates')
        response_data = json.loads(response.text)

        self.BTC = response_data['BTC']
        self.ETH = response_data['ETH']
        self.USDC = response_data['USDC']
        self.USDT = response_data['USDT']
        self.GOLD = RATES_SETTINGS.get('gold_price')

        # response = requests.get(RATES_API.get('DUCATUS_RATES_URL').format(fsym='USD', tsyms='DUC,DUCX'))
        # if response.status_code != 200:
        #     raise Exception(f'Cannot get DUC exchange rate')
        # rates = json.loads(response.content)
        #
        # self.DUC = rates['DUC']
        # self.DUCX = rates['DUCX']