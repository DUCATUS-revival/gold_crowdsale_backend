from apscheduler.schedulers.background import BlockingScheduler
from django.core.management.base import BaseCommand

from gold_crowdsale.settings import SCHEDULER_SETTINGS
from gold_crowdsale.accounts.tasks import check_and_release_accounts
from gold_crowdsale.rates.tasks import update_rates



class Command(BaseCommand):
    help = 'Run blocking scheduler to create periodical tasks'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Preparing scheduler'))
        scheduler = BlockingScheduler()

        accounts_timeout = SCHEDULER_SETTINGS.get('accounts_pool_timeout')
        rates_timeout = SCHEDULER_SETTINGS.get('rates_timeout')
        scheduler.add_job(check_and_release_accounts.send, 'interval', seconds=accounts_timeout)
        scheduler.add_job(update_rates.send, 'interval', seconds=rates_timeout)

        self.stdout.write(self.style.NOTICE('Start scheduler'))
        scheduler.start()
