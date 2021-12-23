import logging

from django.core.management.base import BaseCommand
from gold_crowdsale.purchases.models import TokenPurchase


class Command(BaseCommand):
    help = 'Withdraw funds from internal accounts (BTC)'

    def handle(self, *args, **options):
        logging.info('Started preparing withdraw cycle for BTC')
        all_purchases = TokenPurchase.objects.all().exclude(btc_address=None)
        logging.info('BTC WITHDRAW')

        # for user in all_purchases:

        logging.info('Withdraw completed')
