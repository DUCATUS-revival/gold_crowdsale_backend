from django.db import models
import json
import requests
import logging
from gold_crowdsale.settings import RATES_SETTINGS, DECIMALS


def create_rate_obj():
    usd_rate = UsdRate()
    usd_rate.fetch_rates()

    return usd_rate


def get_rate_object():
    try:
        rate_object = UsdRate.objects.order_by('creation_datetime').last()
        if not rate_object:
            raise UsdRate.DoesNotExist()
    except UsdRate.DoesNotExist:
        raise Exception('RATES ERROR: database does not have saved rates, check scheduler')


class UsdRate(models.Model):
    BTC = models.FloatField()
    ETH = models.FloatField()
    USDC = models.FloatField()
    USDT = models.FloatField()
    GOLD = models.FloatField()
    # DUC = models.FloatField()
    # DUCX = models.FloatField()
    creation_datetime = models.DateTimeField(auto_now_add=True)

    def fetch_rates(self):
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

        self.save()

