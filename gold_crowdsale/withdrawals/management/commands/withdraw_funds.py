import logging

from django.core.management.base import BaseCommand
from gold_crowdsale.withdrawals.models import create_withdraw_cycle


class Command(BaseCommand):
    help = 'Withdraw funds from internal accounts'

    def add_arguments(self, parser):
        parser.add_argument('currencies', nargs='+', type=str)

    def handle(self, *args, **options):
        create_withdraw_cycle(options['currencies'])
        logging.info(f'Started preparing withdraw cycle for currencies: {options["currencies"]}')

