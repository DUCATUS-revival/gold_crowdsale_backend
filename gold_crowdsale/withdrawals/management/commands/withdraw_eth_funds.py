import logging

from django.core.management.base import BaseCommand
from gold_crowdsale.withdrawals.eth import withdraw_eth_funds


class Command(BaseCommand):
    help = 'Withdraw funds from internal accounts (ETH/USDT/USDC)'

    def handle(self, *args, **options):
        logging.info('Started withdrawing funds')
        withdraw_eth_funds()
        logging.info('Withdraw completed')
