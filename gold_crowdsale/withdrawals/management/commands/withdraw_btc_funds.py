import logging

from django.core.management.base import BaseCommand
from gold_crowdsale.withdrawals.services import withdraw_btc_funds


class Command(BaseCommand):
    help = 'Withdraw funds from internal accounts (BTC)'

    def handle(self, *args, **options):
        logging.info('Started withdrawing funds')
        withdraw_btc_funds()
        logging.info('Withdraw completed')
