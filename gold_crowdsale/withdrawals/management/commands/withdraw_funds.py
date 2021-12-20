import logging

from django.core.management.base import BaseCommand
from gold_crowdsale.withdrawals.services import withdraw_funds

if __name__ == '__main__':
    logging.info('Started withdrawing funds')
    withdraw_funds()
    logging.info('Withdraw completed')


class Command(BaseCommand):
    help = 'Withdraw funds from internal accounts'

    def handle(self, *args, **options):
        logging.info('Started withdrawing funds')
        withdraw_funds()
        logging.info('Withdraw completed')
